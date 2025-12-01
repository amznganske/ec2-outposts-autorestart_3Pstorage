#!/usr/bin/env python3

import boto3
import argparse
import sys
import os
import shlex
import subprocess
from botocore.exceptions import ClientError
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from outpost_utils import get_outpost_info

def find_instance_region(instance_id):
    """Find which region contains the instance"""
    session = boto3.Session()
    regions = session.get_available_regions('ec2')
    
    for region in regions:
        try:
            ec2_client = boto3.client('ec2', region_name=region)
            ec2_client.describe_instances(InstanceIds=[instance_id])
            return region
        except ClientError:
            continue
    return None

def list_running_instances(ec2_client):
    """List all running EC2 instances"""
    try:
        response = ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                placement = instance.get('Placement', {})
                outpost_arn = placement.get('OutpostArn', 'N/A')
                az = placement.get('AvailabilityZone', 'N/A')
                
                instances.append({
                    'InstanceId': instance['InstanceId'],
                    'InstanceType': instance['InstanceType'],
                    'Name': name,
                    'AvailabilityZone': az,
                    'OutpostArn': outpost_arn
                })
        return instances
    except ClientError as e:
        print(f"Error listing instances: {e}")
        return []

def select_instance(instances):
    """Display instances and let user select one"""
    if not instances:
        print("No running instances found.")
        return None
    
    print("\nRunning EC2 Instances:")
    print("-" * 80)
    for i, instance in enumerate(instances, 1):
        outpost_info = "(Outpost)" if instance['OutpostArn'] != 'N/A' else ""
        print(f"{i}. {instance['InstanceId']} ({instance['InstanceType']}) - {instance['Name']} {outpost_info}")
        print(f"   AZ: {instance['AvailabilityZone']}")
    
    while True:
        try:
            choice = int(input(f"\nSelect instance (1-{len(instances)}): ")) - 1
            if 0 <= choice < len(instances):
                return instances[choice]['InstanceId']
            print("Invalid selection. Please try again.")
        except (ValueError, KeyboardInterrupt):
            return None

def list_subnets_in_vpc(ec2_client, vpc_id):
    """List all subnets in the specified VPC"""
    try:
        response = ec2_client.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        
        subnets = []
        for subnet in response['Subnets']:
            name = next((tag['Value'] for tag in subnet.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            subnets.append({
                'SubnetId': subnet['SubnetId'],
                'Name': name,
                'AvailabilityZone': subnet['AvailabilityZone'],
                'CidrBlock': subnet['CidrBlock']
            })
        return sorted(subnets, key=lambda x: x['AvailabilityZone'])
    except ClientError as e:
        print(f"Error listing subnets: {e}")
        return []

def select_subnet(subnets):
    """Display subnets and let user select one"""
    if not subnets:
        print("No subnets found in VPC.")
        return None
    
    print("\nAvailable Subnets:")
    print("-" * 80)
    for i, subnet in enumerate(subnets, 1):
        print(f"{i}. {subnet['SubnetId']} - {subnet['Name']}")
        print(f"   AZ: {subnet['AvailabilityZone']}, CIDR: {subnet['CidrBlock']}")
    
    while True:
        try:
            choice = int(input(f"\nSelect subnet (1-{len(subnets)}): ")) - 1
            if 0 <= choice < len(subnets):
                return subnets[choice]['SubnetId']
            print("Invalid selection. Please try again.")
        except (ValueError, KeyboardInterrupt):
            return None

def ask_for_second_template():
    """Ask user if they want to create a second launch template"""
    while True:
        try:
            response = input("\nWould you like to create a second launch template for Outpost Server recovery? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
        except KeyboardInterrupt:
            return False

def ask_instance_choice():
    """Ask user if they want to use same instance or different instance for second template"""
    while True:
        try:
            print("\nFor the second launch template, would you like to:")
            print("1. Use the same instance (for recovery on different Outpost Server)")
            print("2. Use a different instance")
            choice = input("Enter choice (1 or 2): ").strip()
            if choice == '1':
                return 'same'
            elif choice == '2':
                return 'different'
            else:
                print("Please enter '1' or '2'.")
        except KeyboardInterrupt:
            return 'different'

def create_launch_template_from_instance(ec2_client, instance_id, template_name=None):
    """Create launch template from EC2 instance"""
    try:
        # Get instance details
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        

        
        # Get VPC ID and prompt for subnet selection
        vpc_id = instance['VpcId']
        print(f"\nInstance is in VPC: {vpc_id}")
        
        subnets = list_subnets_in_vpc(ec2_client, vpc_id)
        selected_subnet_id = select_subnet(subnets)
        
        if not selected_subnet_id:
            print("No subnet selected. Exiting.")
            return None
        
        # Generate template name if not provided
        if not template_name:
            instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), instance_id)
            template_name = f"lt-{instance_name}-{instance_id}"
        
        # Build launch template data
        template_data = {
            'ImageId': instance['ImageId'],
            'InstanceType': instance['InstanceType'],
            'TagSpecifications': [{
                'ResourceType': 'instance',
                'Tags': instance.get('Tags', [])
            }]
        }
        
        # Add optional fields if they exist
        if instance.get('KeyName'):
            template_data['KeyName'] = instance['KeyName']
            
        # Only add SecurityGroupIds if not using NetworkInterfaces
        if instance['SecurityGroups'] and len(instance.get('NetworkInterfaces', [])) <= 1:
            template_data['SecurityGroupIds'] = [sg['GroupId'] for sg in instance['SecurityGroups']]
            
        # Get UserData using describe_instance_attribute for reliability
        try:
            userdata_response = ec2_client.describe_instance_attribute(
                InstanceId=instance_id,
                Attribute='userData'
            )
            userdata = userdata_response.get('UserData', {}).get('Value', '')
            if userdata:
                template_data['UserData'] = userdata
                print(f"  UserData found: {len(userdata)} characters")
            else:
                print(f"  No UserData found on source instance")
        except ClientError as e:
            print(f"  Could not retrieve UserData: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
            print(f"  Note: Ensure your IAM user/role has ec2:DescribeInstanceAttribute permission")
            
        if instance.get('MetadataOptions'):
            valid_metadata_keys = ['HttpTokens', 'HttpPutResponseHopLimit', 'HttpEndpoint', 'HttpProtocolIpv6', 'InstanceMetadataTags']
            metadata_options = {k: v for k, v in instance['MetadataOptions'].items() if k in valid_metadata_keys}
            if metadata_options:
                template_data['MetadataOptions'] = metadata_options
            
        # Include network interfaces - use selected subnet for both ENIs
        network_interfaces = instance.get('NetworkInterfaces', [])
        if len(network_interfaces) > 1:
            eni_configs = []
            for eni in sorted(network_interfaces, key=lambda x: x['Attachment']['DeviceIndex']):
                eni_config = {
                    'DeviceIndex': eni['Attachment']['DeviceIndex'],
                    'SubnetId': selected_subnet_id,  # Use selected subnet
                    'Groups': [sg['GroupId'] for sg in eni['Groups']]
                }
                eni_configs.append(eni_config)
            template_data['NetworkInterfaces'] = eni_configs
        else:
            # Single ENI - add subnet configuration
            template_data['NetworkInterfaces'] = [{
                'DeviceIndex': 0,
                'SubnetId': selected_subnet_id,
                'Groups': [sg['GroupId'] for sg in instance['SecurityGroups']]
            }]
            # Remove SecurityGroupIds since we're using NetworkInterfaces
            template_data.pop('SecurityGroupIds', None)
        
        # Remove None values but keep empty strings for UserData
        template_data = {k: v for k, v in template_data.items() if v is not None and (k == 'UserData' or v != '')}
        
        # Create launch template
        response = ec2_client.create_launch_template(
            LaunchTemplateName=template_name,
            LaunchTemplateData=template_data
        )
        
        template_id = response['LaunchTemplate']['LaunchTemplateId']
        print(f"✓ Launch template created successfully!")
        print(f"  Template Name: {template_name}")
        print(f"  Template ID: {template_id}")
        print(f"  Source Instance: {instance_id}")
        print(f"  Subnet: {selected_subnet_id}")
        
        return template_id
        
    except ClientError as e:
        print(f"Error creating launch template: {e}")
        return None

def ask_for_automated_recovery():
    """Ask user if they want to setup automated recovery"""
    while True:
        try:
            response = input("\nWould you like to setup automated recovery? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
        except KeyboardInterrupt:
            return False

def setup_automated_recovery(template_ids, region, source_instance_id=None, primary_template_id=None):
    """Setup automated recovery using autorestart tool"""
    
    try:
        print("Source instance information will be auto-detected by the autorestart tool.")
        
        # Generate a valid stack name from instance name or use user input
        if source_instance_id:
            try:
                ec2_client = boto3.client('ec2', region_name=region)
                response = ec2_client.describe_instances(InstanceIds=[source_instance_id])
                instance = response['Reservations'][0]['Instances'][0]
                instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), source_instance_id)
                
                # Ensure stack name starts with a letter and contains only valid characters
                import re
                # Remove invalid characters and ensure it starts with a letter
                clean_name = re.sub(r'[^a-zA-Z0-9-]', '', instance_name)
                if clean_name and not clean_name[0].isalpha():
                    clean_name = f"stack-{clean_name}"
                elif not clean_name:
                    clean_name = f"stack-{source_instance_id.replace('i-', '')}"
                
                suggested_name = f"autorestart-{clean_name}"
                stack_name = input(f"Enter CloudFormation stack name [{suggested_name}]: ").strip() or suggested_name
            except Exception:
                stack_name = input("Enter CloudFormation stack name: ").strip()
        else:
            stack_name = input("Enter CloudFormation stack name: ").strip()
        
        # Validate stack name format
        import re
        if not re.match(r'^[a-zA-Z][-a-zA-Z0-9]*$', stack_name):
            print(f"Invalid stack name '{stack_name}'. Stack names must start with a letter and contain only letters, numbers, and hyphens.")
            return False
        notification_email = input("Enter notification email address: ").strip()
        
        # Find autorestart script path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        autorestart_script = os.path.join(project_root, "autorestart", "autorestart-tool", "init.py")
        template_file = os.path.join(project_root, "autorestart", "autorestart-tool", "AutoRestartTemplate.yaml")
        
        if not os.path.exists(autorestart_script):
            print(f"Autorestart script not found at: {autorestart_script}")
            return False
            
        if not os.path.exists(template_file):
            print(f"Template file not found at: {template_file}")
            return False
        
        # Build command arguments with input validation
        python_cmd = "python" if os.name == "nt" else "python3"
        
        # Validate and sanitize all inputs
        import re
        
        # Validate template IDs (AWS launch template ID format)
        validated_template_ids = []
        for tid in template_ids:
            if tid and isinstance(tid, str) and re.match(r'^lt-[0-9a-f]{17}$', tid):
                validated_template_ids.append(tid)
        
        # Validate stack name (CloudFormation naming rules)
        if not re.match(r'^[a-zA-Z][-a-zA-Z0-9]*$', stack_name):
            raise ValueError(f"Invalid stack name: {stack_name}")
        
        # Validate region (AWS region format)
        if not re.match(r'^[a-z0-9-]+$', region):
            raise ValueError(f"Invalid region: {region}")
        
        # Validate email (basic email format)
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', notification_email):
            raise ValueError(f"Invalid email format: {notification_email}")
        
        cmd = [
            python_cmd, autorestart_script,
            "--launch-template-id"] + validated_template_ids + [
            "--template-file", template_file,
            "--stack-name", stack_name,
            "--region", region,
            "--notification-email", notification_email
        ]
        
        if primary_template_id and isinstance(primary_template_id, str) and re.match(r'^lt-[0-9a-f]{17}$', primary_template_id):
            cmd.extend(["--primary-template-id", primary_template_id])
        
        if source_instance_id and isinstance(source_instance_id, str) and re.match(r'^i-[0-9a-f]{8,17}$', source_instance_id):
            cmd.extend(["--source-instance-id", source_instance_id])
        
        print(f"Running autorestart setup with command: {' '.join(shlex.quote(arg) for arg in cmd)}")
        subprocess.run(cmd, check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error running autorestart setup: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error in autorestart setup: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Create launch template from running EC2 instance')
    parser.add_argument('-i', '--instance-id', help='EC2 instance ID')
    parser.add_argument('-n', '--template-name', help='Launch template name')
    parser.add_argument('-r', '--region', help='AWS region (if not specified, uses default from AWS config)')
    parser.add_argument('--list-regions', action='store_true', help='List available regions')
    
    args = parser.parse_args()
    
    # Handle list regions option
    if args.list_regions:
        try:
            ec2_client = boto3.client('ec2')
            regions = ec2_client.describe_regions()['Regions']
            print("Available AWS regions:")
            for region in sorted(regions, key=lambda x: x['RegionName']):
                print(f"  {region['RegionName']}")
            sys.exit(0)
        except Exception as e:
            print(f"Error listing regions: {e}")
            sys.exit(1)
    
    # Initialize EC2 client
    try:
        if args.region:
            ec2_client = boto3.client('ec2', region_name=args.region)
            print(f"Using region: {args.region}")
        else:
            ec2_client = boto3.client('ec2')
            print(f"Using default region from AWS config")
    except Exception as e:
        print(f"Error initializing AWS client: {e}")
        sys.exit(1)
    
    instance_id = args.instance_id
    
    # If instance ID provided but region detection needed
    if instance_id and not args.region:
        print(f"Searching for instance {instance_id} across regions...")
        detected_region = find_instance_region(instance_id)
        if not detected_region:
            print(f"Instance {instance_id} not found in any region")
            sys.exit(1)
        print(f"Found instance in region: {detected_region}")
        ec2_client = boto3.client('ec2', region_name=detected_region)
    
    # If no instance ID provided, show selection menu
    if not instance_id:
        instances = list_running_instances(ec2_client)
        instance_id = select_instance(instances)
        
        if not instance_id:
            print("No instance selected. Exiting.")
            sys.exit(1)
    
    # Create first launch template
    template_id = create_launch_template_from_instance(ec2_client, instance_id, args.template_name)
    
    if not template_id:
        sys.exit(1)
    
    created_template_ids = [template_id]
    
    # Ask if user wants to create a second template
    if ask_for_second_template():
        print("\n" + "="*60)
        print("Creating second launch template for recovery...")
        print("="*60)
        
        # Ask user if they want to use same instance or different instance
        instance_choice = ask_instance_choice()
        
        if instance_choice == 'same':
            second_instance_id = instance_id
        else:
            instances = list_running_instances(ec2_client)
            print("\nSelect instance for the second launch template:")
            second_instance_id = select_instance(instances)
        
        if second_instance_id:
            # Generate a different template name for the second template
            second_template_name = None
            if args.template_name:
                second_template_name = f"{args.template_name}-recovery"
            elif second_instance_id == instance_id:
                # Same instance, generate unique name
                instance_name = ec2_client.describe_instances(InstanceIds=[second_instance_id])['Reservations'][0]['Instances'][0].get('Tags', [])
                instance_name = next((tag['Value'] for tag in instance_name if tag['Key'] == 'Name'), second_instance_id)
                second_template_name = f"lt-{instance_name}-{second_instance_id}-recovery"
            
            second_template_id = create_launch_template_from_instance(ec2_client, second_instance_id, second_template_name)
            
            if second_template_id:
                created_template_ids.append(second_template_id)
                print("\n✓ Both launch templates created successfully!")
            else:
                print("\n⚠ First template created, but second template failed.")
        else:
            print("\n⚠ No instance selected for second template. Only first template was created.")
    
    # Ask if user wants to setup automated recovery
    if len(created_template_ids) > 0 and ask_for_automated_recovery():
        print("\n" + "="*60)
        print("Setting up automated recovery...")
        print("="*60)
        
        # Get region from EC2 client
        region = ec2_client.meta.region_name or args.region or 'us-east-1'
        
        # Pass recovery template for launching and primary template for monitoring
        if len(created_template_ids) < 2:
            print("\n⚠ Both primary and recovery templates are required for automated recovery.")
        elif setup_automated_recovery([created_template_ids[1]], region, instance_id, created_template_ids[0]):
            print("\n✓ Automated recovery setup completed successfully!")
        else:
            print("\n⚠ Automated recovery setup failed.")
    
    sys.exit(0)

if __name__ == '__main__':
    main()
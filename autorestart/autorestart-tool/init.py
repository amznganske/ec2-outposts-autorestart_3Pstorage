#!/usr/bin/env python3

import argparse
import boto3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from outpost_utils import get_outpost_info


def parse_arguments():
    parser = argparse.ArgumentParser(description='Deploy a CloudFormation stack to set up instance auto-restart based on status checks.')
    parser.add_argument('--launch-template-id', type=str, nargs='+', required=True, help='Launch template IDs')
    parser.add_argument('--primary-template-id', type=str, help='Primary template ID for instance monitoring (if different from launch templates)')
    parser.add_argument('--source-instance-id', type=str, help='Source Instance ID to monitor (auto-detected if not provided)')
    parser.add_argument('--template-file', type=str, required=True, help='Path to the CloudFormation template file')
    parser.add_argument('--stack-name', type=str, required=True, help='Name of the CloudFormation stack')
    parser.add_argument('--region', type=str, required=True, help='AWS region for the CloudFormation stack')
    parser.add_argument('--notification-email', type=str, required=True, help='Email address for SNS notifications')
    return parser.parse_args()


def prompt_descriptions(lt_ids, lt_id_type):
    descriptions = {}
    for lt in lt_ids:
        description = input(f"Enter a description for {lt_id_type} '{lt}': ")
        descriptions[lt] = description
    return descriptions


def prompt_stack_replacement(stack_name):
    response = input(f"The stack '{stack_name}' already exists. Do you want to replace it? (y/n): ")
    return response.strip().lower() == 'y'


def prompt_recovery_mode():
    print("\nRecovery Mode Options:")
    print("1. Automatic Recovery - Automatically restart instances when outpost fails")
    print("2. Notification Only - Send notifications but require manual recovery")
    while True:
        response = input("Choose recovery mode (1 for automatic, 2 for notification only): ").strip()
        if response == '1':
            return 'automatic'
        elif response == '2':
            return 'notification'
        else:
            print("Please enter 1 or 2.")


def prompt_template_confirmation():
    response = input("Please confirm if the generated template looks good. (y/n): ")
    return response.strip().lower() == 'y'


def stack_exists(client, stack_name):
    try:
        client.describe_stacks(StackName=stack_name)
        return True
    except client.exceptions.ClientError:
        return False


def wait_for_stack(client, stack_name, action):
    waiter = client.get_waiter('stack_' + ('update_complete' if action == 'update' else 'create_complete'))
    print(f"Waiting for stack {action} to complete...")
    try:
        waiter.wait(StackName=stack_name)
        print(f"Stack {stack_name} has been {action}d successfully.")
    except Exception as e:
        print(f"An error occurred while waiting for the stack {action} to complete: {str(e)}")
        sys.exit(1)


def create_or_update_stack(client, stack_name, template_body, parameters):
    if stack_exists(client, stack_name):
        print(f"Stack {stack_name} exists. Updating stack...")
        response = client.update_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=parameters,
            Capabilities=['CAPABILITY_NAMED_IAM']
        )
        wait_for_stack(client, stack_name, 'update')
    else:
        print(f"Stack {stack_name} does not exist. Creating stack...")
        response = client.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=parameters,
            Capabilities=['CAPABILITY_NAMED_IAM']
        )
        wait_for_stack(client, stack_name, 'create')


def generate_template_body(base_template_path, launch_template_descriptions, recovery_mode):
    # Use appropriate template based on recovery mode
    if recovery_mode == 'notification':
        template_path = os.path.join(os.path.dirname(base_template_path), 'NotificationOnlyTemplate.yaml')
    else:
        template_path = base_template_path
    
    with open(template_path, 'r') as file:
        template_body = file.read()

    outputs_lines = []
    for index, (template_id, description) in enumerate(launch_template_descriptions.items(), start=1):
        outputs_lines.extend([
            f"  LaunchTemplateId{index}:\n"
            f"    Description: \"{description}\"\n"
            f"    Value: \"{template_id}\"\n"
        ])
        outputs_section = ''.join(outputs_lines)

    template_body = template_body.replace("  # Outputs will be dynamically inserted here", outputs_section.rstrip())
    return template_body


def get_source_instance_id(ec2_client, primary_template_id):
    """Get source instance ID from primary launch template name pattern"""
    try:
        # Get launch template details
        template_response = ec2_client.describe_launch_templates(LaunchTemplateIds=[primary_template_id])
        template_name = template_response['LaunchTemplates'][0]['LaunchTemplateName']
        
        # Extract instance ID from template name (format: lt-{name}-{instance-id})
        if '-i-' in template_name:
            instance_id = 'i-' + template_name.split('-i-')[1]
            # Validate instance exists
            ec2_client.describe_instances(InstanceIds=[instance_id])
            return instance_id
        else:
            raise Exception(f"Cannot extract instance ID from template name: {template_name}")
    except Exception as e:
        raise Exception(f"Failed to get source instance ID: {e}")

def get_vpc_info_from_instance(ec2_client, instance_id):
    """Get VPC and private subnet information from source instance"""
    try:
        # Get instance details
        instance_response = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = instance_response['Reservations'][0]['Instances'][0]
        
        vpc_id = instance['VpcId']
        print(f"Found VPC ID: {vpc_id}")
        
        # Get all subnets in the VPC
        vpc_subnets_response = ec2_client.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        
        # Get route tables to identify private subnets
        route_tables_response = ec2_client.describe_route_tables(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        
        # Find subnets that don't have direct route to internet gateway
        private_subnets = []
        public_subnets = set()
        
        # Identify public subnets (those with IGW routes)
        for rt in route_tables_response['RouteTables']:
            has_igw = any(route.get('GatewayId', '').startswith('igw-') for route in rt['Routes'])
            if has_igw:
                # Check both explicit subnet associations and main route table
                for assoc in rt['Associations']:
                    if 'SubnetId' in assoc:
                        public_subnets.add(assoc['SubnetId'])
                    elif assoc.get('Main', False):
                        # Main route table applies to subnets without explicit associations
                        for subnet in vpc_subnets_response['Subnets']:
                            # Check if subnet has no explicit route table association
                            subnet_has_explicit_rt = False
                            for check_rt in route_tables_response['RouteTables']:
                                for check_assoc in check_rt['Associations']:
                                    if check_assoc.get('SubnetId') == subnet['SubnetId']:
                                        subnet_has_explicit_rt = True
                                        break
                                if subnet_has_explicit_rt:
                                    break
                            if not subnet_has_explicit_rt:
                                public_subnets.add(subnet['SubnetId'])
        
        # Collect only private subnets
        for subnet in vpc_subnets_response['Subnets']:
            if subnet['SubnetId'] not in public_subnets:
                private_subnets.append(subnet['SubnetId'])
                print(f"Found private subnet: {subnet['SubnetId']} in AZ: {subnet['AvailabilityZone']}")
            else:
                print(f"Skipping public subnet: {subnet['SubnetId']} in AZ: {subnet['AvailabilityZone']}")
        
        if not private_subnets:
            print("Error: No private subnets found in VPC. Lambda requires private subnets with NAT Gateway for internet access.")
            raise Exception("No private subnets available for Lambda deployment")
        
        # Ensure we have private subnets in different AZs for Lambda high availability
        selected_subnets = private_subnets[:2] if len(private_subnets) >= 2 else private_subnets
        print(f"Selected private subnets for Lambda: {selected_subnets}")
        
        return {
            'vpc_id': vpc_id,
            'subnet_ids': selected_subnets
        }
        
    except Exception as e:
        raise Exception(f"Failed to get VPC info from instance: {e}")

def main():
    args = parse_arguments()

    # Auto-detect source instance ID from primary launch template if not provided
    if not args.source_instance_id:
        print("Auto-detecting source instance ID from primary launch template...")
        try:
            ec2_client = boto3.client('ec2', region_name=args.region)
            
            # Use primary template or first launch template
            template_for_monitoring = args.primary_template_id or args.launch_template_id[0]
            source_instance_id = get_source_instance_id(ec2_client, template_for_monitoring)
            print(f"Detected Source Instance ID: {source_instance_id}")
                
        except Exception as e:
            print(f"Failed to auto-detect source instance ID: {e}")
            # Prompt user for manual input
            source_instance_id = input("Please enter the source instance ID to monitor: ").strip()
            if not source_instance_id:
                print("Source instance ID is required.")
                sys.exit(1)
    else:
        source_instance_id = args.source_instance_id
    
    # Get VPC info from the source instance
    print("Auto-detecting VPC info from source instance...")
    try:
        ec2_client = boto3.client('ec2', region_name=args.region)
        vpc_info = get_vpc_info_from_instance(ec2_client, source_instance_id)
        print(f"Detected VPC ID: {vpc_info['vpc_id']}")
        print(f"Detected Private Subnet IDs: {', '.join(vpc_info['subnet_ids'])}")
    except Exception as e:
        print(f"Failed to auto-detect VPC info: {e}")
        vpc_info = None

    launch_template_descriptions = prompt_descriptions(args.launch_template_id, "launch template ID")

    print("Descriptions provided for launch templates:")
    for template_id, description in launch_template_descriptions.items():
        print(f"{template_id}: {description}")

    recovery_mode = prompt_recovery_mode()
    print(f"\nSelected recovery mode: {recovery_mode}")
    
    if recovery_mode == 'notification':
        print("Note: Notification-only mode will send email alerts when outpost fails but will NOT automatically restart instances.")
        print("You will need to manually restart instances using the provided launch templates.")
    else:
        print("Note: Automatic recovery mode will automatically restart instances when outpost fails.")

    client = boto3.client('cloudformation', region_name=args.region)

    if stack_exists(client, args.stack_name) and not prompt_stack_replacement(args.stack_name):
        print("Operation cancelled by user.")
        sys.exit(0)

    template_body = generate_template_body(args.template_file, launch_template_descriptions, recovery_mode)

    print(f"Generated CloudFormation Template ({'Notification-Only' if recovery_mode == 'notification' else 'Automatic Recovery'} Mode):")
    print(template_body)

    if not prompt_template_confirmation():
        print("Operation cancelled by user.")
        sys.exit(0)

    parameters = [
        {
            'ParameterKey': 'StackName',
            'ParameterValue': args.stack_name
        },
        {
            'ParameterKey': 'SourceInstanceId',
            'ParameterValue': source_instance_id
        },
        {
            'ParameterKey': 'NotificationEmail',
            'ParameterValue': args.notification_email
        }
    ]
    
    # Add VPC parameters if detected
    if vpc_info:
        parameters.extend([
            {
                'ParameterKey': 'VpcId',
                'ParameterValue': vpc_info['vpc_id']
            },
            {
                'ParameterKey': 'SubnetIds',
                'ParameterValue': ','.join(vpc_info['subnet_ids'])
            }
        ])
    else:
        # Prompt for VPC info if not auto-detected
        vpc_id = input("Enter VPC ID for Lambda function: ").strip()
        subnet_ids = input("Enter comma-separated subnet IDs for Lambda function: ").strip()
        
        parameters.extend([
            {
                'ParameterKey': 'VpcId',
                'ParameterValue': vpc_id
            },
            {
                'ParameterKey': 'SubnetIds',
                'ParameterValue': subnet_ids
            }
        ])

    create_or_update_stack(client, args.stack_name, template_body, parameters)


if __name__ == "__main__":
    main()

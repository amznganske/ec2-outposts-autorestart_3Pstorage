#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError

def get_outpost_info(instance_id=None, region=None):
    """
    Automatically retrieve outpost ID and owner account ID.
    
    Args:
        instance_id: Optional EC2 instance ID to get outpost info from
        region: Optional AWS region, will auto-detect if not provided
    
    Returns:
        dict: {'outpost_id': str, 'owner_account_id': str, 'region': str}
    """
    
    # Auto-detect region if not provided
    if not region and instance_id:
        region = find_instance_region(instance_id)
    elif not region:
        region = boto3.Session().region_name or 'us-east-1'
    
    try:
        outposts_client = boto3.client('outposts', region_name=region)
        
        # If instance_id provided, get outpost from instance
        if instance_id:
            ec2_client = boto3.client('ec2', region_name=region)
            response = ec2_client.describe_instances(InstanceIds=[instance_id])
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    placement = instance.get('Placement', {})
                    outpost_arn = placement.get('OutpostArn')
                    
                    if outpost_arn:
                        outpost_id = outpost_arn.split('/')[-1]
                        owner_account_id = outpost_arn.split(':')[4]
                        return {
                            'outpost_id': outpost_id,
                            'owner_account_id': owner_account_id,
                            'region': region
                        }
        
        # Otherwise, list available outposts and use first one
        response = outposts_client.list_outposts()
        outposts = response.get('Outposts', [])
        
        if outposts:
            outpost = outposts[0]  # Use first available outpost
            outpost_id = outpost['OutpostId']
            owner_account_id = outpost['OwnerId']
            
            return {
                'outpost_id': outpost_id,
                'owner_account_id': owner_account_id,
                'region': region
            }
        
        raise Exception("No outposts found in the account")
        
    except ClientError as e:
        raise Exception(f"Failed to retrieve outpost information: {e}")

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

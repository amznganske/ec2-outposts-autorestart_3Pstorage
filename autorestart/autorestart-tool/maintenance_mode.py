#!/usr/bin/env python3

import argparse
import boto3
import sys
from botocore.exceptions import ClientError

def parse_arguments():
    parser = argparse.ArgumentParser(description='Enable/disable maintenance mode for autorestart CloudWatch alarms')
    parser.add_argument('--stack-name', type=str, required=True, help='CloudFormation stack name')
    parser.add_argument('--region', type=str, required=True, help='AWS region')
    parser.add_argument('--action', type=str, choices=['enable', 'disable'], required=True, 
                       help='enable: disable alarm (maintenance mode), disable: enable alarm (normal mode)')
    return parser.parse_args()

def get_alarm_name(stack_name):
    return f"InstanceStatusCheckAlarm-{stack_name}"

def enable_maintenance_mode(cloudwatch_client, alarm_name):
    """Disable the CloudWatch alarm to prevent recovery during maintenance"""
    try:
        cloudwatch_client.disable_alarm_actions(AlarmNames=[alarm_name])
        print(f"✓ Maintenance mode ENABLED - Alarm actions disabled for {alarm_name}")
        print("  Recovery will NOT trigger during maintenance")
        return True
    except ClientError as e:
        print(f"✗ Error enabling maintenance mode: {e}")
        return False

def disable_maintenance_mode(cloudwatch_client, alarm_name):
    """Enable the CloudWatch alarm to resume normal recovery operations"""
    try:
        cloudwatch_client.enable_alarm_actions(AlarmNames=[alarm_name])
        print(f"✓ Maintenance mode DISABLED - Alarm actions enabled for {alarm_name}")
        print("  Recovery will trigger normally on instance failures")
        return True
    except ClientError as e:
        print(f"✗ Error disabling maintenance mode: {e}")
        return False

def check_alarm_status(cloudwatch_client, alarm_name):
    """Check current alarm status"""
    try:
        response = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
        if not response['MetricAlarms']:
            print(f"✗ Alarm {alarm_name} not found")
            return False
        
        alarm = response['MetricAlarms'][0]
        actions_enabled = alarm['ActionsEnabled']
        state = alarm['StateValue']
        
        print(f"Current alarm status:")
        print(f"  Alarm Name: {alarm_name}")
        print(f"  State: {state}")
        print(f"  Actions Enabled: {actions_enabled}")
        print(f"  Maintenance Mode: {'DISABLED' if actions_enabled else 'ENABLED'}")
        
        return True
    except ClientError as e:
        print(f"✗ Error checking alarm status: {e}")
        return False

def main():
    args = parse_arguments()
    
    try:
        cloudwatch_client = boto3.client('cloudwatch', region_name=args.region)
        alarm_name = get_alarm_name(args.stack_name)
        
        print(f"Managing maintenance mode for stack: {args.stack_name}")
        print(f"Region: {args.region}")
        print(f"Alarm: {alarm_name}")
        print("-" * 50)
        
        # Check current status
        if not check_alarm_status(cloudwatch_client, alarm_name):
            sys.exit(1)
        
        print("-" * 50)
        
        # Perform requested action
        if args.action == 'enable':
            success = enable_maintenance_mode(cloudwatch_client, alarm_name)
        else:
            success = disable_maintenance_mode(cloudwatch_client, alarm_name)
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
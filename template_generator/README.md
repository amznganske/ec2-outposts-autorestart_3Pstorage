# 3P Storage Recovery Launch Template Generator

Creates launch templates from running EC2 instances for Outpost Server recovery scenarios. Supports automated recovery setup with cross-account CloudWatch monitoring. Can be run standalone or invoked by the launch_wizard.

## Usage

```bash
python init.py [options]
```

## Options

- `-i, --instance-id`: EC2 instance ID (optional, will prompt if not provided)
- `-n, --template-name`: Launch template name (optional, auto-generated if not provided)
- `-r, --region`: AWS region (optional, uses default AWS config if not provided)
- `--list-regions`: List available AWS regions

## Features

- **Interactive Instance Selection**: Lists running instances if none specified
- **Dual Template Creation**: Option to create primary and recovery templates
- **Flexible Instance Choice**: Use same instance or different instance for recovery template
- **Subnet Selection**: Choose target subnet for each template
- **Automated Recovery Setup**: Optional integration with autorestart tool for CloudFormation-based recovery
- **Cross-Platform**: Works on Windows and Unix-like systems
- **Cross-Account Support**: Supports outpost owner account ID for proper metric monitoring

## Workflow

1. Select or specify source EC2 instance
2. Create primary launch template
3. Optionally create recovery template:
   - Same instance (for different Outpost Server)
   - Different instance
4. Optionally setup automated recovery:
   - Prompts for source Outpost ID
   - Prompts for outpost owner account ID (for EC2 instance status metric)
   - Prompts for CloudFormation stack name
   - Prompts for notification email
   - Uses only recovery templates for automated setup

## Requirements

- AWS CLI configured with appropriate credentials
- Running EC2 instances in the target region
- Permissions for EC2 describe/create operations
- For automated recovery: CloudFormation permissions and outpost owner account ID

## Automated Recovery Parameters

When setting up automated recovery, you'll be prompted for:
- **Source Outpost ID**: The Outpost where instances are running
- **Outpost Owner Account ID**: Account that owns the Outpost hardware (for ConnectedStatus metric)
- **CloudFormation Stack Name**: Name for the recovery stack
- **Notification Email**: Email for recovery notifications

## Examples

```bash
# Interactive mode
python init.py

# Specify instance and region
python init.py -i i-1234567890abcdef0 -r us-west-2

# Custom template name
python init.py -n my-template -r us-east-1
```

## Integration

This tool integrates with:
- **launch_wizard**: Automatically invoked after successful EC2 instance launch
- **autorestart tool**: For CloudFormation-based automated recovery setup
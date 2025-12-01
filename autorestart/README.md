## EC2 on Outpost Servers with 3rd party storage Auto-Recovery Tool

This repository contains a tool that will set up infrastructure on your AWS account to allow for automatic recovery of EC2 instances based on instance status check failures.

## Usage

```bash
python init.py --launch-template-id <template-id> --source-instance-id <instance-id> --template-file <template-file> --stack-name <stack-name> --region <region> --notification-email <email>
```

## Required Parameters

- `--launch-template-id`: One or more launch template IDs (space-separated)
- `--source-instance-id`: Source instance ID to monitor (auto-detected if not provided)
- `--template-file`: Path to the CloudFormation template file
- `--stack-name`: Name of the CloudFormation stack
- `--region`: AWS region for the CloudFormation stack
- `--notification-email`: Email address for SNS notifications

## Auto-Detection Features

- **Instance ID**: Automatically extracted from primary launch template name
- **VPC Configuration**: Automatically detected from source instance
- **Private Subnets**: Automatically identified for Lambda deployment

## Recovery Modes

The tool supports two recovery modes:

### 1. Automatic Recovery (Default)
- Automatically launches replacement instances when instance status checks fail
- Monitors EC2 StatusCheckFailed_Instance metric (4-minute failure detection)
- Updates ALB target groups automatically
- Sends email notifications for success/failure

### 2. Notification Only
- Sends detailed email alerts when instance status checks fail
- Includes launch template information for manual recovery
- Requires manual instance restart using provided templates
- No automatic instance launching

## Features

- **Instance Status Monitoring**: Monitors EC2 StatusCheckFailed_Instance metric
- **4-Minute Detection**: Triggers recovery after 4 consecutive minutes of status check failures
- **VPC Integration**: Lambda function deployed in same VPC as monitored instance
- **Interactive Setup**: Prompts for launch template descriptions and recovery mode
- **Stack Management**: Creates or updates existing CloudFormation stacks
- **Template Validation**: Shows generated template for user confirmation
- **Flexible Recovery**: Choose between automatic or notification-only recovery
- **ALB Integration**: Automatically updates load balancer target groups (automatic mode)
- **Email Notifications**: Sends detailed notifications via SNS
- **Maintenance Mode**: Script available to disable/enable recovery during maintenance

## CloudFormation Resources Created

### Automatic Recovery Mode
- CloudWatch Alarm for EC2 StatusCheckFailed_Instance monitoring
- Lambda function for instance launch and ALB management (deployed in VPC)
- Lambda security group with HTTPS egress for AWS API calls
- SNS topics for notifications
- IAM roles and policies with VPC access
- KMS key for encryption

### Notification Only Mode
- CloudWatch Alarm for EC2 StatusCheckFailed_Instance monitoring
- Lambda function for formatted email notifications (deployed in VPC)
- Lambda security group with HTTPS egress for AWS API calls
- SNS topics for email notifications
- IAM roles and policies (minimal permissions with VPC access)
- KMS key for encryption

## Maintenance Mode

Use the `maintenance_mode.py` script to disable recovery during maintenance:

```bash
# Enable maintenance mode (disable recovery)
python maintenance_mode.py --stack-name <stack-name> --region <region> --action enable

# Disable maintenance mode (resume recovery)
python maintenance_mode.py --stack-name <stack-name> --region <region> --action disable
```

## Integration

This tool is typically called by the template_generator tool during automated recovery setup.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.


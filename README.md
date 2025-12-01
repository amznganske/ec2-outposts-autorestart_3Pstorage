# Outpost Server Recovery Solution

A comprehensive solution for AWS Outpost Server recovery that provides third-party storage integration, launch template generation, and automated recovery capabilities.

## Solution Components

This solution consists of three main components that can be used individually or as part of an integrated workflow:

### 1. Third-Party Storage Integration
**Location**: `sample-outposts-third-party-storage-integration/launch_wizard/`

Launch EC2 instances on AWS Outposts with integrated third-party storage support.

**Features**:
- Multi-vendor support (NetApp, Pure Storage, Generic)
- Multi-protocol support (iSCSI, NVMe)
- SAN boot and local boot configurations
- Cross-platform compatibility

**Usage**:
```bash
cd sample-outposts-third-party-storage-integration
python -m launch_wizard [vendor] [protocol] [options]
```

### 2. Launch Template Generation
**Location**: `template_generator/`

Create launch templates from running EC2 instances for recovery scenarios.

**Features**:
- Interactive instance selection
- Dual template creation (primary and recovery)
- Subnet selection for recovery scenarios
- Automated recovery integration

**Usage**:
```bash
cd template_generator
python init.py [options]
```

### 3. Automated Recovery Setup
**Location**: `autorestart/autorestart-tool/`

Deploy CloudFormation-based recovery system for Outpost failures with flexible recovery options.

**Recovery Modes**:
- **Automatic Recovery**: Automatically restart instances on Outpost failure
- **Notification Only**: Send alerts for manual recovery

**Features**:
- Cross-account CloudWatch monitoring
- Configurable recovery behavior (automatic vs manual)
- ALB target group management (automatic mode)
- Detailed email notifications with recovery instructions

```

## Integrated Workflow

The complete workflow automatically integrates all three components:

1. **Launch Instance**: Use launch wizard to create EC2 instance with storage integration
2. **Generate Templates**: Automatically prompted to create launch templates after successful launch
3. **Setup Recovery**: Optionally configure automated recovery using generated templates

```bash
# Start integrated workflow
cd sample-outposts-third-party-storage-integration
python -m launch_wizard netapp nvme
# Follow prompts for template generation and recovery setup
```

## IAM Permissions Required
- Grant only the minimum permissions required for each specific use case
- Use resource-specific ARNs instead of `"*"` wherever possible
- Regularly audit and remove unused permissions
- Consider using IAM roles instead of long-term access keys
### 1. Third-Party Storage Integration

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "ec2:ModifySubnetAttribute",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "ec2:CreateVpcEndpoint",
                "ec2:DescribeVpcEndpoints",
                "ec2:DeleteVpcEndpoints",
                "ec2:CreateSecurityGroup",
                "ec2:RevokeSecurityGroupEgress",
                "ec2:AuthorizeSecurityGroupEgress",
                "ec2:DescribeLaunchTemplates",
                "ec2:DescribeLaunchTemplateVersions",
                "ec2:DescribeInstances",
                "ec2:DescribeRouteTables"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateLaunchTemplate",
                "ec2:DescribeLaunchTemplates",
                "ec2:DescribeLaunchTemplateVersions",
                "ec2:DeleteLaunchTemplate",
                "ec2:CreateLaunchTemplateVersion",
                "ec2:DeleteLaunchTemplateVersions"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateNetworkInterface",
                "ec2:CreateTags"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "iam:ListInstanceProfiles",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "secretsmanager:ListSecrets",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "secretsmanager:GetSecretValue",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "outposts:GetOutpost",
                "outposts:GetOutpostInstanceTypes"
            ],
            "Resource": "*"
        }
    ]
}
```

### 2. Launch Template Generation

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceAttribute",
                "ec2:DescribeSubnets",
                "ec2:DescribeLaunchTemplates",
                "ec2:CreateLaunchTemplate"
            ],
            "Resource": "*"
        }
    ]
}
```

### 3. Automated Recovery Setup

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DescribeStacks",
                "cloudformation:GetTemplate"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:GetRolePolicy",
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy",
                "iam:PutRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:GetRole",
                "iam:TagRole",
                "iam:PassRole"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sqs:CreateQueue",
                "sqs:SetQueueAttributes",
                "sqs:GetQueueAttributes",
                "sqs:deletequeue",
                "sqs:TagQueue"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:CreateFunction",
                "lambda:DeleteFunction",
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "lambda:AddPermission",
                "lambda:RemovePermission",
                "lambda:TagResource",
                "lambda:PutFunctionConcurrency",
                "lambda:GetFunction"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:CreateTopic",
                "sns:DeleteTopic",
                "sns:Subscribe",
                "sns:Unsubscribe",
                "sns:GetTopicAttributes",
                "sns:TagResource",
                "sns:SetTopicAttributes"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricAlarm",
                "cloudwatch:DeleteAlarms",
                "cloudwatch:DescribeAlarms"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "kms:CreateKey",
                "kms:DisableKey",
                "kms:CreateAlias",
                "kms:DeleteAlias",
                "kms:DescribeKey",
                "kms:PutKeyPolicy",
                "kms:GetKeyRotationStatus",
                "kms:Encrypt",
                "kms:CreateGrant",
                "kms:EnableKeyRotation"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "outposts:ListOutposts"
            ],
            "Resource": "*"
        }
    ]
}
```

### Runtime Permissions (Lambda Function)

The deployed Lambda function requires these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:RunInstances",
                "ec2:CreateTags",
                "ec2:DescribeInstances",
                "ec2:DescribeLaunchTemplates",
                "elasticloadbalancing:DescribeTargetGroups",
                "elasticloadbalancing:DescribeTargetHealth",
                "elasticloadbalancing:RegisterTargets",
                "elasticloadbalancing:DeregisterTargets",
                "outposts:ListAssets",
                "outposts:GetOutpost",
                "cloudformation:DescribeStacks",
                "cloudwatch:DescribeAlarmHistory",
                "sns:Publish",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "sts:GetCallerIdentity",
                "ssm:GetParameters",
                "kms:Decrypt",
                "kms:GenerateDataKey",
                "sqs:SendMessage"
            ],
            "Resource": "*"
        }
    ]
}
```

## Automatic Outpost Detection

The solution now includes automatic detection of outpost ID and owner account ID, eliminating the need for manual input in most scenarios.

### How It Works

- **Launch Template Generation**: Automatically detects outpost information when setting up recovery
- **Automated Recovery Setup**: Auto-detects outpost details, with manual fallback if needed
- **Instance-Based Detection**: Can extract outpost information from existing EC2 instances

### Testing Automatic Detection

```bash
# Test the outpost detection utility
python test_outpost_utils.py
```

### Manual Override

You can still provide outpost information manually if needed:

```bash
# Autorestart tool with manual outpost info
cd autorestart/autorestart-tool
python init.py --source-outpost-id op-1234567890abcdef0 --outpost-owner-account-id 123456789012 [other options]
```

## Requirements

- Python 3.7+
- AWS CLI configured with appropriate credentials
- AWS Outposts environment
- Third-party storage arrays (for storage integration)
- Bootable operating system volumes (for storage integration)

## Installation

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure AWS credentials
4. Follow component-specific usage instructions

## Architecture

See [SOLUTION_FLOW.md](SOLUTION_FLOW.md) for detailed architecture and workflow documentation.

## Security Considerations

- Use IAM roles with least privilege principles
- Store storage array credentials in AWS Secrets Manager
- Enable CloudTrail for audit logging
- Use KMS encryption for sensitive data
- Regularly rotate credentials

## Support

This solution is provided as a sample for demonstration purposes. Each component includes detailed README files with specific usage instructions and troubleshooting guidance.
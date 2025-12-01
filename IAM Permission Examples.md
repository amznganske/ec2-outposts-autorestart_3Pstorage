# IAM Permission Examples For Deployment

## Security Best Practices

### Principle of Least Privilege
- Grant only the minimum permissions required for each specific use case
- Use resource-specific ARNs instead of `"*"` wherever possible
- Regularly audit and remove unused permissions
- Consider using IAM roles instead of long-term access keys

### Resource-Specific Permissions
Replace `"*"` with specific resource ARNs when possible:
```json
"Resource": [
    "arn:aws:ec2:region:account-id:subnet/subnet-12345678",
    "arn:aws:ec2:region:account-id:security-group/sg-12345678"
]
```

### Secrets Manager Security
- Limit `secretsmanager:GetSecretValue` to specific secret ARNs
- Use resource-based policies on secrets for additional access control
- Enable automatic rotation for storage array credentials

### Monitoring and Auditing
- Enable CloudTrail for all API calls
- Use CloudWatch to monitor permission usage
- Set up alerts for unusual access patterns
- Regularly review IAM Access Analyzer findings

---

## Policy Required for AWS Outpost Server EC2 Instance Launch Wizard
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
            "Resource": [
                "*"
            ]
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
            "Sid": "SecretsManagerPermissions",
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
## Policy Required for Automated Recovery of EC2 Instances on AWS Outpost Servers

**Security Note**: This policy grants broad permissions for CloudFormation stack management. In production environments, consider:
- Restricting CloudFormation actions to specific stack ARNs
- Using IAM conditions to limit resource creation
- Implementing approval workflows for infrastructure changes
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
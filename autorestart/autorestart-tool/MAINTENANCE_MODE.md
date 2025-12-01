# Maintenance Mode for Autorestart Recovery

This script allows you to temporarily disable the CloudWatch alarm that triggers automatic recovery during maintenance windows.

## Usage

### Enable Maintenance Mode (Disable Recovery)
```bash
python maintenance_mode.py --stack-name <stack-name> --region <region> --action enable
```

### Disable Maintenance Mode (Enable Recovery)
```bash
python maintenance_mode.py --stack-name <stack-name> --region <region> --action disable
```

### Check Current Status
The script automatically shows the current alarm status before making changes.

## Examples

```bash
# Enable maintenance mode for stack "autorestart-myinstance" in us-east-1
python maintenance_mode.py --stack-name autorestart-myinstance --region us-east-1 --action enable

# Disable maintenance mode (resume normal recovery)
python maintenance_mode.py --stack-name autorestart-myinstance --region us-east-1 --action disable
```

## What It Does

- **Enable Maintenance Mode**: Disables CloudWatch alarm actions, preventing automatic recovery
- **Disable Maintenance Mode**: Enables CloudWatch alarm actions, resuming normal recovery
- **Status Check**: Shows current alarm state and whether actions are enabled

## Important Notes

- The alarm will still monitor the instance and change states, but won't trigger recovery actions when disabled
- Always remember to disable maintenance mode after maintenance is complete
- The script requires CloudWatch permissions: `cloudwatch:DescribeAlarms`, `cloudwatch:EnableAlarmActions`, `cloudwatch:DisableAlarmActions`

## IAM Permissions Required

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:DescribeAlarms",
                "cloudwatch:EnableAlarmActions",
                "cloudwatch:DisableAlarmActions"
            ],
            "Resource": "*"
        }
    ]
}
```
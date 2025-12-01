# Outpost Server Recovery Solution Flow

This document describes the complete workflow for the Outpost Server recovery solution, from initial EC2 instance launch to automated recovery setup.

## Solution Architecture

![Solution Flow Diagram](diagrams/solution_flow_diagram.png)

## Workflow Steps

### 1. Initial Setup
- **User** initiates the launch wizard CLI
- **Launch Wizard** (`sample-outposts-third-party-storage-integration/launch_wizard/__main__.py`) collects configuration parameters
- **EC2 Helper** (`sample-outposts-third-party-storage-integration/launch_wizard/aws/ec2.py`) validates AWS resources and configurations

### 2. Instance Launch
- **EC2 Instance** is launched on the **AWS Outpost** via `launch_instance_helper()` function
- Instance connects to **3P Storage Array** using configured protocols (iSCSI/NVMe)
- System waits for instance to reach running state (up to 5 minutes)

### 3. Launch Template Generation
- **EC2 Helper** (`sample-outposts-third-party-storage-integration/launch_wizard/aws/ec2.py`) prompts user for launch template creation
- **Launch Template Generator** (`3pstorage_recover/init.py`) creates primary template from running instance
- Optional creation of recovery template for failover scenarios
- Cross-platform subprocess execution handles Windows/Unix compatibility

### 4. Automated Recovery Setup
- **AutoRestart Tool** (`autorestart/autorestart-tool/init.py`) configures automated recovery system
- **CloudFormation Stack** (`autorestart/autorestart-tool/AutoRestartTemplate.yaml`) deploys monitoring and recovery infrastructure
- System monitors Outpost health via cross-account ConnectedStatus metric and automatically restarts instances on failure

## Key Components

### Launch Wizard CLI
**Location**: `sample-outposts-third-party-storage-integration/launch_wizard/`
- Interactive command-line interface (`__main__.py`)
- Multi-vendor storage support (NetApp, Pure Storage, Generic)
- Multi-protocol support (iSCSI, NVMe)
- Cross-platform compatibility (Windows, Linux, macOS)

### EC2 Helper
**Location**: `sample-outposts-third-party-storage-integration/launch_wizard/aws/ec2.py`
- AWS resource validation
- Instance launch orchestration (`launch_instance_helper()` function)
- Launch template creation coordination
- Recovery system integration via subprocess calls

### Launch Template Generator
**Location**: `3pstorage_recover/init.py`
- Extracts instance configuration (`create_launch_template_from_instance()` function)
- Creates reusable launch templates
- Handles network interface configuration
- Preserves user data and metadata
- Integrates with automated recovery setup (`setup_automated_recovery()` function)

### AutoRestart Tool
**Location**: `autorestart/autorestart-tool/init.py`
- CloudFormation-based deployment
- Outpost health monitoring with cross-account support
- Automatic instance recovery
- Email notifications for recovery events
- Template: `autorestart/autorestart-tool/AutoRestartTemplate.yaml`

### Recovery System
**CloudFormation Template**: `autorestart/autorestart-tool/AutoRestartTemplate.yaml`
- CloudWatch alarms for Outpost monitoring (ConnectedStatusAlarm)
- Lambda functions for recovery logic (embedded in template)
- SNS notifications for status updates
- Support for multiple launch templates
- Cross-account metric monitoring using outpost owner account ID

## Recovery Scenarios

### Primary Recovery
**Handled by**: `3pstorage_recover/init.py`
- Uses recovery launch templates created from the original instance
- Deploys to alternative subnets/Outpost Servers
- Maintains storage connectivity and configuration
- Supports same-instance or different-instance recovery scenarios

### Automated Failover
**Handled by**: CloudFormation Lambda function in `AutoRestartTemplate.yaml`
- Monitors Outpost ConnectedStatus metric from outpost owner account
- Triggers automatic instance restart on Outpost failure
- Updates load balancer targets if configured (`update_alb_target_group()` function)
- Sends notifications to administrators via SNS topics

## Script Locations Summary

| Component | Script Location | Key Functions |
|-----------|----------------|---------------|
| Launch Wizard | `sample-outposts-third-party-storage-integration/launch_wizard/__main__.py` | CLI entry point |
| EC2 Helper | `sample-outposts-third-party-storage-integration/launch_wizard/aws/ec2.py` | `launch_instance_helper()` |
| Launch Template Generator | `template_generator/init.py` | `create_launch_template_from_instance()`, `setup_automated_recovery()` |
| AutoRestart Tool | `autorestart/autorestart-tool/init.py` | CloudFormation stack deployment |
| CloudFormation Template | `autorestart/autorestart-tool/AutoRestartTemplate.yaml` | Infrastructure as Code |

## Benefits

- **Reduced Downtime**: Automated recovery minimizes manual intervention
- **Consistent Configuration**: Launch templates ensure identical instance setup
- **Flexible Deployment**: Support for multiple recovery scenarios
- **Comprehensive Monitoring**: CloudWatch integration for health monitoring
- **Scalable Solution**: Support for multiple instances and templates
- **Cross-Account Support**: Proper monitoring of outpost owner metrics
# Configuring On-Premises Data Infrastructure for Lamin

This guide explains how to set up your data infrastructure components to work with Lamin services.

## Setting Up S3 Bucket for Lamin Access

There are two ways to connect your S3 bucket to Lamin:

### Option 1: Using the Lamin Console (Recommended)

1. Log in to your Lamin organization dashboard
2. Navigate to the "Storage" tab in your organization settings
3. Click "Connect S3 Bucket"
4. Follow the on-screen instructions to complete the connection

### Option 2: Manual Bucket Policy Configuration

If you prefer to configure access manually:

1. Create or select an existing S3 bucket
2. Follow the instructions in our [S3 Bucket Policy documentation](bucket-policy.md) to attach the required IAM policy
3. Contact Lamin support to register your bucket in our system

## Setting Up PostgreSQL Database for Lamin Access

To connect your PostgreSQL database to Lamin services:

### 1. Database Prerequisites

Ensure your PostgreSQL database has the default `postgres` user with superuser privileges. When setting up a new PostgreSQL instance, this user is typically created automatically.

### 2. Whitelist Lamin Service IPs

After confirming your PostgreSQL user setup, you need to whitelist the appropriate Lamin outbound IP addresses for your region in your database's security group or firewall.

Refer to our [Service Endpoints and IP Whitelisting documentation](service-endpoints.md) to find the correct IPs to whitelist based on your region.

### 3. RDS Configuration Example

Refer to our [Create RDS Example](create-rds-example.md) for a Pulumi implementation that includes the proper network configuration and security settings.

# Configuring on-premises data infrastructure for Lamin

This guide explains how to set up your data infrastructure components to work with Lamin services.

## Setting up S3 bucket for Lamin access

There are two ways to connect your S3 bucket to Lamin:

### Option 1: Using the Lamin console (recommended)

1. Log in to your Lamin organization dashboard
2. Navigate to the "Storage" tab in your organization settings
3. Click "Connect S3 Bucket"
4. Follow the on-screen instructions to complete the connection

### Option 2: Manual bucket policy configuration

If you prefer to configure access manually:

1. Create or select an existing S3 bucket
2. Follow the instructions in our [S3 bucket policy documentation](bucket-policy.md) to attach the required IAM policy
3. Contact Lamin support to register your bucket in our system

## Setting up PostgreSQL database for Lamin access

To connect your PostgreSQL database to Lamin services:

### 1. Database prerequisites

Ensure your PostgreSQL database meets these requirements:

- Has the default `postgres` user with superuser privileges
- Has a default database named `postgres`

When setting up a new PostgreSQL instance, both the `postgres` user and `postgres` database are typically created automatically. If using a custom setup, ensure both exist.

### 2. Whitelist Lamin service IPs

After confirming your PostgreSQL setup, you need to whitelist the appropriate Lamin outbound IP addresses for your region in your database's security group or firewall.

Refer to our [service endpoints and IP whitelisting documentation](service-endpoints.md) to find the correct IPs to whitelist based on your region.

### 3. RDS configuration example

Refer to our [create RDS example](create-rds-example.md) for a Pulumi implementation that includes the proper network configuration and security settings.

# Lamin Instance Creation Guide

This guide explains how to create a Lamin instance using a provided API endpoint.


## Prerequisites

### Database Server

Ensure you have access to a PostgreSQL server with a default `postgres` database and a default superuser `postgres`.
If needed, you can whitelist api server IP addresses provided [here](service-endpoints.md) for your region.

### Storage

You can optionally provide your own S3 bucket when creating an instance. If you don't want to do that, you can skip this step.

To give Lamin access to your bucket, [this](bucket-policy.md) policy needs to be attached. 
- This can be [manually through the AWS console](https://docs.aws.amazon.com/AmazonS3/latest/userguide/add-bucket-policy.html)
- This can be also be done through lamin.ai once your instance is setup 

## Endpoint Parameters

- `API_URL`: The URL of the API, refer to [this](service-endpoints.md)
- `DB_SERVER_URL`: The URL for the PostgreSQL server in the format `postgresql://postgres:<password>@<host>:<port>/postgres`.
- `NAME`: The name of the Lamin instance.

Optionals:
- `SCHEMA`: The list of schema you to use, e.g., `bionty,wetlab`.
- `STORAGE`: The S3 bucket for storage (optional).


## Creating a Lamin Instance

We recommend using the Python scripts below to create a Lamin instance, as it leverages `lamindb_setup` to retrieve your access token. 

Please use the `lamin login` command first to ensure you're properly authenticated.

```python
import requests
from lamindb_setup import settings

API_URL = "https://qjv38prsit.us-west-2.awsapprunner.com" # Update API_URL according to the region where you to deploy.
DB_SERVER_URL = "postgresql://postgres:<password>@<host>:<port>/postgres"
NAME = "your-instance-name"
SCHEMA = "bionty"
STORAGE = "s3://your-bucket-name"

response = requests.post(
    f"{API_URL}/instance/create?db_server_url={DB_SERVER_URL}&name={NAME}&schema_str={SCHEMA}&storage={STORAGE}",
    headers={"authentication": f"Bearer {settings.user.access_token}"},
)
```
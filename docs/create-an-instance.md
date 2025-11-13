# Create a LaminDB instance on LaminHub

:warning: Currently, these instructions are for customers only.

This guide explains how to create a LaminDB instance that's fully deployed in LaminHub and comes with default SQL permission roles.

Two things happen in addition to the open-source `lamin init`:

- connecting the LaminHub backend to your Postgres database
- creating SQL permission roles `read`, `write`, and `admin` and synching them with storage permissions

## Prerequisites

If you want to use your own infrastructure to create the instance (PostgreSQL database or S3 bucket), it must be properly configured for Lamin access.

Refer to our [configuring on-premises data infrastructure](configure-on-prem-data-infra.md) guide for setup instructions.

## Endpoint parameters

- `API_URL`: The URL of the API from our [service endpoints documentation](service-endpoints.md)
- `DB_SERVER_URL`: The URL for the PostgreSQL server in the format `postgresql://postgres:<password>@<host>:<port>/postgres`
- `NAME`: The name of the LaminDB instance

Optional parameters:

- `SCHEMA`: The list of schemas you want to mount, e.g., `bionty,wetlab`
- `STORAGE`: The S3 bucket URI in the format `s3://my-bucket`

## Create the instance

Install `lamindb_setup` via `pip install lamindb_setup` if you don't have a lamindb installation.

In your terminal, run `lamin login` to ensure you're authenticated.

To create the instance, run the following python code:

```python
import requests
from lamindb_setup import settings

API_URL = "https://aws.us-west-2.lamin.ai/api"  # Update API_URL according to your region
DB_SERVER_URL = "postgresql://postgres:<PASSWORD>@<HOST>:<PORT>/postgres"
NAME = "YOUR-INSTANCE-NAME"
SCHEMA_STR = "bionty"
STORAGE = "s3://YOUR-BUCKET-NAME"

response = requests.put(
    f"{API_URL}/instances?db_server_url={DB_SERVER_URL}&name={NAME}&schema_str={SCHEMA_STR}&storage={STORAGE}",
    headers={"authentication": f"Bearer {settings.user.access_token}"},
)
```

Upon success, navigate to `https://lamin.ai/handle/instance-name`, where `handle` is your user handle and `instance-name` the `NAME` parameter above.

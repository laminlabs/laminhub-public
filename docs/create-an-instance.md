# Create a LaminDB instance on LaminHub

This guide explains how to create a LaminDB instance that's fully deployed in LaminHub and comes with default SQL permission roles.

Two things happen in addition to the open-source `lamin init`:

- connecting the LaminHub backend to your Postgres database
- creating SQL permission roles `read`, `write`, and `admin` and synching them with storage permissions

## Prerequisites

### Database server

Ensure you have access to a PostgreSQL server with a default database called `postgres` and a default superuser called `postgres`.

Ensure that our LaminHub backend servers are whitelisted so that our servers can access your database. The IP addresses are listed [here](service-endpoints.md)) resoled by AWS region.

### Storage

You can optionally provide your S3 bucket to serve as the default storage location of a LaminDB instance.

To give Lamin access to your bucket, attach [this AWS permission policy](bucket-policy.md) ([here is how to do this manually through the AWS console](https://docs.aws.amazon.com/AmazonS3/latest/userguide/add-bucket-policy.html)).

### Endpoint Parameters

- `API_URL`: The URL of the API, depending on your region, pick from [here](service-endpoints.md)
- `DB_SERVER_URL`: The URL for the PostgreSQL server in the format `postgresql://postgres:<password>@<host>:<port>/postgres`
- `NAME`: The name of the LaminDB instance

Optionals:
- `SCHEMA`: The list of schemas you want to mount, e.g., `bionty,wetlab`
- `STORAGE`: The S3 bucket URI in the format `s3://my-bucket`

## Create the instance

Install `lamindb_setup` via `pip install lamindb_setup` in case you don't have a lamindb installation.

In your terminal, run `lamin login` to ensure you're authenticated.

To create the instance, run the following python code:

```python
import requests
from lamindb_setup import settings

API_URL = "https://us-west-2.api.lamin.ai"  # Update API_URL according to the region where you to deploy.
DB_SERVER_URL = "postgresql://postgres:<PASSWORD>@<HOST>:<PORT>/postgres"
NAME = "YOUR-INSTANCE-NAME"
SCHEMA_STR = "bionty"
STORAGE = "s3://YOUR-BUCKET-NAME"

response = requests.post(
    f"{API_URL}/instance/create?db_server_url={DB_SERVER_URL}&name={NAME}&schema_str={SCHEMA_STR}&storage={STORAGE}",
    headers={"authentication": f"Bearer {settings.user.access_token}"},
)
```

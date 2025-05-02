# Database Server API Documentation

This guide provides instructions for managing database servers through the Lamin REST API.

## Important: Connection String Format

Lamin requires a specific PostgreSQL connection string format. You must:

- Use the default `postgres` user
- Use the default `postgres` database name
- Provide your specific password, host, and port values

The connection string format is:

```
postgresql://postgres:<your-password>@<your-host>:<your-port>/postgres
```

## API Endpoints

### Register a Database Server

**Endpoint**: `POST /db/server/register`

**Headers**:

- `Authorization: Bearer ACCESS_TOKEN`
- `Content-Type: application/json`

**Request Body**:

```json
{
  "name": "your-db-server-name",
  "url": "postgresql://postgres:<your-password>@<your-host>:<your-port>/postgres",
  "api_server_name": "prod-us-east-1"
}
```

**Parameters**:

- `name` (required): A unique identifier for your database server. This is an internal name used to reference the server in other API calls.
- `url` (required): The PostgreSQL connection string (must use postgres user and postgres database)
- `api_server_name` (required): The Lamin region identifier (e.g., "prod-us-east-1")

**Response**: Status 201 with success message

### Test Database Server Connection

**Endpoint**: `POST /db/server/checks-access`

**Headers**:

- `Authorization: Bearer ACCESS_TOKEN`

**Query Parameters**:

- `name` (required): The name of the database server to test (the internal reference name you provided during registration)

**Response**: Status indicator and message

## Example

### Authentication

The examples in this example use `settings.user.access_token` from `lamindb_setup` for authentication. This approach automatically uses the token obtained from running `lamin login` in your CLI.

### Python Example

Here's a simple Python script that demonstrates how to register a database server and verify the connection:

```python
import requests
from lamindb_setup import settings

LAMIN_API_URL = "https://api.lamin.ai"
ACCESS_TOKEN = settings.user.access_token
DB_SERVER_NAME = "my-postgres-server"  # A name used to reference your database server in Lamin

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# 1. Register the database server
register_response = requests.post(
    f"{LAMIN_API_URL}/db/server/register",
    json={
        "name": DB_SERVER_NAME,
        "url": "postgresql://postgres:<your-password>@<your-host>:<your-port>/postgres",
        "api_server_name": "prod-us-east-1"
    },
    headers=headers
)
print(f"Registration result: {register_response.json()}")

# 2. Test the connection
test_response = requests.post(
    f"{LAMIN_API_URL}/db/server/checks-access?name={DB_SERVER_NAME}",
    headers=headers
)
print(f"Connection test result: {test_response.json()}")
```

## Related Resources

- [Configuring On-Premises Data Infrastructure](configure-on-prem-data-infra.md)
- [Service Endpoints and IP Whitelisting](service-endpoints.md)

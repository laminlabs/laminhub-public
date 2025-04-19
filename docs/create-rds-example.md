# Creating an Amazon RDS Instance with Pulumi

This guide demonstrates how to create a PostgreSQL RDS instance in AWS using Pulumi that can be accessed by Lamin applications.

## Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/install/) installed
- AWS credentials configured

## Implementation

The following Pulumi program creates an RDS PostgreSQL instance with proper networking and security configurations:

```python
import pulumi
import pulumi_aws as aws

# Create a new VPC
vpc = aws.ec2.Vpc("create-rds-example-test-db", cidr_block="10.0.0.0/16", enable_dns_hostnames=True)

# Create public subnets in two different AZs
subnet1 = aws.ec2.Subnet(
    "create-rds-example-subnet1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-east-1a",
    map_public_ip_on_launch=False
)

subnet2 = aws.ec2.Subnet(
    "create-rds-example-subnet2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-east-1b",
    map_public_ip_on_launch=False
)

# Create an internet gateway
igw = aws.ec2.InternetGateway("igw", vpc_id=vpc.id)

# Create a route table
route_table = aws.ec2.RouteTable(
    "create-rds-example-route-table",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ]
)

# Associate the route table with the subnets
aws.ec2.RouteTableAssociation(
    "create-rds-example-subnet1-rt-association",
    subnet_id=subnet1.id,
    route_table_id=route_table.id
)

aws.ec2.RouteTableAssociation(
    "create-rds-example-subnet2-rt-association",
    subnet_id=subnet2.id,
    route_table_id=route_table.id
)

# Create a security group to allow inbound traffic on port 5432
security_group = aws.ec2.SecurityGroup(
    "create-rds-example-security-group",
    vpc_id=vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=5432,
            to_port=5432,
            cidr_blocks=[
                # Allow traffic from within the VPC
                "10.0.0.0/16",
                # Allow traffic for our us-east-1 staging API
                "100.28.143.249/32",
                "44.195.110.253/32"
            ],
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
)

# Create a PostgreSQL RDS instance
subnet_group = aws.rds.SubnetGroup(
    "create-rds-example-db-subnet-group",
    subnet_ids=[subnet1.id, subnet2.id],
)

db = aws.rds.Instance(
    "create-rds-example-db",
    engine="postgres",
    instance_class="db.t3.micro",
    allocated_storage=20,
    # Lamin requires a default database named 'postgres'
    db_name="postgres",
    # Lamin requires the default postgres superuser for database access
    username="postgres",
    password="mypassword",
    vpc_security_group_ids=[security_group.id],
    db_subnet_group_name=subnet_group.name,
    publicly_accessible=True,
    skip_final_snapshot=False
)

# Export the RDS endpoint
pulumi.export("endpoint", db.endpoint)
```

## Further Reading

- [Pulumi AWS Documentation](https://www.pulumi.com/registry/packages/aws/)
- [Amazon RDS Documentation](https://aws.amazon.com/rds/)

# S3 Bucket Policy for Lamin Manager Access

This document provides the necessary AWS IAM policy to attach to your S3 bucket to grant the `lamin-manager` IAM user the required permissions to access the bucket.

## Policy JSON

Attach the following policy to your S3 bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::767398070972:user/lamin-manager"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::<your-bucket-name>/*",
        "arn:aws:s3:::<your-bucket-name>"
      ]
    }
  ]
}
```

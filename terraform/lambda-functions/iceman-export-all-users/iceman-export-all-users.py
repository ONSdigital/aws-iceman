import os
import boto3
import csv
import io
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Initialize clients
    s3_client = boto3.client('s3')
    identity_store_client = boto3.client('identitystore')

    # Specify the S3 bucket and file name
    bucket_name = os.environ['BUCKET_NAME']
    file_name = 'identity_center_users.csv'

    try:
        # Get the users from IAM Identity Center
        users = get_identity_center_users(identity_store_client)

        # Convert users data to CSV
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerow(['UserID', 'UserName', 'Email'])  # Header row

        for user in users:
            csv_writer.writerow([user['UserId'], user['UserName'], user.get('Email', 'N/A')])

        # Upload CSV to S3
        s3_client.put_object(Body=csv_buffer.getvalue(), Bucket=bucket_name, Key=file_name)

        return {
            'statusCode': 200,
            'body': f'Users exported to {bucket_name}/{file_name}'
        }

    except ClientError as e:
        # Log and raise the AWS client error
        print(f"An error occurred: {e}")
        raise e
    except Exception as e:
        # Handle other exceptions
        print(f"An unexpected error occurred: {e}")
        raise e

def get_identity_center_users(identity_store_client):
    users = []
    try:
        # Initialize pagination
        paginator = identity_store_client.get_paginator('list_users')
        page_iterator = paginator.paginate(
            IdentityStoreId=os.environ['IDENTITYSTORE_ID']
        )

        # Iterate through each page and append users
        for page in page_iterator:
            for user in page['Users']:
                users.append(user)

    except ClientError as e:
        # Log and raise the AWS client error
        print(f"Error retrieving users: {e}")
        raise e

    return users

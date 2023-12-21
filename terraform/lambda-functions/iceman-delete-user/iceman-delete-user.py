import os
import boto3
import logging
import urllib.request
import json

client = boto3.client('identitystore')

def send_to_slack(title, details):
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    slack_message = {
        "attachments": [
            {
                "fallback": title,
                "color": "#36a64f" if "Deleted" in title else "#ff0000",
                "title": title,
                "fields": [{"value": details, "short": False}],
                "footer": "AWS Lambda Notification",
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png"
            }
        ]
    }

    data = json.dumps(slack_message).encode()
    req = urllib.request.Request(webhook_url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            raise ValueError(f"Request to Slack returned an error {response.status}, the response is:\n{response.read().decode()}")

def get_user_id(username):
    response = client.list_users(
        IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
        Filters=[
            {
                'AttributePath': 'UserName',
                'AttributeValue': username
            }
        ]
    )

    users = response['Users']
    if len(users) > 0:
        return users[0]['UserId']
    else:
        return None

def lambda_handler(event, context):
    try:
        username = event['username']
        user_id = get_user_id(username)

        if user_id:
            delete_user_response = client.delete_user(
                IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
                UserId=user_id,
            )
            title = "User Deletion Successful"
            details = f"User `{username}` deleted."
            send_to_slack(title, details)
        else:
            title = "User Not Found"
            details = f"No user found for `{username}`."
            send_to_slack(title, details)

    except Exception as e:
        title = "Delete User Lambda Function Error"
        details = f"An error occurred in the Lambda function: `{str(e)}`"
        send_to_slack(title, details)
        raise e
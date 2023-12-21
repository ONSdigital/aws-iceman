import os
import boto3
import urllib.request
import json

client = boto3.client('identitystore')

def send_to_slack(title, details):
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    slack_message = {
        "attachments": [
            {
                "fallback": title,
                "color": "#36a64f" if "Successful" in title else "#ff0000",
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


def get_group_id(group_name):
    response = client.get_group_id(
        IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
        AlternateIdentifier={'UniqueAttribute': {'AttributePath': 'displayName', 'AttributeValue': group_name}}
    )
    return response['GroupId']


def get_user_id(user_name):
    response = client.get_user_id(
        IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
        AlternateIdentifier={'UniqueAttribute': {'AttributePath': 'userName', 'AttributeValue': user_name}}
    )
    return response['UserId']


def lambda_handler(event, context):
    try:
        if 'group' not in event or 'user' not in event:
            message = "Group and User names are required in event"
            print(message)
            send_to_slack("Event Data Missing", message)
            return

        group_name = event['group']
        user_name = event['user']
        group_id = get_group_id(group_name)
        user_id = get_user_id(user_name)

        response = client.create_group_membership(
            GroupId=group_id,
            IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
            MemberId={'UserId': user_id}
        )

        message = f"User: {user_name} added to Group: {group_name} successfully"
        print(message)
        send_to_slack("AWS Lambda Notification", message)

    except Exception as e:
        error_message = f"Error in Lambda function: {str(e)}"
        send_to_slack("Lambda Function Error", error_message)
        raise

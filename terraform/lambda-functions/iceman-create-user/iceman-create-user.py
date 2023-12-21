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

def lambda_handler(event, context):
    try:
        user_name = event['username']
        given_name = event['givenname']
        family_name = event['familyname']

        # Create user
        display_name = "{} {}".format(given_name, family_name)
        create_user_response = client.create_user(
            IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
            UserName=user_name,
            Name={"FamilyName": family_name, "GivenName": given_name},
            DisplayName=display_name,
            Emails=[{"Value": user_name, "Primary": True}]
        )

        # Send Slack notification of successful user creation
        title = "User Creation Successful"
        details = f"User `{user_name}` with UserId has been created successfully."
        send_to_slack(title, details)

        return {"status": "Success"}

    except Exception as e:
        title = "Create User Lambda Function Error"
        details = f"An error occurred in the Lambda function: `{str(e)}`"
        send_to_slack(title, details)

        raise e

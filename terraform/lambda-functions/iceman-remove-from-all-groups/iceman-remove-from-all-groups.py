import os
import boto3
import logging
import urllib.request
import json


logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('identitystore')
def send_to_slack(title, details):
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    slack_message = {
        "attachments": [
            {
                "fallback": title,
                "color": "#36a64f" if "Success" in title else "#ff0000",  # Green for success, Red for errors
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
    try:
        response = client.list_users(
            IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
            Filters=[
                {'AttributePath': 'UserName', 'AttributeValue': username}
            ]
        )
        if response['Users']:
            return response['Users'][0]['UserId']
        else:
            logger.info(f"User with email {username} not found.")
            return None
    except Exception as e:
        logger.error(f"Error retrieving user ID for email {username}: {e}")
        raise

def get_membership_ids(user_id):
    membership_ids = []
    group_paginator = client.get_paginator('list_groups')

    try:
        for group_page in group_paginator.paginate(IdentityStoreId=os.environ['IDENTITYSTORE_ID']):
            for group in group_page['Groups']:
                membership_paginator = client.get_paginator('list_group_memberships')
                for membership_page in membership_paginator.paginate(
                        IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
                        GroupId=group['GroupId']):
                    for membership in membership_page['GroupMemberships']:
                        if 'UserId' in membership['MemberId'] and membership['MemberId']['UserId'] == user_id:
                            membership_ids.append(membership['MembershipId'])
    except Exception as e:
        logger.error(f"Error retrieving membership IDs for user ID {user_id}: {e}")
        raise

    return membership_ids

def remove_user_from_groups(membership_ids):
    for membership_id in membership_ids:
        try:
            client.delete_group_membership(
                IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
                MembershipId=membership_id
            )
            logger.info(f"Removed membership ID {membership_id}")
        except Exception as e:
            logger.error(f"Error removing membership ID {membership_id}: {e}")
            # If one fails, we should continue to attempt to delete the rest
            continue

def lambda_handler(event, context):
    try:
        username = event.get('username')
        if not username:
            raise ValueError("Username is required")

        user_id = get_user_id(username)
        if not user_id:
            title = "User Not Found"
            details = f"User with email '{username}' not found."
            send_to_slack(title, details)
            raise ValueError(f"User with email '{username}' not found")

        membership_ids = get_membership_ids(user_id)
        remove_user_from_groups(membership_ids)

        title = "User Removal Successful"
        details = f"Removed user with email '{username}' from all groups."
        send_to_slack(title, details)

        return {
            'message': details
        }

    except Exception as e:
        title = "Lambda Function Error"
        details = f"An error occurred in the Lambda function: {str(e)}"
        send_to_slack(title, details)
        raise

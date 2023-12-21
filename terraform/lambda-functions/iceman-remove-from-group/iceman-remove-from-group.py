import os
import boto3
import logging
import urllib.request
import json

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the boto3 client for AWS Identity Store
client = boto3.client('identitystore')

def send_to_slack(title, details):
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    slack_message = {
        "attachments": [
            {
                "fallback": title,
                "color": "#36a64f" if "Success" in title else "#ff0000",  # Green for success, Red for error
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
    response = client.list_groups(
        IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
        Filters=[
            {
                'AttributePath': 'DisplayName',
                'AttributeValue': group_name
            }
        ]
    )
    groups = response['Groups']
    if groups:
        return groups[0]['GroupId']
    else:
        logger.info("Group not found.")
        return None

def get_user_id(user_name):
    response = client.list_users(
        IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
        Filters=[
            {
                'AttributePath': 'UserName',
                'AttributeValue': user_name
            }
        ]
    )
    users = response['Users']
    if users:
        return users[0]['UserId']
    else:
        logger.info("User not found.")
        return None

def get_group_membership_id(group_id, user_id):
    try:
        response = client.get_group_membership_id(
            IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
            GroupId=group_id,
            MemberId={'UserId': user_id}
        )
        return response['MembershipId']
    except client.exceptions.ResourceNotFoundException:
        print("Membership not found.")
        return None
    except Exception as e:
        print(f"An error occurred while getting the group membership ID: {e}")
        return None

def delete_user_from_group(membership_id):
    try:
        response = client.delete_group_membership(
            IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
            MembershipId=membership_id
        )
        return response
    except Exception as e:
        print(f"An error occurred while deleting the group membership: {e}")

def lambda_handler(event, context):
    group_name = event.get('group_name')
    user_name = event.get('user_name')

    if not group_name or not user_name:
        send_to_slack("Missing Information", "Both 'group_name' and 'user_name' are required in the event.")
        return "Both 'group_name' and 'user_name' are required in the event."

    group_id = get_group_id(group_name)
    if group_id is None:
        send_to_slack("Group Not Found", f"Group '{group_name}' not found.")
        return "Group not found."

    user_id = get_user_id(user_name)
    if user_id is None:
        send_to_slack("User Not Found", f"User '{user_name}' not found.")
        return "User not found."

    membership_id = get_group_membership_id(group_id, user_id)
    if membership_id is None:
        send_to_slack("Membership Error", "No membership found or error occurred.")
        return "No membership found or error occurred."

    deletion_response = delete_user_from_group(membership_id)
    if deletion_response:
        message = f"User {user_name} was successfully removed from group {group_name}."
        logger.info(message)
        send_to_slack("User Removed Successfully", message)
        return "User removed successfully."
    else:
        send_to_slack("Deletion Error", "Error occurred during deletion.")
        return "Error occurred during deletion."

import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('identitystore')

def get_group_id(group_name):
    try:
        response = client.list_groups(
            IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
            Filters=[
                {'AttributePath': 'DisplayName', 'AttributeValue': group_name}
            ]
        )
        if response['Groups']:
            return response['Groups'][0]['GroupId']
        else:
            logger.info(f"Group with name {group_name} not found.")
            return None
    except Exception as e:
        logger.error(f"Error retrieving group ID for group name {group_name}: {e}")
        raise
def get_user_details(user_id):
    try:
        user_info = client.describe_user(
            IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
            UserId=user_id
        )
        return {
            'user_name': user_info.get('UserName'),
            'email': user_info.get('Email')
        }
    except Exception as e:
        logger.error(f"Error retrieving details for user ID {user_id}: {e}")
        return None

def get_group_members(group_id):
    group_members = []
    membership_paginator = client.get_paginator('list_group_memberships')

    try:
        for membership_page in membership_paginator.paginate(
                IdentityStoreId=os.environ['IDENTITYSTORE_ID'],
                GroupId=group_id):
            for membership in membership_page['GroupMemberships']:
                user_id = membership['MemberId']['UserId']
                user_details = get_user_details(user_id)
                if user_details:
                    group_members.append(user_details)
    except Exception as e:
        logger.error(f"Error retrieving members for group ID {group_id}: {e}")
        raise

    return group_members

def lambda_handler(event, context):
    group_name = event.get('group_name')
    if not group_name:
        raise ValueError("Group name is required")

    group_id = get_group_id(group_name)
    if not group_id:
        raise ValueError(f"Group with name '{group_name}' not found")

    group_members = get_group_members(group_id)

    return {
        'statusCode': 200,
        'body': {
            'message': f"Members of group '{group_name}':",
            'members': group_members
        }
    }

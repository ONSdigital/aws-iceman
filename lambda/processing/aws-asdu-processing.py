import os
import json
import boto3
from pprint import pprint   # fancy print
import csv

### variables
## Add appropriate values below
dryRun = True       # True / False; 
store_id = os.getenv('store_id')
sso_instance_arn = os.getenv('sso_instance_arn')
region="eu-west-2" 

### functions
def get_user_id_by_username(store_id, username):
    client = boto3.client('identitystore')
    paginator = client.get_paginator('list_users')
    
    for page in paginator.paginate(IdentityStoreId=store_id):
        for user in page['Users']:
            if user['UserName'] == username:
                return user['UserId']

    return None

def get_group_by_group_id(store_id, group_id):
    client = boto3.client('identitystore')
    paginator = client.get_paginator('list_groups')
    
    for page in paginator.paginate(IdentityStoreId=store_id):
        for group in page['Groups']:
            if group['GroupId'] == group_id:
                group_name = group['DisplayName']
                return group_name

    return None

def remove_user_from_all_groups(store_id, user_id, username, dryRun):
    client = boto3.client('identitystore')

    # List all group memberships for the user
    user_groups = client.list_group_memberships_for_member(
        IdentityStoreId=store_id, MemberId={'UserId': user_id}
    )['GroupMemberships']

    for group in user_groups:
        group_id = group['GroupId']
        membership_id = group['MembershipId']
        group_name = get_group_by_group_id(store_id, group_id)
        dry = 'NOT '

        if not dryRun:
            # remove inactive users from group assignments
            client.delete_group_membership(
                IdentityStoreId=store_id,
                MembershipId=membership_id
            )
            dry = ''

        print(f"{dry}Removing user {username} from '{group_name}' group ({group_id})")

### main
if dryRun:
    print(" --- Dry run enabled ---")

# read and process list of users from csv file
with open('output.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0      
    next(csv_reader)      # skip the header

    for row in csv_reader:
        username = row[1]
        status = row[4]
        user_id = get_user_id_by_username(store_id, username)

        if status == 'Inactive':
            remove_user_from_all_groups(store_id, user_id, username, dryRun)

        # print(f'{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}') 
        line_count += 1

print(f'\nProcessed {line_count} users.')
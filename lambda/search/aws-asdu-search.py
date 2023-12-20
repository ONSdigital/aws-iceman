import os
import datetime
import json
import boto3
from pprint import pprint   # fancy print
import csv
import pytz

### variables
# CloudTrail search setup
delta = 60  # how far back we search, in days
csv_header = ['LogDate','UserName','UserID','DaysUntilAction','Status']

## Add appropriate values below
store_id = os.getenv('store_id')
bucket = os.getenv('bucket_name')
exclusion_group_ids = os.getenv('exclusion_group_ids')

### functions
end_time = datetime.datetime.now(pytz.UTC)
start_time = end_time - datetime.timedelta(days=delta)

def find_value_in_dict(data_dict, value_to_find, key_to_search=None):
    def search_nested(item, value_to_find, key_to_search=None):
        if isinstance(item, dict):
            for k, v in item.items():
                if key_to_search is None or k == key_to_search:
                    if search_nested(v, value_to_find, key_to_search):
                        return True
        elif isinstance(item, list):
            for i in item:
                if search_nested(i, value_to_find, key_to_search):
                    return True
        else:
            return item == value_to_find

        return False

    return search_nested(data_dict, value_to_find, key_to_search)

def search_log(log, username):
    for email, data in log.items():
        if email == username:
            event_data = json.loads(data['CloudTrailEvent'])
            return event_data['eventTime']
    return 'n/a'

def writeToCSV(csv_data):
    with open('output.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(csv_header)
        writer.writerows(csv_data)
    # print(csv_data)

def writeToS3(csv_data, bucket):    
    client = boto3.client('s3')

    client.put_object(
        Body=csv_data, 
        Bucket = bucket, 
        Key = bucket+"/out.csv"
    )

def list_all_users(store_id):
    client = boto3.client('identitystore')
    response = client.list_users(IdentityStoreId=store_id)
    users = response["Users"]
    while "NextToken" in response:
        response = client.list_users(IdentityStoreId=store_id, NextToken=response["NextToken"])
        users += response["Users"]
    return users

def list_all_cloudtrail_events(start_time, end_time):
    cloudtrail = boto3.client('cloudtrail')
    paginator = cloudtrail.get_paginator('lookup_events')
    paginator_config = {
        'StartTime': start_time,
        'EndTime': end_time,
        'LookupAttributes': [
            {
                'AttributeKey': 'EventName',
                'AttributeValue': 'Authenticate'
            }
        ],
        'PaginationConfig': {
            'MaxItems': 99999, 
        }
    }
    # Process events and find the latest event for each user
    latest_events = {}
    for page in paginator.paginate(**paginator_config):
        for event in page['Events']:
            event_time = event['EventTime']
            event_data = json.loads(event['CloudTrailEvent'])
            user_name = event_data['userIdentity']['userName']

            if user_name not in latest_events or event_time > latest_events[user_name]['EventTime']:
                latest_events[user_name] = event

    return latest_events

def list_group_memberships(store_id, exclusion_group_ids):
    client = boto3.client('identitystore')
    users_excluded = []

    for group_id in exclusion_group_ids:
        exclusion_response = client.list_group_memberships(
            IdentityStoreId=store_id,
            GroupId=group_id,
        )
        json_list = json.loads(json.dumps(exclusion_response))
        users_excluded.extend(json_list['GroupMemberships'])

    return users_excluded


### main loop
users_excluded = list_group_memberships(store_id, exclusion_group_ids)
users = list_all_users(store_id)
latest_events = list_all_cloudtrail_events(start_time, end_time)

csv_data = []
n_users_found = 0
n_users_excluded = 0
n_users_inactive = 0
n_users_active = 0

for user in users:
    n_users_found += 1
    ## see if the user is in the exclusion group
    value_to_find = user['UserId']
    found = find_value_in_dict(users_excluded, value_to_find)

    newLine = None
    if not found:   
        # user NOT found in the exclusion group, so proceed
        latest_event = find_value_in_dict(latest_events, user['UserName'])

        if latest_event:
            # user login was found within the timeframe, so it's active > ignore
            n_users_active += 1
            last_login = search_log(latest_events, user['UserName'])
            newLine = [last_login, user['UserName'], user['UserId'], 'n/a', 'Active']
            csv_data.append(newLine)
            print(newLine)

        else:
            # user login was NOT found within the defined timeframe >  to be disabled
            n_users_inactive += 1
            last_login = search_log(latest_events, user['UserName'])
            newLine = [last_login, user['UserName'], user['UserId'], '0', 'Inactive']
            csv_data.append(newLine)
            print(newLine)

    else: 
        # user was found in the exclusion list > ignore
        n_users_excluded += 1
        last_login = search_log(latest_events, user['UserName'])
        newLine = [last_login, user['UserName'], user['UserId'], 'n/a', 'Excluded']
        csv_data.append(newLine)
        print(newLine)
        
# writeToCSV(csv_data)
# writeToS3(csv_data)

# print some stats
print(f"\nSSO users:      {n_users_found}")
print(f"Excluded users: {n_users_excluded}")
print(f"Active users:   {n_users_active}")
print(f"To be disabled: {n_users_inactive}")

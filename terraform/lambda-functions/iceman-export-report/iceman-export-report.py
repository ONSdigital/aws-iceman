import boto3, csv, io, datetime

s3 = boto3.client('s3')
idstoreclient = boto3.client('identitystore')
ssoadminclient = boto3.client('sso-admin')
orgsclient= boto3.client('organizations')

bucket_name = 'iceman-identitystorereports'
users={}
groups={}
permissionSets={}
Accounts={}

Instances= (ssoadminclient.list_instances()).get('Instances')
InstanceARN=Instances[0].get('InstanceArn')
IdentityStoreId=Instances[0].get('IdentityStoreId')


#Dictionary mapping User IDs to usernames
def mapUserIDs():
    ListUsers=idstoreclient.list_users(IdentityStoreId=IdentityStoreId)
    ListOfUsers=ListUsers['Users']
    while 'NextToken' in ListUsers.keys():
        ListUsers=idstoreclient.list_users(IdentityStoreId=IdentityStoreId,NextToken=ListUsers['NextToken'])
        ListOfUsers.extend(ListUsers['Users'])
    for eachUser in ListOfUsers:
        users.update({eachUser.get('UserId'):eachUser.get('UserName')})
mapUserIDs()

#Dictionary mapping Group IDs to display names
def mapGroupIDs():
    ListGroups=idstoreclient.list_groups(IdentityStoreId=IdentityStoreId)
    ListOfGroups=ListGroups['Groups']
    while 'NextToken' in ListGroups.keys():
        ListGroups=idstoreclient.list_groups(IdentityStoreId=IdentityStoreId,NextToken=ListGroups['NextToken'])
        ListOfGroups.extend(ListGroups['Groups'])
    for eachGroup in ListOfGroups:
        groups.update({eachGroup.get('GroupId'):eachGroup.get('DisplayName')})
mapGroupIDs()

#Dictionary mapping permission set ARNs to permission set names
def mapPermissionSetIDs():
    ListPermissionSets=ssoadminclient.list_permission_sets(InstanceArn=InstanceARN)
    ListOfPermissionSets=ListPermissionSets['PermissionSets']
    while 'NextToken' in ListPermissionSets.keys():
        ListPermissionSets=ssoadminclient.list_permission_sets(InstanceArn=InstanceARN,NextToken=ListPermissionSets['NextToken'])
        ListOfPermissionSets.extend(ListPermissionSets['PermissionSets'])
    for eachPermissionSet in ListOfPermissionSets:
        permissionSetDescription=ssoadminclient.describe_permission_set(InstanceArn=InstanceARN,PermissionSetArn=eachPermissionSet)
        permissionSetDetails=permissionSetDescription.get('PermissionSet')
        permissionSets.update({permissionSetDetails.get('PermissionSetArn'):permissionSetDetails.get('Name')})
mapPermissionSetIDs()

#Listing Permissionsets provisioned to an account
def GetPermissionSetsProvisionedToAccount(AccountID):
    PermissionSetsProvisionedToAccount=ssoadminclient.list_permission_sets_provisioned_to_account(InstanceArn=InstanceARN,AccountId=AccountID)
    ListOfPermissionSetsProvisionedToAccount = PermissionSetsProvisionedToAccount['PermissionSets']
    while 'NextToken' in PermissionSetsProvisionedToAccount.keys():
        PermissionSetsProvisionedToAccount=ssoadminclient.list_permission_sets_provisioned_to_account(InstanceArn=InstanceARN,AccountId=AccountID,NextToken=PermissionSetsProvisionedToAccount['NextToken'])
        ListOfPermissionSetsProvisionedToAccount.extend(PermissionSetsProvisionedToAccount['PermissionSets'])
    return(ListOfPermissionSetsProvisionedToAccount)

#To retrieve the assignment of each permissionset/user/group/account assignment
def ListAccountAssignments(AccountID):
    PermissionSetsList=GetPermissionSetsProvisionedToAccount(AccountID)
    Assignments=[]
    for permissionSet in PermissionSetsList:
        AccountAssignments=ssoadminclient.list_account_assignments(InstanceArn=InstanceARN,AccountId=AccountID,PermissionSetArn=permissionSet)
        Assignments.extend(AccountAssignments['AccountAssignments'])
        while 'NextToken' in AccountAssignments.keys():
            AccountAssignments=ssoadminclient.list_account_assignments(InstanceArn=InstanceARN,AccountId=AccountID,PermissionSetArn=permissionSet,NextToken=AccountAssignments['NextToken'])
            Assignments.extend(AccountAssignments['AccountAssignments'])
    return(Assignments)


#To list all the accounts in the organization
def ListAccountsInOrganization():
    AccountsList=orgsclient.list_accounts()
    ListOfAccounts=AccountsList['Accounts']
    while 'NextToken' in AccountsList.keys():
        AccountsList=orgsclient.list_accounts(NextToken=AccountsList['NextToken'])
        ListOfAccounts.extend(AccountsList['Accounts'])
    for eachAccount in ListOfAccounts:
        Accounts.update({eachAccount.get('Id'):eachAccount.get('Name')})
    return(Accounts)

def lambda_handler(event, context):
    Accounts=ListAccountsInOrganization()
    ListOfAccountIDs=list(Accounts.keys())
    entries=[]
    for eachAccountID in ListOfAccountIDs:
        try:
            GetAccountAssignments=ListAccountAssignments(eachAccountID)
            for eachAssignment in GetAccountAssignments:
                entry=[]
                entry.append(eachAssignment.get('AccountId'))
                entry.append(Accounts.get(eachAssignment.get('AccountId')))
                entry.append(permissionSets.get(eachAssignment.get('PermissionSetArn')))
                entry.append(eachAssignment.get('PrincipalType'))
                if(eachAssignment.get('PrincipalType')=='GROUP'):
                    entry.append(groups.get(eachAssignment.get('PrincipalId')))
                else:
                    entry.append(users.get(eachAssignment.get('PrincipalId')))
                entries.append(entry)
        except:
            continue

    headers=['Account ID', 'Account Name', 'Permission Set','Principal Type', 'Principal']

    csv_buffer = io.StringIO()
    csvwriter = csv.writer(csv_buffer)
    csvwriter.writerow(headers)
    csvwriter.writerows(entries)

    # Format the current date as YYYYMMDD
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M')

    # Define the filename with the timestamp
    filename = f'IdentityCenterReport{timestamp}.csv'

    # Reset buffer position
    csv_buffer.seek(0)

    # Upload to S3
    s3.put_object(Body=csv_buffer.getvalue(), Bucket=bucket_name, Key=filename)
    print(f"Done! {filename} report is generated successfully and uploaded to {bucket_name}!")
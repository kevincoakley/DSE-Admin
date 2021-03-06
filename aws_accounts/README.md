AWS_ACCOUNTS
============

## Steps Create AWS Org and IAM Accounts

1. Login to master AWS Account
2. Go to Organizations
3. Add a new Account to the Organization
4. Select Create Account
    1. Name: Cohort# Group#
    2. Email: username+cohort#group#@eng.ucsd.edu
    3. IAM Role: OrganizationAccountAccessRole
4. Wait for AWS account creation email to be sent. Once the account has been created, sign into the new account using root credentials (use the email that was used in account creation). Reset the Master Password if necessary
5. Create an Admin IAM user with the usename dse-admin and a group with the name "administrators" with full admin access (add policy named "AdministratorAccess")
    1. Give user both programmatic and console access
6. Change the IAM users sign-in link to cohort#group#
7. Create IAM Groups by running create_groups.py . The following groups are created:
    1. Billing: group_policies/billing.json
    2. EC2: group_policies/ec2/spark_notebook.json
    3. EC2_treasurer: group_policies/ec2/spark_notebook_treasurer.json
    4. EMR: group_policies/emr/emr.json
    5. EMR_treasurer: group_policies/emr/emr_iam_role.json
    6. IAM: group_policies/iam.json
    7. S3: group_policies/s3/spark_notebook_s3.json (NOTE: EMR logs bucket and group bucket need to be updated for each AWS Account. create_groups.py does this for you automatically)
8. Create IAM Users by running create_users.py . Configure the script like the following:
    1. Add the treasurer to all of the IAM groups
    2. Add the regular users to all of the IAM groups minus the *_treasurer groups
9. Add EMR Roles
    1. Install awscli: `$ pip install awscli`
    2. Configure the credentials awscli for the AWS Account: `$ aws configure` . Set defualt region as 'us-east-1'
    3. Add the EMR Roles: `$ aws emr create-default-roles`
10. Add S3 Buckets:
    1. EMR Logs: s3://aws-logs-XXXXXXXXXXXX-us-east-1 (Replace XXXXXXXXXXXX with AWS account id)
    2. Group Bucket: s3://dse-cohort#-group# (replace # with cohort number and group number)
11. Add Cloud Trail
    1. Trail name: cloudtrail-XXXXXXXXXXXX (Replace XXXXXXXXXXXX with AWS account id)
    2. Apply to all regions: Yes
    3. Read/Write events: All
    4. Select all S3 buckets in your account
    5. Create new S3 bucket: Yes
    6. S3 bucket: cloudtrail-XXXXXXXXXXXX (Replace XXXXXXXXXXXX with AWS account id)
    

## Adding Users and Groups

1. Creating groups: `create_groups.py -k ACCESSS_KEY -s SECRET_ACCESS_KEY -o OUTPUT_DIRECTORY -c COHORT_NUM -g GROUP_NUM -a AWS_ACCOUNT_ID`
    NOTE: create_group.py is run by create_groups.py, so it will not need to be run manually. However, it can be run with the following syntax: 
    Example: Add IAM - `$ create_group.py -k XXX -s XXX -n GROUP_NAME -p group_policies/policy.json -o ~/save/`
2. Create the users CSV file, see below and example_users.csv for an example CSV file.
3. Add users from CSV file: `$ create_users.py -k XXX -s XXX -c ~/Desktop/dse_users.csv -u https://cohort#group#.signin.aws.amazon.com/console -o ~/save/`
4. Use share_credentials to distribute *username_aws_console_password.txt* & *username_aws_credentials.csv*.


## create_group.py - Add IAM Groups
Due to the character limits on IAM group inline policies, I recommend creating a new group for each policy. 

Included policies:

* **group_policies/ec2.json**: DeleteVolume, DetachVolume, RebootInstances, StopInstances, TerminateInstances access for instances that have an owner tag that is equal to ${aws:username}. Full access to everything else.
* **group_policies/emr.json**: Access to list clusters and submit new job flows.
* **group_policies/s3.json**: Full access to the bucket named dse-${aws:username}. List access to everything else.

*${aws:username}* equals the IAM username.

Example usage: `$ create_group.py  -k XXX -s XXX -n 2014_students_EC2 -p group_policies/ec2.json -o ~/save/"`


## create_users.py - Create IAM Users

Adds IAM users from a CSV file. The CSV file format is username in the first column then group names in the additional columns. One user per row.

Example CSV file:

```
user1,group1,group2,group3
user2,group1,group2,group3
user3,group1,group2,group3
user4,group1,group2,group3
user5,group1,
user6
```

The user credentials are saved in two files:

* **username_aws_console_password.txt**: Contains the user's AWS console username and password.
* **username_aws_credentials.csv**: Contains the user's AWS Access Key Id and Secret Access Key. 

Example usage: `$ create_users.py  -k XXX -s XXX -c csv_file  -o ~/save/`


## del_users.py - Delete IAM Users

Removes users from IAM that don't exist in the CSV file but do exist in an IAM group.

Example CSV file what would delete user4:

```
user1,group1,group2,group3
user2,group1,group2,group3
user3,group1,group2,group3
user5,group1,
user6
```

Example usage:  `$ del_users.py  -k XXX -s XXX -c csv_file -g 2014_students_EC2 -o ~/save/`

AWS_ACCOUNTS
============

## Steps Create AWS Org and IAM Accounts

1. Login to master AWS Account
2. Go to Organizations
3. Create a new Organization
    1. Name: Cohort# Group#
    2. Email: username+cohort#group#@eng.ucsd.edu
    3. IAM Role: OrganizationAccountAccessRole
4. Wait for AWS account creation email to be sent, reset the Master Password if necessary
5. Create an Admin IAM user and group with full admin access
6. Create IAM Groups
    1. Billing: group_policies/billing.json
    2. EC2: group_policies/ec2/spark_notebook.json
    3. EC2_treasurer: group_policies/ec2/spark_notebook_treasurer.json
    4. EMR: group_policies/emr/emr.json
    5. EMR_treasurer: group_policies/emr/emr_iam_role.json
    6. IAM: group_policies/iam.json
    7. S3: group_policies/s3/spark_notebook_s3.json (NOTE: EMR logs bucket and group bucket need to be updated for each AWS Account.)
7. Create IAM Users
    1. Add the treasurer to all of the IAM groups
    2. Add the regular users to all of the IAM groups minus the *_treasurer groups
8. Add EMR Roles
    1. Install awscli: `$ pip install awscli`
    2. Configure the credentials awscli for the AWS Account: `$ aws configure`
    3. Add the EMR Roles: `$ aws emr create-default-roles`
9. Add S3 Buckets:
    1. EMR Logs: s3://aws-logs-123456789012-us-east-1 (Replace 123456789012)
    2. Group Bucket: s3://dse-cohort#-group#
10. Add Cloud Trail
    1. Trail name: cloudtrail-123456789012 (Replace 123456789012)
    2. Apply to all regions: Yes
    3. Read/Write events: All
    4. Select all S3 buckets in your account
    5. Create new S3 bucket: Yes
    6. S3 bucket: cloudtrail-123456789012 (Replace 123456789012)
    

## Adding Users and Groups

1. Add Groups. 
    1. Add IAM: `$ add_group.py -k XXX -s XXX -n GROUP_NAME -p group_policies/policy.json -o ~/save/"`
2. Create the users CSV file, see below and example_users.csv for an example CSV file.
3. Add users from CSV file: `$ add_users.py -k XXX -s XXX -c ~/Desktop/dse_users.csv -o ~/save/`
4. Use share_credentials to distribute *username_aws_console_password.txt* & *username_aws_credentials.csv*.


## add_group.py - Add IAM Groups
Due to the character limits on IAM group inline policies, I recommend creating a new group for each policy. 

Included policies:

* **group_policies/ec2.json**: DeleteVolume, DetachVolume, RebootInstances, StopInstances, TerminateInstances access for instances that have an owner tag that is equal to ${aws:username}. Full access to everything else.
* **group_policies/emr.json**: Access to list clusters and submit new job flows.
* **group_policies/s3.json**: Full access to the bucket named dse-${aws:username}. List access to everything else.

*${aws:username}* equals the IAM username.

Example usage: `$ add_group.py  -k XXX -s XXX -n 2014_students_EC2 -p group_policies/ec2.json -o ~/save/"`


## add_users.py - Add IAM Users

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

Example usage: `$ add_users.py  -k XXX -s XXX -c csv_file  -o ~/save/`


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

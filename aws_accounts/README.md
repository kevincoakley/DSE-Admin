# Adding Users and Groups

1. Install https://github.com/mas-dse/UCSD_BigData_Scripts: `pip install git+https://github.com/mas-dse/UCSD_BigData_Scripts.git`
2. Setup admin credentials: `ucsd-bigdata-setup.py -o admin`
3. Add Groups. I recommend creating groups with names based on the year or course in order to make account clean up easier.
    1. Add IAM group for EC2: `accounts/add_group.py -n 2014_students_EC2 -p accounts/group_policies/ec2.json"`
    2. Add IAM group for EMR: `accounts/add_group.py -n 2014_students_EMR -p accounts/group_policies/emr.json"`
    3. Add IAM group for S3: `accounts/add_group.py -n 2014_students_S3 -p accounts/group_policies/s3.json"`
4. Create the users CSV file, see below and example_users.csv for an example CSV file.
5. Add users from CSV file: `accounts/add_users.py -c ~/Desktop/dse_users.csv`
6. Distribute *username_aws_console_password.txt* & *username_aws_credentials.csv* to each user.


## add_group.py - Add IAM Groups
Due to the character limits on IAM group inline policies, I recommend creating a new group for each policy. 

Included policies:

* **group_policies/ec2.json**: DeleteVolume, DetachVolume, RebootInstances, StopInstances, TerminateInstances access for instances that have an owner tag that is equal to ${aws:username}. Full access to everything else.
* **group_policies/emr.json**: Access to list clusters and submit new job flows.
* **group_policies/s3.json**: Full access to the bucket named dse-${aws:username}. List access to everything else.

*${aws:username}* equals the IAM username.

Example usage: `./add_group.py -n 2014_students_EC2 -p group_policies/ec2.json"`


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

Example usage: `./add_users.py -c csv_file -o ~/Vault/users/`

CREATE_ACCOUNTS
===============


## Setup

1. Only works on Python 2.7
1. Install mechanize: `$ pip install mechanize`
1. Install github3: `$ pip install --pre github3.py`


## Create GitHub Repositories for Students

1. Create an CSV file with a row for each student's UCSD username and GitHub password.
3. Run the create_accounts script and include the path to the csv file and the Academic Year: `$ create_accounts.py -c csv_file.csv -y 2015`

Example CSV file:

```
ucsd_username1@eng.ucsd.edu,password1
ucsd_username2@eng.ucsd.edu,password2
ucsd_username3@eng.ucsd.edu,password3
```

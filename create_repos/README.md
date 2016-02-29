CREATE_REPOS
============


## Setup

1. Install github3: `$ pip install --pre github3.py`


## Create GitHub Repositories for Students

1. Have each student create a GitHub account and collect each student's GitHub username with a Google Drive Form.
2. Create CSV file with a row for each student's UCSD username and GitHub username.
3. Run the create_repos script and include the path to the csv file and the Academic Year: `$ create_repos.py -c csv_file.csv -y 2015`

Example CSV file:

```
ucsd_username1,githubname1
ucsd_username2,githubname2
ucsd_username3,githubname3
```

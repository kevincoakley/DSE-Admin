SHARE_CREDENTIALS
=================

## Setup

1. Follow step 1 at https://developers.google.com/drive/web/quickstart/python to enable the Google 
Drive API and download the client_secret.json file
2. Copy client_secret.json to your Vault directory
3. Install google-api-python-client: `$ pip install --upgrade google-api-python-client`

## Run

1. Copy all files from Vault/users to Google Drive: `$ ./share_files.py -r google_drive_folder_name`
  * *NOTE*: 
    * Directories Vault/users/username will be shared with username@eng.ucsd.edu
    * Directories Vault/users/google@account.name will be shared with google@account.name

### Google Drive Documentation

* https://developers.google.com/drive/web/about-sdk
* https://developers.google.com/resources/api-libraries/documentation/drive/v2/python/latest/index.html

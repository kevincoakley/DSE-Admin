SHARE_CREDENTIALS
=================


## Setup

1. Follow step 1 at https://developers.google.com/drive/web/quickstart/python to enable the Google 
Drive API and download the client_secret.json file
2. Copy client_secret.json to your save directory
3. Install google-api-python-client: `$ pip install --upgrade google-api-python-client`


## Share Credentials using Google Drive

1. Authorize your computer (first time only): 
    1. Run quickstart.py in the directory where client_secret.json is saved
    2. Select the authorize button when browser window opens
2. Copy all files from save/users to Google Drive: `$ share_credentials.py -s ~/save -r google_drive_folder_name`
  * *NOTE*: 
    * Directories save/users/username will be shared with username@eng.ucsd.edu
    * Directories save/users/google@account.name will be shared with google@account.name


### Google Drive Documentation

* https://developers.google.com/drive/web/about-sdk
* https://developers.google.com/resources/api-libraries/documentation/drive/v2/python/latest/index.html

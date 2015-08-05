#!/usr/bin/env python

import httplib2
import os
import sys
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import apiclient.http
import argparse
import logging
from ucsd_bigdata.vault import Vault

SCOPES = 'https://www.googleapis.com/auth/drive'

APPLICATION_NAME = 'DSE-Admin'


def get_credentials(client_secret_file="client_secret.json"):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(client_secret_file, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials


def create_directory(name, parent_id=None):
    logging.info("Creating Directory: %s Parent: %s" % (name, parent_id))

    if parent_id is None:
        body = {
            'title': name,
            'mimeType': "application/vnd.google-apps.folder"
        }
    else:
        body = {
            'title': name,
            'parents': [{
                'id': parent_id
            }],
            'mimeType': "application/vnd.google-apps.folder"
        }

    directory = service.files().insert(body=body).execute()
    print "Directory Created: %s (%s)" % (directory["title"], directory["id"])
    logging.info("Directory Created: %s (%s)" % (directory["title"], directory["id"]))

    return directory["id"]


def upload_file(file_to_upload, parent_id):
    logging.info("Uploading File: %s Parent: %s" % (file_to_upload, parent_id))

    file_to_upload_path, file_name = os.path.split(file_to_upload)

    media_body = apiclient.http.MediaFileUpload(file_to_upload, resumable=True)

    body = {
        'title': file_name,
        'parents': [{
            'id': parent_id
        }],
    }

    # Perform the request and print the result.
    uploaded_file = service.files().insert(body=body, media_body=media_body).execute()
    print "File Uploaded: %s (%s)" % (uploaded_file["title"], uploaded_file["id"])
    logging.info("File Uploaded: %s (%s)" % (uploaded_file["title"], uploaded_file["id"]))

    return uploaded_file["id"]


def share(directory_id, google_username):
    logging.info("Sharing Directory %s with %s" % (directory_id, google_username))

    if "@" not in google_username:
        google_username = "%s@eng.ucsd.edu" % google_username

    body = {
        'value': google_username,
        'type': 'user',
        'role': 'reader'
    }

    service.permissions().insert(fileId=directory_id,
                                 body=body,
                                 sendNotificationEmails=False).execute()
    share_url = "https://drive.google.com/a/eng.ucsd.edu/folderview?id=%s&usp=sharing" \
                % directory_id
    print "Directory %s Shared with %s" % (directory_id, google_username)
    print "Share URL: %s" % share_url
    logging.info("Directory %s Shared with %s" % (directory_id, google_username))
    logging.info("Share URL: %s" % share_url)

    return share_url


if __name__ == '__main__':
    # parse parameters
    parser = argparse.ArgumentParser(description="Share files with students using Google Drive",
                                     epilog="Example: ./share_files.py -r DSE_2015")
    parser.add_argument("-l",
                        metavar="local_directory",
                        dest="local_directory",
                        help="Directory on local computer",
                        default=None,
                        required=False)
    parser.add_argument("-r",
                        dest="remote_directory",
                        metavar="remote_directory",
                        help="Name of folder on Google Drive",
                        required=True)

    args = vars(parser.parse_args())

    # Get the vault from ~/.vault or default to ~/Vault
    vault = Vault()

    # If local_directory isn't specified, use vault/users/
    local_directory = "%s/users/" % vault.path
    if args['local_directory'] is not None:
        local_directory = args['local_directory']

    # Create a logs directory in the vault directory if one does not exist
    if not os.path.exists(vault.path + "/logs"):
        os.makedirs(vault.path + "/logs")

    # Save a log to vault/logs/share_files.log
    logging.basicConfig(filename=vault.path + "/logs/share_files.log",
                        format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logging.info("share_files.py started")
    logging.info("Local Directory: %s" % local_directory)
    logging.info("Remote Directory: %s" % args["remote_directory"])
    logging.info("Vault: %s" % vault.path)

    if not os.path.exists(local_directory):
        logging.info("Local Directory (%s) does not exist." % local_directory)
        sys.exit("Local Directory (%s) does not exist." % local_directory)

    # Authenticate to Google Drive
    google_drive_credentials = get_credentials("%s/client_secret.json" % vault.path)
    http = google_drive_credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v2', http=http)

    # Store all of the path ids in a dict
    path_ids = dict()

    path_ids["/"] = create_directory(args["remote_directory"])

    for path, dirs, files in os.walk(local_directory):
        relative_path = path.replace(local_directory, "/")

        if relative_path == "/":
            continue

        # Get the parent directory path and the directory name
        parent, directory_name = os.path.split(relative_path)

        # Create Google Drive directory and store the id in path_ids
        path_ids[relative_path] = create_directory(directory_name, path_ids[parent])

        # If the parent is the root directory then share the directory with the student
        if path_ids[parent] == path_ids["/"]:
            share(path_ids[relative_path], directory_name)

        for f in files:
            file_path = "%s/%s" % (path, f)
            upload_file(file_path, path_ids[relative_path])

    logging.info("share_files.py finished")

#!/usr/bin/env python

import sys
import os
from glob import glob
import csv
import json
from boto.s3.connection import S3Connection
from boto.exception import S3ResponseError
import time
import logging
import argparse
import shutil
from vault import Vault

credentials_file_name = "credentials.json"


def test_aws_credentials(aws_access_key_id, aws_secret_access_key):
    s3_conn = S3Connection(aws_access_key_id, aws_secret_access_key)

    try:
        s3_conn.get_all_buckets()
        logging.info("AWS Access Key ID and Access Key are correct: %s" % aws_access_key_id)
        s3_conn.close()
        return True
    except S3ResponseError:
        s3_conn.close()
        logging.info("WARN: AWS Access Key ID and Access Key are incorrect: %s" % aws_access_key_id)
        return False


def collect_credentials():
    credentials = []

    # Log the csv files found in the vault directory
    for csv_file in glob(vault + '/*.csv'):
        logging.info("Found csv file: %s" % csv_file)

        if os.path.isfile(csv_file):
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                aws_credentials_list = list(reader)

                for aws_credentials in aws_credentials_list:
                    # Skip the csv column header
                    if not aws_credentials[1] == "Access Key Id":
                        if test_aws_credentials(aws_credentials[1], aws_credentials[2]):
                            credentials.append({'user_name': aws_credentials[0],
                                                'access_key_id': aws_credentials[1],
                                                'secret_access_key': aws_credentials[2]})

    # If there is more than one AWS key pair then display them using a menu,
    # otherwise just select the one
    if len(credentials) > 1:
        # Log the valid AWS credentials that are found
        logging.info("Multiple AWS credentials found:")

        print "You have multiple AWS credentials in your vault. The user names are listed below:\n"

        for position, credential in enumerate(credentials):
            logging.info("AWS credential found: %s : %s" %
                         (credential["user_name"], credential["access_key_id"]))

            print "\t%s. %s (%s)" % (position + 1,
                                     credential["user_name"],
                                     credential["access_key_id"])

        # Make sure user_input is value
        selected_credentials = None
        while selected_credentials is None:
            user_input = raw_input("\nEnter the number next to the credentials that "
                                   "you would like to use: ")
            try:
                if 0 < int(user_input) <= len(credentials):
                    selected_credentials = int(user_input) - 1
            except ValueError:
                continue

        logging.info("AWS credential selected: %s : %s" %
                     (credentials[selected_credentials]["user_name"],
                      credentials[selected_credentials]["access_key_id"]))
    elif len(credentials) == 1:
        selected_credentials = 0
        logging.info("One AWS credential found and selected: %s : %s" %
                     (credentials[selected_credentials]["user_name"],
                      credentials[selected_credentials]["access_key_id"]))
    else:
        logging.info("No AWS credentials found")
        sys.exit("No AWS credentials found.")

    return credentials[selected_credentials]["user_name"], \
        credentials[selected_credentials]["access_key_id"], \
        credentials[selected_credentials]["secret_access_key"]


def save_credentials_json(json_object_name, aws_user_name, aws_access_key_id,
                          aws_secret_access_key):
    # Make sure all of the variables exist before trying to write them to
    # vault/credentials_file_name
    if ((aws_user_name is not None) and (aws_access_key_id is not None) and
            (aws_secret_access_key is not None)):
        print "ID: %s, key_id: %s" % (aws_user_name, aws_access_key_id)
    else:
        logging.info("Undefined variable: user_id: %s, key_id: %s " % (aws_user_name,
                                                                       aws_access_key_id))
        sys.exit("Undefined variable")

    credentials_json = dict()

    # If credentials_file_name already exists then make a copy of the file and copy the
    # credentials that are not json_object_name credentials into the new credentials_file_name
    if os.path.isfile("%s/%s" % (vault, credentials_file_name)):
        logging.info("Found existing %s/%s" % (vault, credentials_file_name))
        # Make a copy of vault/credentials_file_name before making any changes
        credentials_file_copy = "%s/%s-%s" % (vault, credentials_file_name, str(int(time.time())))
        try:
            shutil.copyfile("%s/%s" % (vault, credentials_file_name), credentials_file_copy)
            logging.info("Copied %s/%s to %s" % (vault, credentials_file_name,
                                                 credentials_file_copy))
        except (IOError, EOFError):
            logging.info("Error copying %s/%s to %s" % (vault, credentials_file_name,
                                                        credentials_file_copy))
            sys.exit("Error copying %s/%s to %s" % (vault, credentials_file_name,
                                                    credentials_file_copy))

        # Read the contents of vault/credentials_file_name
        old_credentials_json = dict()
        try:
            with open("%s/%s" % (vault, credentials_file_name)) as old_credentials:
                old_credentials_json = json.load(old_credentials)
            logging.info("Reading old credentials in %s/%s" % (vault, credentials_file_name))
        except (IOError, EOFError):
            logging.info("Error reading %s/%s" % (vault, credentials_file_name))
            print "Error reading %s/%s" % (vault, credentials_file_name)

        # Add all the top level keys to credentials_json that are not json_object_name
        for top_level_key in old_credentials_json:
            if not top_level_key == json_object_name:
                credentials_json[top_level_key] = old_credentials_json[top_level_key]
    else:
        logging.info("Creating a new %s/%s" % (vault, credentials_file_name))
        print "Creating a new %s/%s" % (vault, credentials_file_name)

    # Add the new credentials
    logging.info("Adding json_object_name: %s, aws_user_name: %s, aws_access_key_id: %s to %s"
                 % (json_object_name, aws_user_name, aws_access_key_id, credentials_file_name))

    credentials_json[json_object_name] = dict()
    credentials_json[json_object_name]["aws_user_name"] = aws_user_name
    credentials_json[json_object_name]["aws_access_key_id"] = aws_access_key_id
    credentials_json[json_object_name]["aws_secret_access_key"] = aws_secret_access_key

    # Write the new vault/credentials_file_name
    with open("%s/%s" % (vault, credentials_file_name), 'w') as json_outfile:
        json.dump(credentials_json, json_outfile, sort_keys=True, indent=4, separators=(',', ': '))
    json_outfile.close()

    logging.info("Saved %s/%s" % (vault, credentials_file_name))


def clear_vault():
    backup_directory = "%s/Vault_%s" % (vault, str(int(time.time())))

    os.makedirs(backup_directory)
    logging.info("Clearing Vault to %s" % backup_directory)

    # Move all of the non .csv files into the backup_directory
    for clear_vault_file in glob(vault+'/*'):
        if os.path.isfile(clear_vault_file):
            if os.path.splitext(clear_vault_file)[1] == ".csv":
                logging.info("Leaving Vault file: %s" % clear_vault_file)
            else:
                logging.info("Moving Vault file: %s" % clear_vault_file)
                os.rename(clear_vault_file,
                          backup_directory + "/" + os.path.basename(str(clear_vault_file)))
    logging.info("Clearing Complete")


if __name__ == "__main__":

    my_vault = Vault()
    vault = my_vault.path

    # Create a logs directory in the vault directory if one does not exist
    if not os.path.exists(vault + "/logs"):
        os.makedirs(vault + "/logs")

    # Save a log to vault/logs/setup.log
    logging.basicConfig(filename=vault + "/logs/setup.log",
                        format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logging.info("setup.py started")
    logging.info("Vault: %s" % vault)

    # Log all of the files in the Vault directory
    for vault_file in glob(vault+'/*'):
        logging.info("Found Vault file: %s" % vault_file)

    # Commandline Parameters
    parser = argparse.ArgumentParser(description="setup.py: Collects the AWS credentials and "
                                                 "stores them in json file.")
    parser.add_argument('-c', dest='clear', action='store_true', default=False,
                        help='Clear the Vault directory before running')
    parser.add_argument('-r', dest='region', action='store', type=str, default="us-east-1",
                        help='The AWS region where the EC2 ssh key pair is created in')
    parser.add_argument('-o', dest='json_object_name', action='store', type=str, default="admin",
                        help='The name of the JSON object used to store the credentials')

    args = vars(parser.parse_args())

    if args['clear']:
        clear_vault()

    # Collect the AWS credentials stored in the Vault
    user_id, key_id, secret_key = collect_credentials()

    # Save the credentials to the user's Vault
    save_credentials_json(args['json_object_name'], user_id, key_id, secret_key)

    logging.info("setup.py finished")

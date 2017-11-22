#!/usr/bin/env python

import os.path
import sys
import boto
import random
import argparse
import logging
import csv


def random_password_generator():
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    upper_alphabet = alphabet.upper()
    password_length = 8
    password_list = []

    for i in range(password_length//3):
        password_list.append(alphabet[random.randrange(len(alphabet))])
        password_list.append(upper_alphabet[random.randrange(len(upper_alphabet))])
        password_list.append(str(random.randrange(10)))
    for i in range(password_length-len(password_list)):
        password_list.append(alphabet[random.randrange(len(alphabet))])

    random.shuffle(password_list)
    password_string = "".join(password_list)

    return password_string


if __name__ == "__main__":

    # parse parameters
    parser = argparse.ArgumentParser(description="Create IAM users from a CSV file")

    parser.add_argument("-k",
                        metavar="aws_access_key_id",
                        dest="aws_access_key_id",
                        help="AWS Access Key ID",
                        required=True)
    parser.add_argument("-s",
                        metavar="aws_secret_access_key",
                        dest="aws_secret_access_key",
                        help="AWS Secret Access Key",
                        required=True)
    parser.add_argument("-c",
                        metavar="csv_file",
                        dest="csv_file",
                        help="Location of the user CSV file",
                        required=True)
    parser.add_argument("-u",
                        metavar="console_url",
                        dest="console_url",
                        help="Console URL; example https://mas-dse.signin.aws.amazon.com/console",
                        required=True)
    parser.add_argument("-o",
                        dest="output_path",
                        metavar="output_path",
                        help="Path to where the output will be saved",
                        required=True)
    parser.add_argument("-s3",
                        dest="s3",
                        help="Create a S3 bucket for the user. Default is False.",
                        choices=['True', 'False'],
                        default=False)

    args = vars(parser.parse_args())

    # Create a logs directory in the vault directory if one does not exist
    if not os.path.exists(args['output_path'] + "/logs"):
        os.makedirs(args['output_path'] + "/logs")

    # Save a log to vault/logs/LaunchNotebookServer.log
    logging.basicConfig(filename=args['output_path'] + "/logs/add_students.log",
                        format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logging.info("add_users.py started")
    logging.info("CSV File: %s" % args['csv_file'])
    logging.info("Output Path: %s" % args['output_path'])

    # Open IAM connection to aws
    try:
        iam = boto.connect_iam(aws_access_key_id=args['aws_access_key_id'],
                               aws_secret_access_key=args['aws_secret_access_key'])
        logging.info("Created IAM Connection = %s" % iam)
        print("Created IAM Connection = %s" % iam)
    except Exception as e:
        logging.info("There was an error connecting to AWS IAM: %s" % e)
        sys.exit("There was an error connecting to AWS IAM: %s" % e)

    # Open S3 connection to aws
    try:
        s3 = boto.connect_s3(aws_access_key_id=args['aws_access_key_id'],
                             aws_secret_access_key=args['aws_secret_access_key'])
        logging.info("Created S3 Connection = %s" % s3)
        print("Created S3 Connection = %s" % s3)
    except Exception as e:
        logging.info("There was an error connecting to AWS S3: %s" % e)
        sys.exit("There was an error connecting to AWS S3: %s" % e)

    # Read CSV File into a list
    try:
        csv_reader = csv.reader(open(args['csv_file'], 'rU'), dialect=csv.excel_tab, delimiter=',')
        csv_users_list = list(csv_reader)
        logging.info("Contents of the CSV file %s:\n %s" % (args['csv_file'], csv_users_list))
    except Exception as e:
        logging.info("There was an error reading the CSV file %s: %s" % (args['csv_file'], e))
        sys.exit("There was an error reading the CSV file %s: %s" % (args['csv_file'], e))

    for row in csv_users_list:
        if len(row) > 0:
            user_name = row.pop(0)
            password = random_password_generator()

            try:
                user = iam.create_user(user_name)
                logging.info("Added user %s" % user_name)
            except Exception as e:
                logging.info("There was an error adding %s: %s" % (user_name, e))
                sys.exit("There was an error adding %s: %s" % (user_name, e))

            try:
                iam.create_login_profile(user_name, password)
                logging.info("Added random password to user %s" % user_name)
            except Exception as e:
                logging.info("There was an error adding random password (%s) to %s: %s" %
                             (password, user_name, e))
                sys.exit("There was an error adding random password (%s) to %s: %s" %
                         (password, user_name, e))

            # Add user to groups
            for user_group in row:
                if len(user_group) > 0:
                    try:
                        iam.add_user_to_group(user_group, user_name)
                        logging.info("Added user %s to group %s" % (user_name, user_group))
                    except Exception as e:
                        logging.info("There was an error adding user %s to group %s: %s" %
                                     (user_name, user_group, e))
                        sys.exit("There was an error adding user %s to group %s: %s" %
                                 (user_name, user_group, e))

            # Create access_key_id/secret_access_key
            try:
                access_key = iam.create_access_key(user_name)
                logging.info("Got the access_key for %s " % user_name)
            except Exception as e:
                logging.info("There was an error getting the access_key for %s: %s" %
                             (user_name, e))
                sys.exit("There was an error getting the access_key for %s: %s" % (user_name, e))

            try:
                access_key_id = access_key.access_key_id
                logging.info("Got the access_key_id for %s " % user_name)
            except Exception as e:
                logging.info("There was an error getting the access_key_id for %s: %s" %
                             (user_name, e))
                sys.exit("There was an error getting the access_key_id for %s: %s" % (user_name, e))

            try:
                secret_access_key = access_key.secret_access_key
                logging.info("Got the secret_access_key for %s " % user_name)
            except Exception as e:
                logging.info("There was an error getting the secret_access_key for %s: %s" %
                             (user_name, e))
                sys.exit("There was an error getting the secret_access_key for %s: %s" %
                         (user_name, e))

            print("Username: %s Password: %s" % (user_name, password))
            print("Access key: %s Secret: %s" % (access_key_id, secret_access_key))

            # Get the path the save the credentials
            if (args['output_path'] is None) or (len(args['output_path']) == 0):
                output_path = "%s/users/" % args['output_path']
            else:
                output_path = args['output_path']

            # Make sure the output_path ends with /
            if not output_path.endswith("/"):
                output_path = "%s/" % output_path

            # Create the output_path if it doesn't exist
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            # Create a directory for the user if it doesn't exist
            if not os.path.exists("%s%s/" % (output_path, user_name)):
                os.makedirs("%s/%s/" % (output_path, user_name))

            console_text_file = "%s%s/%s_aws_console_password.txt" % (output_path,
                                                                      user_name, user_name)
            credentials_text_file = "%s%s/%s_aws_credentials.csv" % (output_path,
                                                                     user_name, user_name)

            try:
                console_text = open(console_text_file, "w")
                console_text.write("AWS Console URL: "
                                   "%s\n\n"
                                   "Username: %s\n"
                                   "Password: %s\n" % (args['console_url'], user_name, password))
                console_text.close()
                logging.info("Wrote the console password file for %s: %s" % (user_name,
                                                                             console_text_file))
            except Exception as e:
                logging.info("There was an error writing the console password file %s: %s" %
                             (console_text_file, e))
                sys.exit("There was an error writing the console password file %s: %s" %
                         (console_text_file, e))

            try:
                credentials_text = open(credentials_text_file, "w")
                credentials_text.write("User Name,Access Key Id,Secret Access Key\n")
                credentials_text.write("\"%s\",%s,%s" % (user_name, access_key_id,
                                                         secret_access_key))
                credentials_text.close()
                logging.info("Wrote the credentials file for %s: %s" % (user_name,
                                                                        credentials_text_file))
            except Exception as e:
                logging.info("There was an error writing the credentials file %s: %s" %
                             (credentials_text_file, e))
                sys.exit("There was an error writing the credentials file %s: %s" %
                         (credentials_text_file, e))

            # Create an s3 bucket for the user
            if args['s3'] is True:
                s3_bucket = "dse-%s" % user_name
                try:
                    s3.create_bucket(s3_bucket)
                    print("Created s3 bucket: %s" % s3_bucket)
                    logging.info("Created s3 bucket: %s" % s3_bucket)
                except Exception as e:
                    logging.info("There was an error creating s3 bucket %s: %s" % (s3_bucket, e))
                    sys.exit("There was an error creating s3 bucket %s: %s" % (s3_bucket, e))

    logging.info("add_users.py finished")

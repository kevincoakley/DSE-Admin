#!/usr/bin/env python

import os.path
import sys
import boto
import argparse
import logging
import csv


if __name__ == "__main__":

    # parse parameters
    parser = argparse.ArgumentParser(description="Delete IAM users missing from a CSV file")

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

    parser.add_argument("-g",
                        metavar="group_name",
                        dest="group_name",
                        help="Name of the group to compare user list",
                        required=True)

    parser.add_argument("-s3",
                        dest="s3",
                        help="Delete a S3 bucket for the user. Default is True.",
                        choices=['True', 'False'],
                        default=True)
    parser.add_argument("-o",
                        dest="output_path",
                        metavar="output_path",
                        help="Path to where the output will be saved",
                        required=True)

    args = vars(parser.parse_args())

    # Create a logs directory in the vault directory if one does not exist
    if not os.path.exists(args['output_path'] + "/logs"):
        os.makedirs(args['output_path'] + "/logs")

    # Save a log to vault/logs/LaunchNotebookServer.log
    logging.basicConfig(filename=args['output_path'] + "/logs/del_students.log",
                        format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logging.info("del_users.py started")
    logging.info("CSV File: %s" % args['csv_file'])
    logging.info("Group Name: %s" % args['group_name'])
    logging.info("Output Path: %s" % args['output_path'])

    # Open IAM connection to aws
    try:
        iam = boto.connect_iam(aws_access_key_id=args['aws_access_key_id'],
                               aws_secret_access_key=args['aws_secret_access_key'])
        logging.info("Created IAM Connection = %s" % iam)
        print "Created IAM Connection = %s" % iam
    except Exception, e:
        logging.info("There was an error connecting to AWS IAM: %s" % e)
        sys.exit("There was an error connecting to AWS IAM: %s" % e)

    # Open S3 connection to aws
    try:
        s3 = boto.connect_s3(aws_access_key_id=args['aws_access_key_id'],
                             aws_secret_access_key=args['aws_secret_access_key'])
        logging.info("Created S3 Connection = %s" % s3)
        print "Created S3 Connection = %s" % s3
    except Exception, e:
        logging.info("There was an error connecting to AWS S3: %s" % e)
        sys.exit("There was an error connecting to AWS S3: %s" % e)

    # Get the list of users in IAM group_name
    iam_group_users = iam.get_group(args['group_name'])

    group_users = []

    if "get_group_response" in iam_group_users:
        if "get_group_result" in iam_group_users["get_group_response"]:
            if "users" in iam_group_users["get_group_response"]["get_group_result"]:
                for user in iam_group_users["get_group_response"]["get_group_result"]["users"]:
                    group_users.append(user["user_name"])
            else:
                sys.exit("users not in iam_group_users")
        else:
            sys.exit("get_group_result not in iam_group_users")
    else:
        sys.exit("get_group_response not in iam_group_users")

    if len(group_users) is 0:
        sys.exit("No users in IAM group")

    # Read CSV File into a list
    try:
        csv_reader = csv.reader(open(args['csv_file'], 'rU'), dialect=csv.excel_tab, delimiter=',')
        csv_users_list = list(csv_reader)
        logging.info("Contents of the CSV file %s:\n %s" % (args['csv_file'], csv_users_list))
    except Exception, e:
        logging.info("There was an error reading the CSV file %s: %s" % (args['csv_file'], e))
        sys.exit("There was an error reading the CSV file %s: %s" % (args['csv_file'], e))

    csv_users = []

    for row in csv_users_list:
        if len(row) > 0:
            csv_users.append(row.pop(0))

    if len(csv_users) is 0:
        sys.exit("No users in CSV File")

    # Check if user in group_users also exists in csv_users. If user in group_users and not in
    # csv_users then delete user from IAM
    for group_user in group_users:

        if group_user not in csv_users:
            print "%s is NOT in group; Deleting user." % group_user

            try:
                # Find all of the access keys associated with the user and delete them
                access_keys = iam.get_all_access_keys(group_user)

                for access_key in access_keys["list_access_keys_response"]["list_access_keys_result"]["access_key_metadata"]:
                    iam.delete_access_key(access_key["access_key_id"], user_name=group_user)

                # Find all of the groups the user belongs to and remove them from those groups
                user_groups = iam.get_groups_for_user(group_user)

                for user_group in user_groups["list_groups_for_user_response"]["list_groups_for_user_result"]["groups"]:
                    iam.remove_user_from_group(user_group["group_name"], group_user)

                # Delete the user account
                iam.delete_login_profile(group_user)
                iam.delete_user(group_user)
                logging.info("Deleting user %s" % group_user)
            except Exception, e:
                logging.info("There was an error deleting %s: %s" % (group_user, e))
                sys.exit("There was an error deleting %s: %s" % (group_user, e))

            # Delete the user's s3 bucket
            if args['s3'] is True:
                s3_bucket = "dse-%s" % group_user
                try:
                    # Delete all keys in the bucket
                    bucket = s3.get_bucket(s3_bucket)
                    bucket.delete_keys(bucket.get_all_keys())

                    s3.delete_bucket(bucket)
                    print "Deleted s3 bucket: %s" % s3_bucket
                    logging.info("Deleted s3 bucket: %s" % s3_bucket)
                except Exception, e:
                    logging.info("There was an error deleting s3 bucket %s: %s" % (s3_bucket, e))
                    sys.exit("There was an error deleting s3 bucket %s: %s" % (s3_bucket, e))

    logging.info("del_users.py finished")

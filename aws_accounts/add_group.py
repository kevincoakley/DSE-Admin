#!/usr/bin/env python

import os.path
from os.path import basename
from os.path import splitext
import sys
import argparse
import logging
import boto


if __name__ == "__main__":
    # parse parameters
    parser = argparse.ArgumentParser(description="Create an IAM group from a policy JSON file")

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
    parser.add_argument("-n",
                        metavar="IAM_group_name",
                        dest="iam_group_name",
                        help="Name of the IAM group to be created",
                        required=True)
    parser.add_argument("-p",
                        dest="policy_file",
                        metavar="policy.json",
                        help="Location of the policy JSON file",
                        required=True)
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
    logging.basicConfig(filename=args['output_path'] + "/logs/add_group.log",
                        format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logging.info("add_group.py started")
    logging.info("IAM Group Name: %s" % args['iam_group_name'])
    logging.info("Policy File: %s" % args['policy_file'])
    logging.info("Output Path: %s" % args['output_path'])

    # Open connection to aws
    try:
        iam = boto.connect_iam(aws_access_key_id=args['aws_access_key_id'],
                               aws_secret_access_key=args['aws_secret_access_key'])
        logging.info("Created Connection = %s" % iam)
        print("Created Connection = %s" % iam)
    except Exception as e:
        logging.info("There was an error connecting to AWS: %s" % e)
        sys.exit("There was an error connecting to AWS: %s" % e)

    try:
        with open(args['policy_file'], "r") as policy_file:
            policy = policy_file.read()
            logging.info("Policy from %s:\n%s" % (args['policy_file'], policy))
    except Exception as e:
        logging.info("There was an error reading the policy JSON file: %s" % e)
        sys.exit("There was an error reading the policy JSON file: %s" % e)

    try:
        iam.create_group(args['iam_group_name'])
        logging.info("Added IAM group %s" % args['iam_group_name'])
        print("Added IAM group %s" % args['iam_group_name'])
    except Exception as e:
        logging.info("There was an error adding the group %s:\n %s" % (args['iam_group_name'], e))
        sys.exit("There was an error adding the group %s:\n %s" % (args['iam_group_name'], e))

    try:
        iam.put_group_policy(args['iam_group_name'], splitext(basename(args['policy_file']))[0],
                             policy)
        logging.info("Policy %s added to IAM group %s" % (args['policy_file'],
                                                          args['iam_group_name']))
        print("Policy %s added to IAM group %s" % (args['policy_file'], args['iam_group_name']))
    except Exception as e:
        logging.info("There was an error adding the policy to group %s:\n %s" %
                     (args['iam_group_name'], e))
        sys.exit("There was an error adding the policy to group %s:\n %s" %
                 (args['iam_group_name'], e))

    logging.info("add_group.py finished")

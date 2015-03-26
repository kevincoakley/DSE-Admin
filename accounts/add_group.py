#!/usr/bin/env python

import os
from os.path import basename
from os.path import splitext
import sys
import argparse
import logging
import boto
import dse_credentials

if __name__ == "__main__":
    # parse parameters
    parser = argparse.ArgumentParser(description="Create an IAM group from a policy JSON file",
                                     epilog="Example: ./add_group.py -n 2014_students_EC2 -p group_policies/ec2.json")
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

    args = vars(parser.parse_args())

    # Get vault location
    vault = dse_credentials.get_vault()

    # Create a logs directory in the vault directory if one does not exist
    if not os.path.exists(vault + "/logs"):
        os.makedirs(vault + "/logs")

    # Save a log to vault/logs/LaunchNotebookServer.log
    logging.basicConfig(filename=vault + "/logs/add_group.log", format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logging.info("add_group.py started")
    logging.info("IAM Group Name: %s" % args['iam_group_name'])
    logging.info("Policy File: %s" % args['policy_file'])
    logging.info("Vault: %s" % vault)

    # Read AWS key_id and key_secret from vault
    aws_access_key_id, aws_secret_access_key = dse_credentials.read_credentials(vault)

    # Open connection to aws
    try:
        iam = boto.connect_iam(aws_access_key_id=aws_access_key_id,
                               aws_secret_access_key=aws_secret_access_key)
        logging.info("Created Connection = %s" % iam)
        print "Created Connection = %s" % iam
    except Exception, e:
        logging.info("There was an error connecting to AWS: %s" % e)
        sys.exit("There was an error connecting to AWS: %s" % e)

    try:
        with open(args['policy_file'], "r") as policy_file:
            policy = policy_file.read()
            logging.info("Policy from %s:\n%s" % (args['policy_file'], policy))
    except Exception, e:
        logging.info("There was an error reading the policy JSON file: %s" % e)
        sys.exit("There was an error reading the policy JSON file: %s" % e)

    try:
        iam.create_group(args['iam_group_name'])
        logging.info("Added IAM group %s" % args['iam_group_name'])
        print "Added IAM group %s" % args['iam_group_name']
    except Exception, e:
        logging.info("There was an error adding the group %s:\n %s" % (args['iam_group_name'], e))
        sys.exit("There was an error adding the group %s:\n %s" % (args['iam_group_name'], e))

    try:
        iam.put_group_policy(args['iam_group_name'], splitext(basename(args['policy_file']))[0], policy)
        logging.info("Policy %s added to IAM group %s" % (args['policy_file'], args['iam_group_name']))
        print "Policy %s added to IAM group %s" % (args['policy_file'], args['iam_group_name'])
    except Exception, e:
        logging.info("There was an error adding the policy to group %s:\n %s" % (args['iam_group_name'], e))
        sys.exit("There was an error adding the policy to group %s:\n %s" % (args['iam_group_name'], e))

    logging.info("add_group.py finished")
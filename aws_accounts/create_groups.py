#!/usr/bin/env python

import os.path
from os.path import basename
from os.path import splitext
import sys
import subprocess
import argparse
import logging
import boto

def main():
    args = parse_args()
    path_to_script = os.path.dirname(os.path.realpath(__file__))

    # Create custom policy file for s3
    custom_s3_policy_path = create_custom_policy(args['cohort_number'], args['group_number'], args['account_id'])

    # List of groups that will be created
    group_params = [
        {'group_name': 'Billing',       'policy_path': os.path.join(path_to_script, 'group_policies/billing.json')},
        {'group_name': 'EC2',           'policy_path': os.path.join(path_to_script, 'group_policies/ec2/spark_notebook.json')},
        {'group_name': 'EC2_treasurer', 'policy_path': os.path.join(path_to_script, 'group_policies/ec2/spark_notebook_treasurer.json')},
        {'group_name': 'EMR',           'policy_path': os.path.join(path_to_script, 'group_policies/emr/emr.json')},
        {'group_name': 'EMR_treasurer', 'policy_path': os.path.join(path_to_script, 'group_policies/emr/emr_iam_role.json')},
        {'group_name': 'IAM',           'policy_path': os.path.join(path_to_script, 'group_policies/iam.json')},
        {'group_name': 'S3',            'policy_path': custom_s3_policy_path}
    ]

    # Create the groups
    for group_param in group_params:
        create_group(args['aws_access_key_id'], args['aws_secret_access_key'], group_param['group_name'], group_param['policy_path'], args['output_path'])

    # Delete the custom policy
    os.remove(custom_s3_policy_path)


def parse_args():
    parser = argparse.ArgumentParser(description="Perform initial setup of groups")

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
    parser.add_argument("-a",
                        metavar="account_id",
                        dest="account_id",
                        help="AWS Account ID",
                        required=True)
    parser.add_argument("-c",
                        dest="cohort_number",
                        metavar="cohort_number",
                        help="The cohort number",
                        required=True)
    parser.add_argument("-g",
                        dest="group_number",
                        metavar="group_number",
                        help="The group number",
                        required=True)
    parser.add_argument("-o",
                        dest="output_path",
                        metavar="output_path",
                        help="Path to where the output will be saved",
                        required=True)

    return vars(parser.parse_args())

def create_custom_policy(cohort_number, group_number, account_id):
    policy_template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "group_policies/s3/spark_notebook_s3.json")
    custom_policy_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cohort{0}group{1}_custom_policy.json'.format(cohort_number, group_number))

    policy_template_file = open(policy_template_path)
    custom_policy_file = open(custom_policy_path, 'w+')

    policy_template_string = policy_template_file.read()
    policy_template_string = policy_template_string.replace('aws-logs-XXXXXXXXXXXX-us-east-1', 'aws-logs-{0}-us-east-1'.format(account_id))
    policy_template_string = policy_template_string.replace('dse-cohort#-group#', 'dse-cohort{0}-group{1}'.format(cohort_number, group_number))

    custom_policy_file.write(policy_template_string)

    policy_template_file.close()
    custom_policy_file.close()

    return custom_policy_path


def create_group(access_key, secret_access_key, policy_name, policy_path, output_path):
    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "add_group.py")

    command_format = "{0} -k {1} -s {2} -n {3} -p {4} -o {5}"
    command = command_format.format(script_path, access_key, secret_access_key, policy_name, policy_path, output_path)
    print("Running command: " + command)
    subprocess.call(command.split(" "))

if __name__ == "__main__":
    main()

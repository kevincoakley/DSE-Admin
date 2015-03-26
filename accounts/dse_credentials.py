#!/usr/bin/env python

import os
import sys
import pickle
import logging
from os.path import expanduser


def get_vault():
    # If the EC2_VAULT environ var is set then use it, otherwise default to ~/Vault/
    try:
        os.environ['EC2_VAULT']
    except KeyError:
        vault = expanduser("~") + '/Vault'
    else:
        vault = os.environ['EC2_VAULT']

    # Exit if no vault directory is found
    if not os.path.isdir(vault):
        sys.exit("Vault directory not found.")

    return vault


def read_credentials(c_vault):
    # Read credentials from vault/Creds.pkl
    try:
        logging.info("(RC) Reading credentials from %s/Creds.pkl" % c_vault)
        p_credentials_path = c_vault + '/Creds.pkl'
        p_credentials_file = open(p_credentials_path)
        p = pickle.load(p_credentials_file)
        credentials = p['admin']
    except Exception, e:
        print e
        logging.info("(RC) Could not read %s/Creds.pkl" % c_vault)
        sys.exit("Could not read %s/Creds.pkl" % c_vault)

    for c in credentials:
        if c == "key_id":
            p_aws_access_key_id = credentials['key_id']
            logging.info("(RC) Found aws_access_key_id: %s" % p_aws_access_key_id)
        elif c == "secret_key":
            p_aws_secret_access_key = credentials['secret_key']
            logging.info("(RC) Found aws_secret_access_key: ...")

    # These credentials are required to be set before proceeding
    try:
        p_aws_access_key_id
        p_aws_secret_access_key
    except NameError, e:
        logging.info("(RC) Not all of the credentials were defined: %s" % e)
        sys.exit("Not all of the credentials were defined: %s" % e)

    return p_aws_access_key_id, p_aws_secret_access_key

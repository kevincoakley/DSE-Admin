#!/usr/bin/env python
import sys
import logging
import pickle
import os
from os.path import expanduser
import json
from urllib2 import urlopen
import time
import datetime
import boto.ec2
import subprocess
import select


ec2_region = "us-east-1"  # us-east-1 or us-west-2
us_east_1_ami_image_id = "ami-9a562df2"  # Ubuntu 14.04 HVM AMI for us-east-1
us_west_2_ami_image_id = "ami-3d50120d"  # Ubuntu 14.04 HVM AMI for us-west-2
ami_image_id = us_east_1_ami_image_id
instance_type = "t2.micro"
ami_owner_id = '846273844940'  # owner id of the MAS DSE account
dse_ami_image_name = "DSE200HVM"
ubuntu_login_id = 'ubuntu'
number_backups_to_keep = 3


def read_credentials(c_vault):
    p_credentials_path = None
    p_aws_access_key_id = None
    p_aws_secret_access_key = None
    p_user_name = None
    p_key_pair_file = None
    p_key_name = None

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
        elif c == "ID":
            p_user_name = credentials['ID']
            logging.info("(RC) Found user_name: %s" % p_user_name)
        elif c == "ssh_key_pair_file":
            p_key_pair_file = credentials['ssh_key_pair_file']    # name of local file storing keypair
            logging.info("(RC) Found key_pair_file: %s" % p_key_pair_file)
        elif c == "ssh_key_name":
            p_key_name = credentials['ssh_key_name']              # name of keypair on AWS
            logging.info("(RC) Found key_name: %s" % p_key_name)

    # These credentials are required to be set before proceeding
    try:
        if p_credentials_path is None:
            logging.info("(RC) p_credentials_path was not defined")
            sys.exit("p_credentials_path was not defined")
        elif p_aws_access_key_id is None:
            logging.info("(RC) p_aws_access_key_id was not defined")
            sys.exit("p_aws_access_key_id was not defined")
        elif p_aws_secret_access_key is None:
            logging.info("(RC) p_aws_secret_access_key was not defined")
            sys.exit("p_aws_secret_access_key was not defined")
        elif p_user_name is None:
            logging.info("(RC) p_user_name was not defined")
            sys.exit("p_user_name was not defined")
        elif p_key_pair_file is None:
            logging.info("(RC) p_key_pair_file was not defined")
            sys.exit("p_key_pair_file was not defined")
        elif p_key_name is None:
            logging.info("(RC) p_key_name was not defined")
            sys.exit("p_key_name was not defined")
    except NameError, e:
        logging.info("(RC) Not all of the credentials were defined: %s" % e)
        sys.exit("Not all of the credentials were defined: %s" % e)

    return p_credentials_path, p_aws_access_key_id, p_aws_secret_access_key, p_user_name, p_key_pair_file, p_key_name


def check_security_groups():
    #
    # Use a security named the same as user_name. Create the security group if it does not exist.
    # Make sure the current IP address is added to the security group if it is missing.
    #

    # Open http://httpbin.org/ip to get the public ip address
    ip_address = json.load(urlopen('http://httpbin.org/ip'))['origin']
    logging.info("(SG) Found IP address: %s" % ip_address)

    security_group_name = user_name

    # Check for the security group and create it if missing
    c_security_groups = [security_group_name]
    security_group_found = False

    for sg in conn.get_all_security_groups():
        if sg.name == security_group_name:
            logging.info("(SG) Found security group: %s" % security_group_name)
            security_group_found = True

            tcp_rule = False
            udp_rule = False
            icmp_rule = False

            # Verify the security group has the current ip address in it
            for rule in sg.rules:
                if (str(rule.ip_protocol) == "tcp" and str(rule.from_port) == "0" and
                        str(rule.to_port) == "65535" and str(ip_address) + "/32" in str(rule.grants)):
                    logging.info("(SG) Found TCP rule: %s : %s" % (security_group_name, ip_address))
                    tcp_rule = True

                if (str(rule.ip_protocol) == "udp" and str(rule.from_port) == "0" and
                        str(rule.to_port) == "65535" and str(ip_address) + "/32" in str(rule.grants)):
                    logging.info("(SG) Found UDP rule: %s : %s" % (security_group_name, ip_address))
                    udp_rule = True

                if (str(rule.ip_protocol) == "icmp" and str(rule.from_port) == "-1" and
                        str(rule.to_port) == "-1" and str(ip_address) + "/32" in str(rule.grants)):
                    logging.info("(SG) Found ICMP rule: %s : %s" % (security_group_name, ip_address))
                    icmp_rule = True

            # If the current ip address is missing from the security group then add it
            if tcp_rule is False:
                logging.info("(SG) Adding " + str(ip_address) + " (TCP) to " + security_group_name + " security group")
                print "Adding " + str(ip_address) + " (TCP) to " + security_group_name + " security group"
                sg.authorize('tcp', 0, 65535, str(ip_address) + "/32")  # Allow all TCP
            if udp_rule is False:
                logging.info("(SG) Adding " + str(ip_address) + " (UDP) to " + security_group_name + " security group")
                print "Adding " + str(ip_address) + " (UDP) to " + security_group_name + " security group"
                sg.authorize('udp', 0, 65535, str(ip_address) + "/32")  # Allow all UDP
            if icmp_rule is False:
                logging.info("(SG) Adding " + str(ip_address) + " (ICMP) to " + security_group_name + " security group")
                print "Adding " + str(ip_address) + " (ICMP) to " + security_group_name + " security group"
                sg.authorize('icmp', -1, -1, str(ip_address) + "/32")   # Allow all ICMP

    # If a security group does not exist for the user then create it
    if security_group_found is False:
        logging.info("(SG) Creating security group: %s : %s" % (security_group_name, ip_address))
        print "Creating security group: %s" % security_group_name
        security_group_description = "MAS DSE created on " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sg = conn.create_security_group(security_group_name, security_group_description)
        sg.authorize('tcp', 0, 65535, str(ip_address) + "/32")  # Allow all TCP
        sg.authorize('udp', 0, 65535, str(ip_address) + "/32")  # Allow all UDP
        sg.authorize('icmp', -1, -1, str(ip_address) + "/32")   # Allow all ICMP

    return c_security_groups


def empty_call_back(line):
    return False


def run_command(command, stderr_call_back=empty_call_back, stdout_call_back=empty_call_back, display=True):
    return_variable = False

    command_output = subprocess.Popen(command,
                                      shell=False,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

    def data_waiting(source):
        return select.select([source], [], [], 0) == ([source], [], [])

    while True:
        # Read from stderr and print any errors
        if data_waiting(command_output.stderr):
            command_stderr = command_output.stderr.readline()
            if len(command_stderr) > 0:
                if display:
                    print command_stderr,
                # Run custom stderr_call_back routine
                return_variable |= stderr_call_back(command_stderr)

        # Read from stdout
        if data_waiting(command_output.stdout):
            command_stdout = command_output.stdout.readline()
            # Stop if the end of stdout has been reached
            if not command_stdout:
                break
            else:
                if display:
                    print command_stdout,
                # Run custom stdout_call_back routine
                return_variable |= stdout_call_back(command_stdout)

        time.sleep(0.1)

    return return_variable

if __name__ == "__main__":
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

    # Create a logs directory in the vault directory if one does not exist
    if not os.path.exists(vault + "/logs"):
        os.makedirs(vault + "/logs")

    # Save a log to vault/logs/LaunchNotebookServer.log
    logging.basicConfig(filename=vault + "/logs/createami.log", format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logging.info("createami.py started")
    logging.info("Vault: %s" % vault)

    credentials_path, aws_access_key_id, aws_secret_access_key, user_name, key_pair_file, key_name = \
        read_credentials(vault)

    # Open connection to aws
    try:
        conn = boto.ec2.connect_to_region(ec2_region,
                                          aws_access_key_id=aws_access_key_id,
                                          aws_secret_access_key=aws_secret_access_key)
        logging.info("Created Connection = %s" % conn)
        print "Created Connection = %s" % conn
    except Exception, e:
        logging.info("There was an error connecting to AWS: %s" % e)
        sys.exit("There was an error connecting to AWS: %s" % e)

    # Make sure a security group exists for the user and their current ip address has been added
    security_groups = check_security_groups()

    reservation = conn.run_instances(
        ami_image_id,
        key_name=key_name,
        instance_type=instance_type,
        security_groups=security_groups)

    instance = reservation.instances[0]

    logging.info("Launched reservation %s with instance: %s" % (instance.id, reservation.id))
    print 'Launched reservation %s with instance: %s' % (instance.id, reservation.id)

    # TODO: make sure only once instance was started

    while not instance.state == 'running':
        logging.info("Waiting for instance (%s) state running. Current state: %s" % (instance.id, instance.state))
        print "%s Waiting for instance (%s) state running. Current state: %s" % (time.strftime('%H:%M:%S'),
                                                                                 instance.id, instance.state)
        time.sleep(10)
        instance.update()

    # Load the DSE Software
    ssh_command = ["ssh", "-i", key_pair_file, "%s@%s" % (ubuntu_login_id, instance.public_dns_name), "-o",
                   "StrictHostKeyChecking=no"]

    # ssh to the remote EC2 instance and echo True to verify that the ssh service is available
    test_ssh_available = ['echo', '"True"']

    # Function to parse the output of the test_ssh_available command
    def parse_test_ssh_available_response(response):
        logging.info("(PTSA) %s" % response.strip())

        # If the remote shell echos True then SSH is available on the remote EC2 instance
        if not response.find("True") == -1:
            logging.info("(PTSA) Found True: %s" % response.strip())
            return True

        return False

    while not run_command(ssh_command + test_ssh_available, stderr_call_back=parse_test_ssh_available_response,
                          stdout_call_back=parse_test_ssh_available_response):
        logging.info("Waiting for EC2 instance to finish booting up")
        print "Waiting for EC2 instance to finish booting up"
        time.sleep(10)

    copy_install_script = ["scp", "-i", key_pair_file, "-o", "StrictHostKeyChecking=no", os.getcwd() + "/install.sh",
                           "%s@%s:/tmp/" % (ubuntu_login_id, instance.public_dns_name)]

    run_command(copy_install_script, display=True)

    run_install_script = ["/bin/bash", "/tmp/install.sh"]

    run_command(ssh_command + run_install_script, display=True)

    #
    # Create AMI of the running instance
    #
    new_dse_ami_image_name = "%s_%s" % (dse_ami_image_name, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    logging.info("Creating %s from %s" % (new_dse_ami_image_name, instance.id))
    print "Creating %s from %s" % (new_dse_ami_image_name, instance.id)

    new_dse_ami_image_id = conn.create_image(instance.id, new_dse_ami_image_name)

    logging.info("New DSE AMI Image ID: %s" % new_dse_ami_image_id)

    new_dse_ami_image = conn.get_image(new_dse_ami_image_id)

    while not new_dse_ami_image.state == 'available':
        logging.info("Waiting for %s image (%s) state available. Current state: %s" % (new_dse_ami_image_name,
                                                                                       new_dse_ami_image.id,
                                                                                       new_dse_ami_image.state))
        print "%s Waiting for %s image (%s) state available. Current state: %s" % (time.strftime('%H:%M:%S'),
                                                                                   new_dse_ami_image_name,
                                                                                   new_dse_ami_image.id,
                                                                                   new_dse_ami_image.state)
        time.sleep(10)
        new_dse_ami_image.update()

    new_dse_ami_image.add_tag("source", "createami.py")
    new_dse_ami_image.add_tag("created", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    #
    # Delete the old dse_ami_image_name
    #
    logging.info("Deleting %s if it exists" % dse_ami_image_name)
    print "Deleting %s if it exists" % dse_ami_image_name

    old_dse_ami_image = conn.get_all_images(filters={'owner-id': ami_owner_id, 'name': dse_ami_image_name})

    # Attempt to delete dse_ami_image_name only if one AMI image is returned
    if len(old_dse_ami_image) == 1:
        logging.info("Found one %s! Deleting %s" % (dse_ami_image_name, old_dse_ami_image[0].id))
        print "Found one %s! Deleting %s" % (dse_ami_image_name, old_dse_ami_image[0].id)

        old_dse_ami_image[0].deregister(delete_snapshot=True)

    #
    # Copy the newly created image to dse_ami_image_name
    #
    logging.info("Copying %s (%s) to %s" % (new_dse_ami_image_name, new_dse_ami_image_id, dse_ami_image_name))
    print "Copying %s (%s) to %s" % (new_dse_ami_image_name, new_dse_ami_image_id, dse_ami_image_name)

    copy_image_dse_ami = conn.copy_image(ec2_region, new_dse_ami_image_id, name=dse_ami_image_name)
    dse_ami_image = conn.get_image(copy_image_dse_ami.image_id)

    while not dse_ami_image.state == 'available':
        logging.info("Waiting for %s image (%s) state available. Current state: %s" % (dse_ami_image_name,
                                                                                       dse_ami_image.id,
                                                                                       dse_ami_image.state))
        print "%s Waiting for %s image (%s) state available. Current state: %s" % (time.strftime('%H:%M:%S'),
                                                                                   dse_ami_image_name,
                                                                                   dse_ami_image.id,
                                                                                   dse_ami_image.state)
        time.sleep(10)
        dse_ami_image.update()

    #
    # Terminate the instance once the AMI has been created
    #
    instance.terminate()

    while not instance.state == 'terminated':
        logging.info("Waiting for instance (%s) state terminated. Current state: %s" % (instance.id, instance.state))
        print "%s Waiting for instance (%s) state terminated. Current state: %s" % (time.strftime('%H:%M:%S'),
                                                                                    instance.id, instance.state)
        time.sleep(10)
        instance.update()

    conn.close()

    #
    # Delete the old backups of dse_ami_image_name
    #
    logging.info("Deleting the old backups of %s" % dse_ami_image_name)
    print "Deleting the old backups of %s" % dse_ami_image_name

    backup_dse_ami_image = conn.get_all_images(filters={"owner-id": ami_owner_id, "tag:source": "createami.py"})

    logging.info("Found %s backups of %s. Max %s backups to keep." % (len(backup_dse_ami_image), dse_ami_image_name,
                                                                      number_backups_to_keep))
    print "Found %s backups of %s. Max %s backups to keep." % (len(backup_dse_ami_image), dse_ami_image_name,
                                                               number_backups_to_keep)

    if len(backup_dse_ami_image) > number_backups_to_keep:

        ami_created_timestamp = []

        # Get a list of created timestamps
        for b in backup_dse_ami_image:
            logging.info("Backup: %s Created: %s" % (b.name, b.tags["created"]))
            ami_created_timestamp.append(time.strptime(b.tags["created"], "%Y-%m-%d %H:%M:%S"))

        ami_created_timestamp.sort(reverse=True)
        logging.info("Deleting backups older than %s" % (time.strftime("%Y-%m-%d %H:%M:%S",
                                                                       ami_created_timestamp[number_backups_to_keep])))
        print "Deleting backups older than %s" % (time.strftime("%Y-%m-%d %H:%M:%S",
                                                                ami_created_timestamp[number_backups_to_keep]))

        # Delete backups older than number_backups_to_keep
        for b in backup_dse_ami_image:
            if time.strptime(b.tags["created"], "%Y-%m-%d %H:%M:%S") <= ami_created_timestamp[number_backups_to_keep]:
                logging.info("Deleting backup %s (%s)" % (b.name, b.tags["created"]))
                print "Deleting backup %s (%s)" % (b.name, b.tags["created"])
                b.deregister(delete_snapshot=True)
            else:
                logging.info("Keeping backup %s (%s)" % (b.name, b.tags["created"]))
                print "Keeping backup %s (%s)" % (b.name, b.tags["created"])

    logging.info("createami.py finished")
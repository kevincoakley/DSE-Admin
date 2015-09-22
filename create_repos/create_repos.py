#!/usr/bin/env python

import os
import csv
import github3
import argparse
from getpass import getpass, getuser
import sys
import logging
from ucsd_bigdata.vault import Vault

organization_name = "mas-dse"
course_directories = ["DSE200", "DSE210", "DSE201", "DSE220", "DSE230", "DSE203"]


def github_login():
    try:
        user = raw_input('GitHub username: ')
    except KeyboardInterrupt:
        user = getuser()

    password = getpass('GitHub password for {0}: '.format(user))

    # Obviously you could also prompt for an OAuth token
    if not (user and password):
        print("Cowardly refusing to login without a username and password.")
        sys.exit(1)

    return github3.login(user, password)


def create_team(organization, team_name):
    team = None

    while team is None:
        for t in organization.teams():
            if t.name == team_name:
                print "Team \"%s\" already exists" % team_name
                logging.info("Team \"%s\" already exists" % team_name)
                team = t

        if team is None:
            logging.info("Creating new team: %s" % team_name)
            team = organization.create_team(team_name)
            print "Team \"%s\" created" % team_name
            logging.info("Team \"%s\" created" % team_name)

    return team


def invite_member_to_team(team, member_name):
    if not team.is_member(member_name):
        logging.info("Adding member %s to team \"%s\"" % (member_name, team.name))
        team.invite(member_name)
        print "Member %s added to team \"%s\"" % (member_name, team.name)
        logging.info("Member %s added to team \"%s\"" % (member_name, team.name))
    else:
        print "Member %s is already in team \"%s\"" % (member_name, team.name)
        logging.info("Member %s is already in team \"%s\"" % (member_name, team.name))


def create_repository(organization, ucsd_username, year):
    repository = None

    while repository is None:
        for r in organization.repositories(type="private"):
            if str(r) == "%s/%s" % (organization_name, ucsd_username):
                print "Repository %s/%s already exists" % (organization_name, ucsd_username)
                logging.info("Repository %s/%s already exists" % (organization_name, ucsd_username))
                repository = r

        if repository is None:
            logging.info("Creating new repository: %s/%s" % (organization_name, ucsd_username))
            repository = organization.create_repository(ucsd_username, "DSE %s" % year,
                                                        private=True,
                                                        auto_init=True)
            print "Repository %s/%s created" % (organization_name, ucsd_username)
            logging.info("Repository %s/%s created" % (organization_name, ucsd_username))

            logging.info("Updating README.md")
            readme = repository.readme()
            readme.update("Added welcome message to README.md",
                          "%s\n========\n\nThis is your MAS-DSE Private GitHub Repository.\n\n"
                          "A directory has been created for each course.\n\n"
                          "See [https://mas-dse.github.io/startup/]"
                          "(https://mas-dse.github.io/startup/) for startup instructions." %
                          ucsd_username)
            logging.info("README.md Updated")

    return repository


def create_repository_folders(repo):
    logging.info("Creating course directories in the repository")
    for course_directory in course_directories:
        logging.info("Checking if the %s directory is in the repository" % course_directory)
        logging.info("Repository contents: %s" % repo.directory_contents("/"))

        if not any(directory[0] == course_directory for directory in repo.directory_contents("/")):
            logging.info("Creating %s in repository" % course_directory)
            repo.create_file("%s/README.md" % course_directory,
                             "Created %s/README.md" % course_directory,
                             "%s\n======\n\nCourse directory for %s" % (course_directory,
                                                                        course_directory))
        else:
            logging.info("The %s directory already exists in the repository" % course_directory)


def add_repository_to_team(team, repo):
    if team.has_repository(repo):
        print "Team \"%s\" already has access to %s" % (team.name, repo)
        logging.info("Team \"%s\" already has access to %s" % (team.name, repo))
    else:
        logging.info("Adding repository %s to team \"%s\"" % (repo, team.name))
        team.add_repository(repo)
        print "Repository %s added to team \"%s\"" % (repo, team.name)
        logging.info("Repository %s added to team \"%s\"" % (repo, team.name))


if __name__ == '__main__':
    # parse parameters
    parser = argparse.ArgumentParser(description="Create teams and private GitHub repositories "
                                                 "for Students",
                                     epilog="Example: ./create_repos.py -y 2014 -c csv_file")
    parser.add_argument("-y",
                        metavar="class_year",
                        dest="class_year",
                        help="Name of the class's team. Example: \"2014 Students\".",
                        default=None,
                        required=True)

    parser.add_argument("-c",
                        dest="csv_file",
                        metavar="csv_file",
                        help="Location of the user CSV file.",
                        required=True)

    parser.add_argument("-t",
                        dest="github_token",
                        metavar="github_token",
                        help="GitHub personal access token, used to bypass login for 2fa accounts.",
                        default=None,
                        required=False)

    args = vars(parser.parse_args())

    # Get the vault from ~/.vault or default to ~/Vault
    vault = Vault()

    # Create a logs directory in the vault directory if one does not exist
    if not os.path.exists(vault.path + "/logs"):
        os.makedirs(vault.path + "/logs")

    # Save a log to vault/logs/create_repos.log
    logging.basicConfig(filename=vault.path + "/logs/create_repos.log",
                        format='%(asctime)s %(message)s',
                        level=logging.INFO)

    logging.info("create_repos.py started")
    logging.info("CSV File: %s" % args['csv_file'])
    logging.info("Class Year: %s" % args['class_year'])

    # If the user specified a GitHub personal access token then skip asking for a username and
    # password to allow admins with two factor authentication enabled to run the script.
    if args["github_token"] is None:
        github = github_login()
    else:
        github = github3.login(token=args["github_token"])

    try:
        class_organization = github.organization(organization_name)
    except github3.exceptions.AuthenticationFailed:
        sys.exit("Invalid username or password")

    # Verify the organization was found
    if len(str(class_organization.name)) > 0:
        print "Found organization: %s" % class_organization.name
        logging.info("Found organization: %s" % class_organization.name)
    else:
        print "Organization %s not found" % organization_name
        logging.info("Organization %s not found" % organization_name)
        sys.exit()

    # Read CSV File into a list
    try:
        csv_reader = csv.reader(open(args['csv_file'], 'rU'), dialect=csv.excel_tab, delimiter=',')
        csv_users_list = list(csv_reader)
        logging.info("Contents of the CSV file %s:\n %s" % (args['csv_file'], csv_users_list))
    except Exception, e:
        logging.info("There was an error reading the CSV file %s: %s" % (args['csv_file'], e))
        sys.exit("There was an error reading the CSV file %s: %s" % (args['csv_file'], e))

    # If the class team does not exist then create it
    class_team = create_team(class_organization, "%s Students" % args["class_year"])

    # Process the student accounts
    for user_row in csv_users_list:
        # Add the student to the class team
        invite_member_to_team(class_team, user_row[1])

        # If the student team does not exist then create it
        student_team = create_team(class_organization, "%s %s" % (args["class_year"], user_row[0]))
        # Add the student to their student team
        invite_member_to_team(student_team, user_row[1])

        # If the student repository doesn't exist then create it
        student_repo = create_repository(class_organization, user_row[0], args["class_year"])

        # Create a directory for each DSE course using the course_directories list
        create_repository_folders(student_repo)

        # Add the student repository to the student team
        add_repository_to_team(student_team, student_repo)

    logging.info("create_repos.py finished")

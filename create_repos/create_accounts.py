#!/usr/bin/env python

import argparse
import csv
import github3
from getpass import getpass, getuser
import logging
import mechanize
import sys
import requests
import json

github_create_account_url = "https://github.com/join"

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


def create_github_account(login, email, password):
    # Create a Mechanized Browser
    br = mechanize.Browser()

    # Browser options
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)

    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) '
                                    'Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    # Open the github join page:
    br.open(github_create_account_url)

    # Select the 2rd form
    br.select_form(nr=1)

    # Complete the create account form
    br.form['user[login]'] = login
    br.form['user[email]'] = email
    br.form['user[password]'] = password

    br.submit()


def get_create_team(organization, team_name):
    team = None

    while team is None:
        for t in organization.teams():
            if t.name == team_name:
                print "Team \"%s\" already exists" % team_name
                logging.info("Team \"%s\" already exists" % team_name)
                team = t

        if team is None:
            logging.info("Creating new team: %s" % team_name)
            team = organization.create_team(team_name, permission="admin")
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


def create_repository(organization, username, year):
    repository = None

    while repository is None:
        for r in organization.repositories(type="private"):
            if str(r) == "%s/%s" % (organization_name, username):
                print "Repository %s/%s already exists" % (organization_name, username)
                logging.info("Repository %s/%s already exists" % (organization_name, username))
                repository = r

        if repository is None:
            logging.info("Creating new repository: %s/%s" % (organization_name, username))
            repository = organization.create_repository(username, "DSE %s" % year,
                                                        private=True,
                                                        auto_init=True)
            print "Repository %s/%s created" % (organization_name, username)
            logging.info("Repository %s/%s created" % (organization_name, username))

            logging.info("Updating README.md")
            readme = repository.readme()
            readme.update("Added welcome message to README.md",
                          "%s\n========\n\nThis is your MAS-DSE Private GitHub Repository.\n\n"
                          "A directory has been created for each course.\n\n"
                          "See [https://mas-dse.github.io/startup/]"
                          "(https://mas-dse.github.io/startup/) for startup instructions." %
                          username)
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


def add_member_as_collaborator(repo, username):
    if repo.is_collaborator(username):
        print "User \"%s\" is already a collaborator of %s" % (username, repo.name)
        logging.info("User \"%s\" is already a collaborator of  %s" % (username, repo.name))
    else:
        logging.info("Adding \"%s\" as a collaborator of \"%s\"" % (username, repo.name))
        repo.add_collaborator(username)
        print "User \"%s\" added as a collaborator of %s" % (username, repo.name)
        logging.info("User \"%s\" added as a collaborator of %s" % (username, repo.name))


def add_repository_to_team(team, repo):
    if team.has_repository(repo):
        print "Team \"%s\" already has access to %s" % (team.name, repo)
        logging.info("Team \"%s\" already has access to %s" % (team.name, repo))
    else:
        logging.info("Adding repository %s to team \"%s\"" % (repo, team.name))
        team.add_repository(repo)
        print "Repository %s added to team \"%s\"" % (repo, team.name)
        logging.info("Repository %s added to team \"%s\"" % (repo, team.name))


def accept_organization_invitation(username, password):
    # Accept the invitation to the mas-dse organization
    data = json.dumps({"state": "active"})

    r = requests.patch("https://api.github.com/user/memberships/orgs/mas-dse",
                       auth=(username, password),
                       data=data)

    if r.status_code == requests.codes.ok:
        print "User %s accepted invitation to the mas-dse organization" % username
        logging.info("User %s accepted invitation to the mas-dse organization" % username)
    else:
        print "User %s failed to accept invitation to the mas-dse organization: %s %s" % \
              (username, r.status_code, r.text)
        logging.info("User %s failed to accept invitation to the mas-dse organization: %s %s" %
                     (username, r.status_code, r.text))


def accept_repository_invitation(username, password):
    # Get the list of repository invitations
    r = requests.get("https://api.github.com/user/repository_invitations",
                     auth=(username, password))

    if r.status_code == requests.codes.ok:
        data = r.json()
        print "User %s got repository invitations" % username
        logging.info("User %s got repository invitations" % username)

        # Loop through all of the repository invitations and accept them all
        for i in range(len(data)):
            r = requests.patch(data[i]["url"], auth=(username, password))

            if r.status_code == 204:
                print "User %s accepted invitation to the %s repository" % \
                      (username, data[i]["repository"]["name"])
                logging.info("User %s accepted invitation to the %s repository" %
                             (username, data[i]["repository"]["name"]))
            else:
                print "User %s failed to accept invitation to the %s repository: %s %s" % \
                      (username, data[i]["repository"]["name"], r.status_code, r.text)
                logging.info("User %s failed to accept invitation to the %s repository: %s %s" %
                             (username, data[i]["repository"]["name"], r.status_code, r.text))
    else:
        print "User %s failed to get repository invitations: %s %s" % \
              (username, r.status_code, r.text)
        logging.info("User %s failed to get repository invitations: %s %s" %
                     (username, r.status_code, r.text))
        return None


if __name__ == '__main__':
    # Set the default encoding to utf8 due to issues with mechanize and urllib using str()
    reload(sys)
    sys.setdefaultencoding('utf8')

    # parse parameters
    parser = argparse.ArgumentParser(description="Create GitHub accounts for Students",
                                     epilog="Example: ./create_accounts.py -c csv_file")

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

    log_level = logging.INFO

    logging.basicConfig(level=log_level,
                        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s',
                        handlers=[logging.StreamHandler()])

    logging.info("create_accounts.py started")
    logging.info("CSV File: %s" % args['csv_file'])

    # Read CSV File into a list
    try:
        csv_reader = csv.reader(open(args['csv_file'], 'rU'), dialect=csv.excel_tab, delimiter=',')
        csv_users_list = list(csv_reader)
        logging.info("Contents of the CSV file %s:\n %s" % (args['csv_file'], csv_users_list))
    except Exception, e:
        logging.info("There was an error reading the CSV file %s: %s" % (args['csv_file'], e))
        sys.exit("There was an error reading the CSV file %s: %s" % (args['csv_file'], e))

    # If the user specified a GitHub personal access token then skip asking for a username and
    # password to allow admins with two factor authentication enabled to run the script.
    if args["github_token"] is None:
        github = github_login()
    else:
        github = github3.login(token=args["github_token"])

    try:
        # Get the class Organization object
        class_organization = github.organization(organization_name)
    except github3.exceptions.AuthenticationFailed:
        sys.exit("Invalid username or password")

    # If the class team does not exist then create it
    class_team = get_create_team(class_organization, "%s Students" % args["class_year"])

    # Process the student accounts
    for user_row in csv_users_list:

        email_username = user_row[0].split("@")[0]
        github_username = "%s-%s" % (organization_name, email_username)
        github_email = user_row[0]
        github_password = user_row[1]

        logging.info("%s,%s,%s,%s" % (email_username, github_username, github_email,
                                      github_password))

        # Create a Github Account
        create_github_account(github_username, github_email, github_password)

        # Add the student to the class team
        invite_member_to_team(class_team, github_username)

        # If the student repository doesn't exist then create it
        student_repo = create_repository(class_organization, email_username, args["class_year"])

        # Create a directory for each DSE course using the course_directories list
        create_repository_folders(student_repo)

        # Add the student as a collaborator
        add_member_as_collaborator(student_repo, github_username)

        # Get the Instructors Team object
        instructors_team = get_create_team(class_organization, "Instructors")

        # Add the student repository to the instructor team
        add_repository_to_team(instructors_team, student_repo)

        # Login as the student and accept Organization invitation
        accept_organization_invitation(github_username, github_password)

        # Login as the student and accept the Repository invitation
        accept_repository_invitation(github_username, github_password)

    logging.info("create_accounts.py finished")

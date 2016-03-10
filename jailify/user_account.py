#!/usr/bin/env python3
import sys
import os.path
import datetime
import subprocess

def add_group(jail, group):
    """Creates a group within the given jail.

    Args:
        jail (str): Current jail to make modification in.
        group (str): The name of the group that needs to be created.

    Returns:
        None
    """
    command = ('jexec', jail, 'pw', 'groupadd', group)
    do_command(command)


def add_user(jail, user, group, gecos, groups=["wheel"],
             skel_dir="/usr/share/skel", shell="/bin/tsch",
             passwd_method="random"):
    """Uses pw adduser to add a user to the current jail.

    Args:
        jail (str): Current jail to make modification in.
        user (str): Current user to add to the jail.
        group (str): The group to add the current user to.
        gecos (str): Personal information related to the user.
        groups (list): Other groups to potentially add the user to.
        skel_dir (str): Path to the directory that every user's directory
                        will be based off of.
        shell (str): Path to the default shell a user will be using.
        passwd_method (str): Type of password to be generated when account
                             has been successfully created.

    Returns:
        None
    """
    command = (
        'jexec',
        jail,
        'pw',
        'useradd',
        '-n', user,
        '-c', '"{}"'.format(gecos),
        '-g', group,
        '-G', ",".join(groups),
        '-m',
        '-k', skel_dir,
        '-s', shell,
        '-w', passwd_method
    )
    do_command(command)


def set_password_expiration(jail, user):
    """Sets the account expiration to 120 days after creation.

    Args:
        jail (str): The current jail to make the modification in.
        user (str): The user to set the password expiration date on.

    Returns:
        None
    """
    duration = 120
    exp_date = datetime.date.today() + datetime.timedelta(duration)
    exp_date = exp_date.strftime('%m-%b-%Y')
    command = ('jexec', jail, 'pw', 'usermod', '-p', exp_date, '-n', user)
    do_command(command)


def do_command(command):
    """Executes command and error handles when applicable.

    Args:
        command (tuple): The command that needs to be executed.

    Returns:
        None
    """
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        sys.exit(e.output)


def send_msg():
    """Uses information from adduser cmdline progrm to send
    a user mail that can be checked during their first login

    Args:
        None

    Returns:
        None
    """
    pass


def add_key(jail, user, key):
    """Places public key into authorized_keys inside the .ssh
    folder.

    Args:
        path_to_key (str): Path to the location where the pub key lives.
        jail (str): Current jail name we are working with.
        user (str): The use who will need the authorized_key updated.

    Returns:
        None
    """
    jail_root = "/usr/jail/"
    home_dir = "usr/home/"
    auth_key_path = ".ssh/authorized_keys"
    
    path_to_file = os.path.join(jail_root, jail, home_dir, user, auth_key_path)
    print("This the path to authorized_keys: {}".format(path_to_file))

    if os.path.isfile(path_to_file):
        with open(path_to_file, "a") as f:
            f.write(key)
    else:
        print("Error: {} does not exist.".format(path_to_file))


if __name__ == '__main__':
    #for testing....

    jail = "example"
    user_groups = ["test01", "test02", "test03", "test04"]
    user_names = ["test01", "test02", "test03", "test04"]
    user_gecos = ["test 01", "test 02", "test 03", "test 04"]
    user_keys = ["jsdahj01", "jksda02", "jasdjk03", "jkdakh04"]

    for user, group, gecos, key  in zip(user_names, user_groups, user_gecos, user_keys):
        print("Adding {} as a group.".format(group))
        add_group(jail, group)
        print("Adding {} as a user.".format(user))
        add_user(jail, user, group, gecos)
        print("Setting password expiration date for {}".format(user))
        set_password_expiration(jail, user)
        print("Placing ssh-keys for {}".format(user))
        add_key(jail, user, key)

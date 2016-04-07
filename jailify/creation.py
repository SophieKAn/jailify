#!/usr/bin/env python3
import re
import sys
import os.path
import ipaddress
import subprocess
from jailify.util import do_command
from jailify.util import do_command_with_return

def get_interface():
    """Finds the correct interface.

    Finds the lowest interface by using the command ifconfig then searching through
    the output for the non loopback interface.

    Args:
        None

    Returns:
        interface (str): correct interface
    """
    cmd = ('ifconfig') 
    output = do_command_with_return(cmd)

    interfaces = [i for i in re.findall(r'(^\S*):', output, re.M) if i != 'lo0']
    if(len(interfaces) == 1):
        return interfaces[0]
    else:
        print("Multiple interfaces detected. Aborting due to ambiguity.")
        sys.exit(1)

def check_name(jail_name):
    """Checks the desired jail name for availability.

    Checks the desired jail name by going through /etc/jail.conf line by line. If the
    first word in that line is the desired jail name then that jail already exists.

    Args:
        jail_name (str): desired jailname

    Returns:
        True: jail_name is a valid name for a jail
        False: jail_name is already taken and is an invalid name for a jail
    """
    with open('/etc/jail.conf', 'r') as jail_config:
        for line in jail_config:
            if line.startswith(jail_name):
                print("Error: {} already exists as a jail name".format(jail_name))
                return False
    return True

def get_latest_snapshot():
    """Finds the latest snapshot.

    Finds the latest snapshot by using a regular expression on the output of calling
    'zfs list -t snapshot'.

    Args:
        None

    Returns:
        latest_snapshot (str): a string of the name of the latest snapshot
    """
    cmd = ["zfs", "list", "-t", "snapshot"]
    zfs_output = do_command_with_return(cmd)

    snapshot_list = re.findall('(?<=@)\S*', str(zfs_output))
    latest_snapshot = snapshot_list[-1]
    return latest_snapshot

def get_lowest_ip():
    """Finds the next available ip address.

    Finds the next available ip address by searching through the /etc/jail.conf file.
    Then uses a regular expression find all ip addresses being used and stores the ip
    addresses in a sorted list. If the current ip + 1 is not in the list, that is the
    next lowest ip.

    Args:
        None

    Returns:
        A string that is the next available ip address
    """
    with open('/etc/jail.conf', 'r') as jail_config:
        jail_config = jail_config.read()

    ip_addrs = re.findall("(?<=ip4.addr = )(.*);", jail_config)

    ip_addrs.sort()
    for ip in ip_addrs:
        ip = ipaddress.IPv4Address(ip)
        if not (str(ip + 1) in ip_addrs):
            return str(ip + 1)
    return str(ip + 1)

def add_entry(ip_addr, jail_name, interface):
    """Opens /etc/jail.conf and appends the file to include an entry for the new jail.

    Args:
        ip_addr (str): the next available ip address. Found by get_lowest_ip().
        jail_name (str): the name for the jail that is being created.
        interface (str): the primary interface. Currently hardcoded to 'em0'.

    Returns:
        None
    """
    print("Adding entry to /etc/jail.conf")
    with open('/etc/jail.conf', 'a') as jail_file:
        jail_description = "\n{} {{\n    interface = \"{}\";\n    ip4.addr = {};\n}}\n".format(jail_name, interface, ip_addr)
        jail_file.write(jail_description)

def create_fstab_file(jail_name):
    """Creates an empty file in the /etc/ directory called fstab.jail_name where jail_name is an argument
    Argument:
        jail_name (str): the name for the jail that is being created

    Returns:
        None
    """
    print("Creating fstab file")
    path = "/etc/fstab."
    fstab_path = path + jail_name
    fstab_file = open(fstab_path, 'w')
    fstab_file.close()

def clone_base_jail(snapshot, jail_name):
    """Clones the base jail.

    Arguments:
        snapshot (str): the latest snapshot. Found by get_latest_snapshot.
        jail_name (str): the name for the jail that is being created.

    Returns:
        None
    """
    path = "zroot/jail/"
    jail_version = ".base10.2x64"
    snapshot_path = "{}{}@{}".format(path, jail_version, snapshot)
    jail_path = os.path.join(path, jail_name)

    cmd = ["zfs", "clone", snapshot_path, jail_path]
    do_command(cmd)
    print("Success cloning base jail")

def start_jail(jail_name):
    """Starts jail by running 'service jail start jail_name' where jail_name is an argument.

    Arguments:
        jail_name (str): the name for the jail that is being created.

    Returns:
        None
    """
    cmd = ["service", "jail", "start", jail_name]
    do_command(cmd)

if __name__ == '__main__':
    lowest_ip = get_lowest_ip()
    jail_name = str(sys.argv[1]) #extract.py - teamname
    interface = get_interface()
    snapshot = get_latest_snapshot()
    if check_name(jail_name):
        add_entry(lowest_ip, jail_name, interface)
        create_fstab_file(jail_name)
        clone_base_jail(snapshot, jail_name)
        start_jail(jail_name)
    else:
        sys.exit(1)
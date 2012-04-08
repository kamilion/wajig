# This file is part of wajig.  The copyright file is at debian/copyright.

"""Keep track of changes between UPDATEs"""

import os
import tempfile
import socket
import datetime
import time

import apt
import apt_pkg

import perform

#------------------------------------------------------------------------
#
# LOCATIONS
#
# init_dir
#
#       Wajig can be run on several machines sharing the same home
#       directories (often through NFS) so we need to have host specific
#       status files. Make sure the directories exist.
#
#------------------------------------------------------------------------
init_dir = os.path.expanduser("~/.wajig/") + socket.gethostname()
if not os.path.exists(init_dir):
    os.makedirs(init_dir)
#
# Temporarily, remove old files from .wajig
# After a few versions remove this code.
#
tmp_dir = os.path.expanduser("~/.wajig")
if os.path.exists(tmp_dir + "/Available"):
    os.rename(tmp_dir + "/Available", init_dir + "/Available")
if os.path.exists(tmp_dir + "/Available.prv"):
    os.rename(tmp_dir + "/Available.prv", init_dir + "/Available.prv")
if os.path.exists(tmp_dir + "/Installed"):
    os.rename(tmp_dir + "/Installed", init_dir + "/Installed")

# 100104 Remove any old tmp files. Bug#563573
perform.execute("rm -f " + init_dir + "/tmp*")

# TODO 23 Aug 2003
#
# Perhaps the only file that wajig needs to cache itself is
# Available.prv - the other two can be generated dynamically.
# Installed is now like this. Available can be done.
# This would mean essentially half the space usage (Installed
# is quite small at 30K, while Available and Available.prv
# were 280K). This is significant for a user who manages
# many hosts.
#
# If this is the case, then don't worry about creating a host
# subdirectory in ~/.wajig.  Simply use host in filename,
# unless init_dir is used elsewhere?????? Perhaps keep as folder
# since tempfiles are created there.
#
# TODO Work to use bzip2 files for available and previous.
# Then bunzip2 to temporary files when needed!
# Disk usage goes from 274K to 83K.
available_file = init_dir + "/Available"
previous_file  = init_dir + "/Available.prv"

# removes a no-longer-used log file
# this code should go away after Debian 7.0 is released
log_file = init_dir + "/Log"
if os.path.exists(log_file):
    os.remove(log_file)

# Set the temporary directory to the init_dir.
# Large files are not generally written there so should be okay.
tempfile.tempdir = init_dir


def update_available(noreport=False):
    """Generate current list of available packages, backing up the old list.

    noreport    If set, do not report on the number of packages.
    """

    if not os.path.exists(available_file):
        f = open(available_file, "w")
        f.close()

    temporary_file = tempfile.mkstemp()[1]

    os.rename(available_file, temporary_file)
    command = "apt-cache dumpavail " +\
              "| egrep '^(Package|Version):' " +\
              "| tr '\n' ' '" +\
              "| perl -p -e 's|Package: |\n|g; s|Version: ||g'" +\
              "| sort -k 1b,1 | tail -n +2 | sed 's| $||' > " + available_file
    # Use langC in the following since it uses a grep.
    perform.execute(command, langC=True)  # root is not required.
    os.rename(temporary_file, previous_file)

    available_packages = len(open(available_file).readlines())
    previous_packages = len(open(previous_file).readlines())
    diff = available_packages - previous_packages

    # 090425 Use langC=True to work with change from coreutils 6.10 to 7.2
    command = "join -v 1 -t' '  {0} {1} | wc -l"
    command = command.format(available_file, previous_file)
    newest = perform.execute(command, pipe=True, langC=True)
    newest = newest.readlines()[0].strip()

    if not noreport:
        if diff < 0:
            direction = str(0 - diff) + " down on"
        elif diff == 0:
            direction = "the same as"
        else:
            direction = str(diff) + " up on"
        print("This is " + direction + " the previous count", end=' ')
        print("with " + newest + " new", end=' ')
        if newest == "1":
            print("package.")
        else:
            print("packages.")


def gen_installed_command_str():
    "Generate command to list installed packages and their status."
    command = "cat /var/lib/dpkg/status | " +\
              "egrep '^(Package|Status|Version):' | " +\
              "awk '/^Package: / {pkg=$2} " +\
              "     /^Status: / {s1=$2;s2=$3;s3=$4}" +\
              "     /^Version: / {print pkg,$2,s1,s2,s3}' | " +\
              "grep 'ok installed' | awk '{print $1,$2}' | sort -k 1b,1"
    return command


def count_upgrades():
    "Return as a string the number of new upgrades since last update."
    ifile = tempfile.mkstemp()[1]
    # Use langC in the following since it uses a grep.
    perform.execute(gen_installed_command_str() + " > " + ifile, langC=True)
    command = "join " + previous_file + " " + available_file + " |" +\
              "awk '$2 != $3 {print}' | sort -k 1b,1 | join - " + ifile + " |" +\
              "awk '$4 != $3 {print}' | wc -l | awk '{print $1}' "
    # 090425 Use langC=True to work with change from coreutils 6.10 to 7.2
    count = perform.execute(command, pipe=True,
            langC=True).read().split()[0]
    if os.path.exists(ifile):
        os.remove(ifile)
    return count


def reset_files():
    if os.path.exists(available_file):
        os.remove(available_file)
    if os.path.exists(previous_file):
        os.remove(previous_file)
    update_available(noreport=True)


def ensure_initialised():
    "Create the init_dir and files if they don't exist."
    if not os.path.exists(available_file):
        reset_files()


def backup_before_upgrade(packages, distupgrade=False):
    """Backup packages before a (dist)upgrade.

     This optional functionality helps recovery in case of trouble caused
     by the newly-installed packages. The packages are by default stored
     in a directory named like  ~/.wajig/hostname/backups/2010-09-21_09h21."""

    date = time.strftime("%Y-%m-%d_%Hh%M", time.localtime())
    target = os.path.join(init_dir, "backups", date)
    if not os.path.exists(target):
        os.makedirs(target)
    os.chdir(target)
    print("The packages will saved in", target)
    for package in packages:
        command = "fakeroot -u dpkg-repack " + package
        perform.execute(command)

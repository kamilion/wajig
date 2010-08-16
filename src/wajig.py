#!/usr/bin/env python
#
# WAJIG - Debian Command Line System Administrator
#
# Copyright (c) Graham.Williams@togaware.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version. See the file LICENSE.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#

########################################################################
# Standard python modules
#
import getopt
import os
import sys
import re
import tempfile

########################################################################
# Wajig modules
#
import documentation
import commands
import changes
import perform

########################################################################
# Global Variables
#
pause = False
interactive = False  # Set to true for interactive command line
match_commands = []  # For interactive command line completion

#------------------------------------------------------------------------
#
# SUPPORT METHODS
#
#------------------------------------------------------------------------

def requires_no_args(command, args, test=False):
    if len(args) > 1:
        if not test:
            message = "no further arguments"
            print "WaJIG Error: " + command.upper() + " requires " + message
            finishup(1)
        return False
    return True


def requires_one_arg(command, args, message=False):
    if len(args) != 2:
        if message:  # checks if this is a unit test
            print "WaJIG Error: " + command.upper() + " requires " + message
            finishup(1)
        return False
    return True


def requires_two_args(command, args, message=False):
    if len(args) != 3:
        if message:  # checks if this is a unit test
            print "WaJIG Error: " + command.upper() + " requires " + message
            finishup(1)
        return False
    return True


def requires_opt_arg(command, args, message=False):
    if len(args) > 2:
        if message:  # checks if this is a unit test
            print "WaJIG Error: " + command.upper() +\
                  " has one optional arg: " + message
            finishup(1)
        return False
    return True


def requires_args(command, args, required=False):
    if len(args) == 1:
        if required:  # checks if this is a unit test
            print "WaJIG Error: {0} requires {1}".\
                   format(command.upper(), required)
            finishup(1)
        return False
    return True


def requires_package(package, path, test=False):
    if not os.path.exists(path):
        if not test:
            print 'The "' + package + '" package does not appear to be installed.'
            print 'Consider installing it with "wajig install ' + package + '".'
            finishup(1)
        return False
    return True


def finishup(code=0):
    global pause
    if pause:
        print "Press Enter to continue...",
        sys.stdin.readline()
    if not interactive:
        sys.exit(code)


def print_help(command, args, verbose=False, exit=False):
    if   command == "doc" or command == "docs" or command == "documentation":
        requires_no_args(command, args)
        verbose = 2
        documentation.help(verbose)
        if exit:
            finishup(0)
    elif command == "help":
        requires_no_args(command, args)
        documentation.help(verbose)
        if exit:
            finishup(0)


#------------------------------------------------------------------------
#
# INTERACTIVE COMMAND LINE
#
#-----------------------------------------------------------------------
def list_commands():
    f = os.popen('wajig commands', 'r')
    lines = f.readlines()
    command_patt = r'^ ([a-z][a-z-]*) '
    command_patt_r = re.compile(command_patt)
    cmds = []
    for l in lines:
        mo = command_patt_r.search(l)
        if mo == None:
            continue
        # a "-" in completion seems to start strings from beginning?
        #cmds += [re.sub('-', '', mo.group(1))]
        cmds += [mo.group(1)]
    return cmds


def wajig_completer(text, state):
    """The start of a completer function. Very rough so far."""
    #
    # Check first that we are completing just the first word.
    # Otherwise do not perform any completion.
    #
    import readline  # To get it in scope.
    current = readline.get_line_buffer()
    if len(current.split()) > 1 or current[-1] == ' ':
        return None
    #
    # Complete the command.
    #
    global match_commands  # List of cached matching commands
    n = len(text)
    word = None
    if state == 0:
        match_commands = []
        for w in all_commands:
            if text == w[:n]:
                match_commands += [w]
    if state < len(match_commands):
        return match_commands[state]
    return None


def interactive_shell():
    global all_commands
    global interactive
    interactive = True
    try:
        import readline
        readline.parse_and_bind("tab: complete")
        readline.set_completer(wajig_completer)
        # Allow "-" in command names.
        readline.set_completer_delims(readline.
                                      get_completer_delims().
                                      replace("-", ""))
        all_commands = list_commands()
    except:
        pass
    prompt = "JIG> "
    while True:
        try:
            cmdline = raw_input(prompt)
        except:
            print ""
            return
        cmd = cmdline.split()
        if cmd:
            command = re.sub('-|_|/', '', cmd[0].lower())
        else:
            command = ""
        if command in ("exit", "quit", "bye"):
            return
        elif command in ("doc", "docs", "documentation", "help"):
            print_help(command, cmd)
        elif cmd:
            select_command(command, cmd, False, False)

#------------------------------------------------------------------------
#
# MAIN PROGRAM
#
#------------------------------------------------------------------------

def main():
    global pause
    global yes
    global noauth
    #
    # Remove commas and insert the arguments appropriately.
    #
    oldargv = sys.argv
    sys.argv = oldargv[0:2]
    for i in range(2, len(oldargv)):
        sys.argv += oldargv[i].split(",")

    try:
        sopts = "dhnpqstvy"
        lopts = ["debug", "help", "pause", "quiet", "simulate", "teaching",
                 "verbose=", "version", "yes", "noauth"]
        opts, args = getopt.getopt(sys.argv[1:], sopts, lopts)
    except getopt.error, e:
        print e
        documentation.usage()
        finishup(2)

    simulate = False
    teaching = False
    verbose = 0
    debug = False
    yes = ""
    noauth = ""
    #
    # Action the command line options
    #
    for o, a in opts:
        if o in ("-h", "--help"):
            documentation.usage()
            finishup()
        elif o in ("-d", "--debug"):
            debug = True
        elif o in ("-p", "--pause"):
            pause = True
            perform.pause = True
        elif o in ("-q", "--quiet"):
            perform.set_quiet()
        elif o in ("-s", "--simulate"):
            simulate = True
            perform.set_simulate(simulate)
        elif o in ("-t", "--teaching"):
            teaching = True
            perform.set_teaching_level(teaching)
        elif o in ("-y", "--yes"):
            yes = " --yes "
        # The --force-yes is a dangerous option that will cause apt to
        # continue without prompting if it is doing something
        # potentially harmful. It should not be used except in very
        # special situations.  Using force-yes can potentially destroy
        # your system! Configuration Item: APT::Get::force-yes.
        # elif o in ("-Y", "--force-yes"):
        #    yes = " --yes --force-yes"
        elif o in ("-n", "--noauth"):
            noauth = " --allow-unauthenticated "
        elif o == "-v":
            verbose = verbose + 1
            commands.set_verbosity_level(verbose)
        elif o == "--verbose":
            verbose = int(a)
            commands.set_verbosity_level(verbose)
        elif o == "--version":
            documentation.version()
            finishup()

    #
    # NO ARGS => INTERACTIVE COMMAND LINE
    #
    #   Run interactive shell with optional readline support
    #   Returns from inside the IF
    #
    if len(args) == 0:
        interactive_shell()
        return
    #
    # Process the command. Lowercase it so that we allow any case
    # for commands and allow hyphens and underscores and slash.
    #
    # Need to check for install/sarge-backport and not convert the
    # part after the / (Bug##350944)
    #
    slash = args[0].find("/")
    if slash == -1:
        command = re.sub('-|_|/', '', args[0].lower())
    else:
        command = re.sub('-|_|/', '', args[0][:slash].lower()) +\
                  args[0][slash + 1:]

    # 081222 remove any commas - this makes it easier to copy and
    # paste from the security status email, for example.

    args = filter(lambda x: x != "", args)

    # Provide help up front - don't need to initialise the system to give help

    print_help(command, args, verbose, exit=True)
    #
    # Before we do any other command make sure the right files exist.
    #
    changes.ensure_initialised()
    #
    # Catch exceptions and ignore them, for end users.
    # Check for sys.exit (SystemExit exceptions) and return code.
    #
    if debug:
        select_command(command, args, verbose, teaching)
    else:
        try:
            select_command(command, args, verbose, teaching)
        except SystemExit, e:
            sys.exit(e)
        except:
            # print "Exiting...."
            None
    finishup(0)


def select_command(command, args, verbose, teaching):
    """Select the appropriate command and execute it.

    This function was separated out of the main so that I could wrap
    it up with exception handling.
    """
    result = 0
    changes.start_log()
    if command in ["addcdrom", "cdromadd"]:
        if requires_no_args(command, args):
            perform.execute("apt-cdrom add", root=True)

    elif command in ["autoalts", "autoalternatives"]:
        if requires_one_arg(command, args, "name alternative to set as auto"):
            perform.execute("update-alternatives --auto " + args[1], root=True)

    elif command == "autodownload":
        if requires_no_args(command, args):
            if verbose > 0:
                commands.do_update()
                filter_str = ""
            else:
                commands.do_update(quiet=True)
                filter_str = '| egrep -v "(http|ftp)"'
            perform.execute("apt-get --download-only --show-upgraded " +\
                            "--assume-yes dist-upgrade " + filter_str,
                            root=True)
            commands.do_describe_new()
            commands.do_newupgrades()

    elif command == "autoclean":
        if requires_no_args(command, args):
            perform.execute("apt-get autoclean", root=True)

    elif command == "autoinstall":
        if requires_args(command, args, "a list of package names"):
            command = "apt-get install --assume-yes " + noauth + " " +\
                      perform.concat(args[1:])
            perform.execute(command, root=True)

    elif command == "autoremove":
        if requires_no_args(command, args):
            perform.execute("apt-get autoremove", root=True)

    elif command in ["available", "avail"]:
        if requires_args(command, args, "a list of packages"):
            perform.execute("apt-cache policy " + perform.concat(args[1:]))

    elif command in ["bug", "bugs", "reportbug"]:
        if requires_one_arg(command, args, "a single named package"):
            if requires_package("reportbug", "/usr/bin/reportbug"):
                # 090430 Specify bts=debian since ubuntu not working at present
                perform.execute("reportbug --bts=debian " + args[1])

    elif command == "build":
        if requires_args(command, args, "a list of package names"):
            if requires_package("fakeroot", "/usr/bin/fakeroot"):
                # First make sure dependencies are met
                result = perform.execute("apt-get build-dep " +
                                         perform.concat(args[1:]), root=True)
                if not result:
                    perform.execute("fakeroot " + "apt-get source -b " +
                                    perform.concat(args[1:]))

    elif command == "builddepend":
        if requires_args(command, args, "a list of package names"):
            perform.execute("apt-get build-dep " + perform.concat(args[1:]),
                            root=True)

    elif command == "changelog":
        if requires_args(command, args, "a list of packages"):
            commands.do_changelog(args[1:])

    elif command == "clean":
        if requires_no_args(command, args):
            perform.execute("apt-get clean", root=True)

    elif command == "contents":
        if requires_one_arg(command, args, "a filename"):
            perform.execute("dpkg --contents " + args[1])

    elif command == "dailyupgrade":
        if requires_no_args(command, args):
            commands.do_update()
            perform.execute("apt-get --show-upgraded dist-upgrade", root=True)

    elif command == "dependents":
        if requires_one_arg(command, args, "package name"):
            commands.do_dependents(args[1])

    elif command == "describe":
        if requires_args(command, args, "a list of packages"):
            commands.do_describe(args[1:])

    elif command in ["describenew", "newdescribe"]:
        if requires_no_args(command, args):
            commands.do_describe_new()

    elif command in ["detail", "details", "show"]:
        if requires_args(command, args, "a list of packages or package file"):
            verbose = 2
            commands.set_verbosity_level(verbose)
            commands.do_describe(args[1:])

    elif command in ["detailnew", "newdetail"]:
        if requires_no_args(command, args):
            verbose = 2
            commands.set_verbosity_level(verbose)
            commands.do_describe_new()

    elif command == "distupgrade":
        if requires_opt_arg(command, args,
                            "the distribution to upgrade to"):
            cmd = "apt-get -u %s %s " % (yes, noauth)
            if len(args) == 2:
                cmd += "-t " + args[1] + " "
            cmd += "dist-upgrade"
            perform.execute(cmd, root=True)

    elif command == "download":
        if requires_args(command, args, "a list of packages"):
            pkgs = args[1:]
            if len(pkgs) == 1 and pkgs[0] == "-":
                stripped = [x.strip() for x in sys.stdin.readlines()]
                joined = str.join(stripped)
                pkgs = joined.split()
            elif len(pkgs) == 2 and pkgs[0] == "-f":
                stripped = [x.strip() for x in open(pkgs[1]).readlines()]
                joined = str.join(stripped)
                pkgs = joined.split()
            #
            # Print message here since no messages are printed for the command.
            #
            print "Packages being downloaded to /var/cache/apt/archives..."
            #
            # Do the download, non-interactively (--quiet),
            # and force download for already installed packages (--reinstall)
            #
            perform.execute("apt-get --quiet=2 --reinstall " +
                            "--download-only install " +
                            perform.concat(pkgs),
                            root=True)

    elif command in ["editsources", "setup"]:
        if requires_no_args(command, args):
            # if requires_package("base-config", "/usr/sbin/apt-setup"):
            #    perform.execute("apt-setup", root=True)
            perform.execute("editor /etc/apt/sources.list", root=True)

    elif command == "extract":
        if requires_two_args(command, args,
                             "a filename and directory to extract into"):
            perform.execute("dpkg --extract " + args[1] + " " + args[2])

    elif command in ["filedownload", "downloadfile"]:
        if requires_one_arg(command, args,
        "a file name containing list of packages"):
            stripped = [x.strip() for x in open(args[1]).readlines()]
            pkgs = str.join(stripped)
            perform.execute("apt-get --download-only install " + pkgs, root=True)

    elif command in ["fileinstall", "installfile"]:
        if requires_one_arg(command, args,
        "a file name containing list of packages"):
            stripped = [x.strip() for x in open(args[1]).readlines()]
            pkgs = str.join(stripped)
            perform.execute("apt-get install " + pkgs, root=True)

    elif command in ["fileremove", "removefile"]:
        if requires_one_arg(command, args,
        "a file name containing list of packages"):
            stripped = [x.strip() for x in open(args[1]).readlines()]
            pkgs = str.join(stripped)
            perform.execute("apt-get remove " + pkgs, root=True)

    elif command in ["findfile", "locate"]:
        if requires_one_arg(command, args, "a file name"):
            perform.execute("dpkg --search " + args[1])

    elif command in ["findpkg", "unofficial"]:
        if requires_one_arg(command, args, "a package name"):
            commands.do_findpkg(args[1])

    elif command == "fixconfigure":
        if requires_no_args(command, args):
            perform.execute("dpkg --configure -a", root=True)

    elif command == "fixinstall":
        if requires_no_args(command, args):
            perform.execute("apt-get --fix-broken install", root=True)

    elif command == "fixmissing":
        if requires_no_args(command, args):
            perform.execute("apt-get --fix-missing upgrade", root=True)

    elif command == "force":
        if requires_args(command, args, "a package name"):
            commands.do_force(args[1:])

    elif command == "geturl":
        if requires_one_arg(command, args, "a package name"):
            # Not yet quite working
            perform.execute("/usr/lib/apt-move/fetch -t " + args[1], root=True)

    elif command == "hold":
        if requires_args(command, args, "a list of packages to place on hold"):
            commands.do_hold(args[1:])
            # TODO Perhaps I can use map to "execute" over each package

    elif command == "info":
        if requires_one_arg(command, args, "a filename"):
            perform.execute("dpkg --info " + args[1])

    elif command == "init":
        if requires_no_args(command, args):
            changes.reset_files()

    elif command in ["install", "isntall"]:
        #
        # Okay, so I'm sometimes dyslexic :-)
        #
        if requires_args(command, args,
                         "a list of packages, .deb files, or url"):
            commands.do_install(args[1:], noauth)

    elif command in ["installr", "recommended"]:
        if requires_args(command, args, "a list of packages"):
            commands.do_install_suggest(args[1:], "Recommends")

    elif command == "installrs":
        if requires_args(command, args, "a list of packages"):
            commands.do_install_suggest(args[1:], "Both")

    elif command in ["installs", "suggested"]:
        if requires_args(command, args, "a list of packages"):
            commands.do_install_suggest(args[1:], "Suggests")

    elif re.compile(r'install.*').match(command):
        # For example: install/unsable
        if requires_args(command, args,
                         "a list of packages, .deb files, or url"):
            command = "apt-get --target-release %s install %s" % \
                  (re.compile(r'install').sub("", command),
                   perform.concat(args[1:]))
            perform.execute(command, root=True)

    elif command == "integrity":
        if requires_no_args(command, args):
            perform.execute("debsums -s -a")

    elif command == "large":
        commands.do_size(args[1:], 10000)

    elif command == "lastupdate":
        if requires_no_args(command, args):
            perform.execute("/bin/ls -l --full-time " +
                            changes.available_file +
                            " 2>/dev/null |awk '{printf \"Last update was " +
                            "%s %s %s\\n\"" +
                            ", $6, $7, $8}' | sed 's|\.000000000||'")

    elif command in ["list", "listwide"]:
        if requires_opt_arg(command, args, "string to filter on"):
            cmd = ""
            if command == "listwide":
                cmd += "COLUMNS=200 "
            cmd += "dpkg --list '*' | grep -v 'no description avail'"
            if len(args) > 1:
                cmd += " | egrep '" + args[1] + "' | sort -k 1b,1"
            if command == "listwide":
                cmd += "| sed 's|   *|  |g'"
            perform.execute(cmd)

    elif command == "listall":
        if requires_opt_arg(command, args, "string to filter on"):
            cmd = "apt-cache dumpavail |" +\
                            "egrep \"^(Package|Description): \" |" +\
                            "awk '/^Package: /{pkg=$2} /^Description: /" +\
                                 "{printf(\"%-24s %s\\n\", pkg," +\
                                 "substr($0,13))}' |" +\
                            "sort -u -k 1b,1"
            if len(args) == 2:
                cmd = cmd + " | grep '" + args[1] + "'"
            perform.execute(cmd)

    elif command in ["listalts", "listalternatives"]:
        if requires_no_args(command, args):
            perform.execute("ls /etc/alternatives/ | " +\
                            "egrep -v '(\.1|\.1\.gz|\.8|\.8\.gz|README)$'")

    elif command == "listcache":
        if requires_opt_arg(command, args, "string to filter on"):
            cmd = "printf 'Found %d files %s in the cache.\n\n'\
            $(ls /var/cache/apt/archives/ | wc -l) \
            $(ls -sh /var/cache/apt/archives/ | head -1 | awk '{print $2}')"
            perform.execute(cmd)
            cmd = "ls /var/cache/apt/archives/"
            if len(args) == 2:
                cmd = cmd + " | grep '" + args[1] + "'"
            cmd += "; echo"
            perform.execute(cmd)

    elif command in ["listcommands", "commands"]:
        if requires_no_args(command, args):
            documentation.help(verbose)

    elif command == "listdaemons":
        if requires_no_args(command, args):
            perform.execute("printf 'Found %d daemons in /etc/init.d.\n\n'\
            $(ls /etc/init.d/ | \
            egrep -v '(~$|README|-(old|dist)|\.[0-9]*$)' | wc -l)")
            perform.execute("ls /etc/init.d/ | \
            egrep -v '(~$|README|-(old|dist)|\.[0-9]*$)' |\
            pr --columns=3 --omit-header")

    elif command == "listfiles":
        if requires_one_arg(command, args,
                            "the name of a single Debian package or deb file"):
            if re.match(".*\.deb$", args[1]):
                perform.execute("dpkg --contents " + args[1])
            else:
                perform.execute("dpkg --listfiles " + args[1])

    elif command == "listsection":
        if requires_one_arg(command, args, "the name of a Debian Section." +
                            "\nUse the LIST-SECTIONS command for a list " +
                            "of Debian Sections."):
            commands.do_listsection(args[1])

    elif command == "listsections":
        if requires_no_args(command, args):
            commands.do_listsections()

    elif command == "listhold":
        if requires_no_args(command, args):
            perform.execute("dpkg --get-selections | egrep 'hold$' | cut -f1")

    elif command == "listinstalled":
        if requires_opt_arg(command, args, "string to filter on"):
            commands.do_listinstalled(args[1:])

    elif command == "listlog":
        if requires_opt_arg(command, args, "string to filter on"):
            cmd = "cat " + changes.log_file + "| sed 's|T| |'"
            if len(args) == 2:
                cmd = cmd + " | grep '" + args[1] + "'"
            perform.execute(cmd)

    elif command == "listnames":
        # pdb.set_trace()
        if requires_opt_arg(command, args, "at most one argument"):
            result = commands.do_listnames(args[1:])

    elif command == "listscripts":
        if requires_one_arg(command, args, "a package name or deb file"):
            result = commands.do_listscripts(args[1])

    elif command == "liststatus":
        if requires_opt_arg(command, args, "package name"):
            cmd = "COLUMNS=400 "
            cmd += "dpkg --list '*' | grep -v 'no description avail'"
            cmd += " | awk '{print $1,$2}'"
            if len(args) > 1:
                cmd += " | egrep '" + args[1] + "' | sort -k 1b,1"
            perform.execute(cmd)

    elif command == "localdistupgrade":
        if requires_no_args(command, args):
            perform.execute("apt-get --no-download --ignore-missing " +
                            "--show-upgraded dist-upgrade", root=True)

    elif command == "localupgrade":
        if requires_no_args(command, args):
            perform.execute("apt-get --no-download --ignore-missing " \
                            + "--show-upgraded upgrade", root=True)

    elif command == "moo":
        perform.execute("apt-get moo")

    elif command == "madison":
        perform.execute("apt-cache madison " + perform.concat(args[1:]))

    elif command == "move":
        if requires_no_args(command, args):
            perform.execute("apt-move update", root=True)
            # Then clean out the cached archive.
            perform.execute("apt-get clean", root=True)

    elif command == "new":
        if requires_opt_arg(command, args, "whether to INSTALL the new pkgs"):
            if len(args) == 1:
                commands.do_describe_new()
            elif args[1].lower() == "install":
                commands.do_describe_new(install=True)
            else:
                print "WaJIG Error: NEW only accepts optional " +\
                      "argument INSTALL"
                finishup(1)
                return False

    elif command == "news":
        if requires_args(command, args, "a list of packages"):
            if requires_package("lynx", "/usr/bin/lynx"):
                commands.do_news(args[1:])

    elif command in ["newupgrades", "newupgrade"]:
        if requires_opt_arg(command, args, "whether to INSTALL upgraded pkgs"):
            if len(args) == 1:
                commands.do_newupgrades()
            elif args[1].lower() == "install":
                commands.do_newupgrades(install=True)
            else:
                print "WaJIG Error: NEWUPGRADES only accepts " +\
                      "optional argument INSTALL"
                finishup(1)
                return False

    elif command == "nonfree":
        if requires_no_args(command, args):
            if requires_package("vrms", "/usr/bin/vrms"):
                perform.execute("vrms")

    elif command in ["orphans", "listorphans"]:
        if requires_no_args(command, args):
            if requires_package("deborphan", "/usr/bin/deborphan"):
                perform.execute("deborphan")

    elif command == "policy":
        perform.execute("apt-cache policy " + perform.concat(args[1:]))

    elif command == "purge":
        if requires_args(command, args, "a list of packages"):
            perform.execute("dpkg --purge " + perform.concat(args[1:]), root=True)

    elif command == "purgedepend":
        if requires_one_arg(command, args, "a single package"):
            # Bug#579419 - this is more efficient than do_removedepend 
            perform.execute("apt-get remove --purge --auto-remove " + args[1], root=True)
            # commands.do_removedepend(args[1], purge=True)

    elif command == "purgeorphans":
        #
        # Deborphans does not require root, but dpkg does.
        # So build up the orphans list first, then apss that to dpkg.
        #
        if requires_no_args(command, args):
            if requires_package("deborphan", "/usr/bin/deborphan"):
                pkgs = ""
                for p in perform.execute("deborphan", pipe=True):
                    pkgs += " " + p.strip()
                if pkgs:
                    perform.execute("apt-get remove --purge" + pkgs, root=True)

    elif command == "purgeremoved":
        if requires_no_args(command, args):
            pkgs = ""
            cmd = "dpkg-query --show --showformat='${Package}\t${Status}\n' |"\
            + " grep \"deinstall ok config-files\" | cut -f 1 "
            for p in perform.execute(cmd, pipe=True):
                pkgs += " " + p.strip()
            # 090430 Use dpkg --purge instead - like wajig purge....
            # Was there any reason to use apt-get instead?
            # if pkgs: perform.execute("apt-get remove --purge" + pkgs, root=True)
            if pkgs:
                perform.execute("dpkg --purge" + pkgs, root=True)

    elif command == "readme":
        if requires_one_arg(command, args, "a single package"):
            docpath = "/usr/share/doc/" + args[1] + "/"
            if not os.path.exists(docpath):
                print "No docs found for '%s'. Is it installed?" % args[1]
                return
            readmes = ["README", "README.Debian", "USAGE"]
            found = False
            for r in readmes:
                readme = docpath + r
                cat = "cat"
                if not os.path.exists(readme):
                    readme = readme + ".gz"
                    cat = "zcat"
                if os.path.exists(readme):
                    found = True
                    print "=" * 30 + " " + r + " " + "=" * 30
                    sys.stdout.flush()
                    perform.execute(cat + " " + readme)
            if not found:
                print "No README found for '%s'" % args[1]

    elif command in ["recursive", "recdownload"]:
        if requires_args(command, args, "a list of packages"):
            commands.do_recdownload(args[1:])

    elif command == "reconfigure":
        # With no args this will run gkdebconf
        if len(args) > 1:
            perform.execute("dpkg-reconfigure " +\
                            perform.concat(args[1:]),
                            root=True)
        else:
            perform.execute("gkdebconf", root=True)

    elif command == "reinstall":
        if requires_args(command, args, "a list of packages"):
            perform.execute("apt-get --reinstall install " +\
                             perform.concat(args[1:]), root=True)

    elif command == "reload":
        if requires_one_arg(command, args, "name of service to " + command):
            perform.execute("/etc/init.d/" + args[1] + " " + command, root=True)
            # Bug#426969
            # perform.execute("invoke-rc.d " + args[1] + " " + command, root=True)

    elif command == "remove":
        if requires_args(command, args, "a list of packages"):
            perform.execute("apt-get %s remove %s" %
                            (yes, perform.concat(args[1:])), root=True)

    elif command == "removedepend":
        if requires_one_arg(command, args, "a single package"):
            #print changes.get_dependents("libclan2-mikmod")
            # Bug#579419 - this is more efficient than do_removedepend 
            perform.execute("apt-get remove --auto-remove " + args[1], root=True)
            #commands.do_removedepend(args[1])
            
    elif command == "removeorphans":
        if requires_no_args(command, args):
            if requires_package("deborphan", "/usr/bin/deborphan"):
                pkgs = ""
                for p in perform.execute("deborphan", pipe=True):
                    pkgs += " " + p.strip()
                if pkgs:
                    perform.execute("apt-get remove" + pkgs, root=True)

    elif command in ["repackage", "package"]:
        if requires_one_arg(command, args, "name of an installed package"):
            if requires_package("dpkg-repack", "/usr/bin/dpkg-repack"):
                perform.execute("dpkg-repack " + args[1], root=True)

    elif command == "reset":
        if requires_no_args(command, args):
            changes.reset_files()

    elif command == "restart":
        if requires_one_arg(command, args, "name of service to " + command):
            perform.execute("/etc/init.d/" + args[1] + " " + command, root=True)
            # Bug#426969
            # perform.execute("invoke-rc.d " + args[1] + " " + command, root=True)

    elif command == "rpminstall":
        if requires_one_arg(command, args,
        "a Red Hat package file name (.rpm)"):
            perform.execute("alien --to-deb --install " + args[1], root=True)

    elif command in ["rpmtodeb", "rpm2deb"]:
        if requires_one_arg(command, args,
        "a Red Hat package file name (.rpm)"):
            perform.execute("alien -d " + args[1], root=True)

    elif command == "search":
        # Note that this uses a regular expression, thus libstdc++6
        # finds nothing but libstdc..6 does.
        if requires_args(command, args, "a list of words to search for"):
            perform.execute("apt-cache search " + perform.concat(args[1:]))

    elif command == "searchapt":
        if requires_one_arg(command, args, "one of stable|testing|unstable"):
            requires_package("netselect-apt", "/usr/bin/netselect-apt")
            perform.execute("netselect-apt " + args[1], root=True)

    elif command == "showdistupgrade":
        if requires_no_args(command, args):
            perform.execute("apt-get -u -s dist-upgrade", root=True)

    elif command == "showinstall":
        if requires_args(command, args, "a list of packages"):
            perform.execute("apt-get -u -s install " +
            perform.concat(args[1:]), root=True)

    elif command == "showremove":
        if requires_args(command, args, "a list of packages"):
            perform.execute("apt-get -u -s remove " + perform.concat(args[1:]),
            root=True)

    elif command == "showupgrade":
        if requires_no_args(command, args):
            perform.execute("apt-get -u -s upgrade", root=True)

    elif command == "size" or command == "sizes":
        commands.do_size(args[1:], 0)

    elif command == "snapshot":
        if requires_no_args(command, args):
            commands.do_status([], True)

    elif command == "source":
        if requires_args(command, args, "a list of package names"):
            # First make sure dependencies are met
            # John V. Belmonte 04 Nov 2005 requested this not be done
            # Leave it to the user to do wajig builddepend
            # It is not always necessary
            #perform.execute("apt-get build-dep " + perform.concat(args[1:]),
            #                root=True)
            perform.execute("apt-get source " + perform.concat(args[1:]))

    elif command == "start":
        if requires_one_arg(command, args, "name of service to " + command):
            perform.execute("/etc/init.d/" + args[1] + " " + command, root=True)
            # Bug#426969
            # perform.execute("invoke-rc.d " + args[1] + " " + command, root=True)

    elif command == "status":
        commands.do_status(args[1:])

    elif command == "statusmatch" or command == "statussearch":
        if requires_one_arg(command, args,
        "a search string for the package name"):
            pkgs = map(lambda s: s.strip(),
                   commands.do_listnames(args[1:], pipe=True).readlines())
            if len(pkgs) > 0:
                commands.do_status(pkgs)
            else:
                print "No packages found matching '%s'" % args[1]
        #
        # Simplest thing to do is call wajig again.  Not the right way
        # but works for now.
        #
        # This was too slow and was not stopping when killed!
        #perform.execute("apt-cache search " \
        #                    + perform.concat(args[1:]) \
        #                    + " | awk '{print $1}' " \
        #                    + " | xargs wajig status ")

    elif command == "stop":
        if requires_one_arg(command, args, "name of service to " + command):
            perform.execute("/etc/init.d/" + args[1] + " " + command, root=True)
            # Bug#426969
            # perform.execute("invoke-rc.d " + args[1] + " " + command, root=True)

    elif command == "tasksel":
        if requires_no_args(command, args):
            if requires_package("tasksel", "/usr/bin/tasksel"):
                perform.execute("tasksel", root=True)

    elif command == "toupgrade":
        if requires_no_args(command, args):
            commands.do_toupgrade()

    # edd 03 Sep 2003  unhold patch based on hold semantics
    elif command == "unhold":
        if requires_args(command, args,
        "a list of packages to remove from hold"):
            commands.do_unhold(args[1:])
        # TODO Perhaps I can use map to "execute" over each package

    elif command == "update":
        if requires_no_args(command, args):
            commands.do_update()

    # For testing only!
    elif command == "updateavailable":
        if requires_no_args(command, args):
            changes.update_available()

    elif command in ["updatealts", "updatealternatives", "setalts",
        "setalternatives"]:
        if requires_one_arg(command, args, "name of alternative to update"):
            perform.execute("update-alternatives --config " + args[1], root=True)

    elif command == "updatepciids":
        if requires_package("pciutils", "/usr/bin/update-pciids"):
            if requires_no_args(command, args):
                perform.execute("update-pciids", root=True)

    elif command == "updateusbids":
        if requires_package("usbutils", "/usr/sbin/update-usbids"):
            if requires_no_args(command, args):
                perform.execute("update-usbids", root=True)

    elif command == "upgrade":
        if len(args) > 1:
            perform.execute("apt-get install " + perform.concat(args[1:]),
                                root=True)
        else:
            perform.execute("apt-get %s -u upgrade" % noauth, root=True)

    elif command == "upgradesecurity":
        sources_list = tempfile.mkstemp(".security", "wajig.", "/tmp")[1]
        sources_file = open(sources_list, "w")
        # check dist
        sources_file.write("deb http://security.debian.org/ " +\
                           "testing/updates main contrib non-free\n")
        sources_file.close()
        command = "apt-get --no-list-cleanup -o Dir::Etc::SourceList=" +\
                  sources_list + " update"
        perform.execute(command, root=True)
        command = "apt-get -o Dir::Etc::SourceList=" +\
                  sources_list + " upgrade"
        perform.execute(command, root=True)
        if os.path.exists(sources_list):
            os.remove(sources_list)

    elif command == "verify":
        if requires_one_arg(command, args, "a package name"):
            perform.execute("debsums " + args[1])

    elif command == "version" or command == "versions":
        if command == "version" and len(args) == 1:
            documentation.version()
        else:
            if requires_package("apt-show-versions",
                                "/usr/bin/apt-show-versions"):
                commands.versions(args[1:])
    elif command == "whatis":
        if requires_args(command, args, "a list of package names"):
            commands.do_describe(args[1:])

    elif command in ["whichpkg", "whichpackage"]:
        if requires_one_arg(command, args,
        "a file name (possibly with a path)"):
            commands.do_whichpkg(args[1])

    else:
        if command == args[0]:
            print "The command `" + command + "' was not recognised."
        else:
            print "The command `" + command + "' (entered as `" + args[0] + \
                  "') was not recognised."
        print "Perhaps it is not yet implemented or you misspelt the command."
        print "Try `wajig help' for further information."
        print "Try `wajig list-commands' for list of all commands."

    changes.finish_log()

#------------------------------------------------------------------------
#
# Start it all
#
#------------------------------------------------------------------------
if __name__ == '__main__':
    main()
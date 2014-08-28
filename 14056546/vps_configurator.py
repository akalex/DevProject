#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import platform
import commands
import logging
import shutil
import zipfile
import socket
import fcntl
import struct
import csv

# Console colors
BOLD = '\033[1m' # Bold
END = '\033[0m' # Classical text
W  = '\033[0m'  # white (normal)
R  = '\033[31m' # red
G  = '\033[32m' # green
O  = '\033[33m' # orange
B  = '\033[34m' # blue
P  = '\033[35m' # purple
C  = '\033[36m' # cyan
GR = '\033[37m' # gray

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S')
ch.setFormatter(formatter)
root.addHandler(ch)


class VPS_Manager(object):

    def __init__(self):
        """
        Constructor. Describe main variables

        """

        # Get bit OS (32bit or 64bit)
        self.architecture = platform.architecture()[0]
        # Get CentOS version
        linux_version = (commands.getoutput("""cat /etc/redhat-release""")).split()
        self.centos_version = float(linux_version[2])
        print "%s (%s) %s %s" % (linux_version[0], self.architecture, linux_version[1], linux_version[2])
        #print self.architecture
        #print self.centos_version
        find_iface_comm = """ route -n | awk '{ if ($1 == "0.0.0.0") print $8 }' """
        self.iface_name = commands.getoutput(find_iface_comm)

    def install_epel_repo(self):
        """
        Method that installs Extra Packages for Enterprise Linux (EPEL) repository

        """

        bit_prefix = ''
        epel_mirror = ''
        if self.architecture == "32bit":
            bit_prefix = 'i386'
        elif self.architecture == "64bit":
            bit_prefix = 'x86_64'
        if 5 <= self.centos_version < 6:
            epel_mirror = 'http://dl.fedoraproject.org/pub/epel/5/%s/epel-release-5-4.noarch.rpm' % bit_prefix
        elif 6 <= self.centos_version < 7:
            epel_mirror = 'http://dl.fedoraproject.org/pub/epel/6/%s/epel-release-6-8.noarch.rpm' % bit_prefix
        try:
            logging.info(G + 'Downloading EPEL package...' + END)
            commands.getoutput("""wget %s""" % epel_mirror)
            logging.info(G + 'Done' + END)
        except Exception, error:
            logging.error(R + 'Cannot download package %s\n%s\n\n' % (epel_mirror, error) + END)
            sys.exit(1)
        try:
            logging.info(G + 'Installing EPEL package...' + END)
            commands.getoutput("""rpm -Uvh `ls epel-release*`""")
            commands.getoutput("""rm -f epel-release*""")
            logging.info(G + 'Done' + END)
        except Exception, error:
            logging.error(R + 'Cannot install EPEL package %s\n\n' % error + END)
            sys.exit(1)

    def install_pkgs(self):
        """
        Method that installs additional packages
        """

        yum_update_command = "yum -y update"
        yum_install_command = "yum -y install %s"
        list_of_pkg = ['vim-enhanced', 'gcc', 'ncurses-devel', 'pcre-devel', 'bzip2-devel', 'zlib-devel', 'autoconf',
                       'automake', 'libpcap', 'libpcap-devel', 'libnet', 'bc', 'automake14', 'openssl-devel',
                       'rpm-build', 'pam-devel', 'pkgconfig', 'vixie-cron', 'crontabs', 'sshpass']
        try:
            logging.info(G + 'Updating all packages to the latest version...' + END)
            output = commands.getoutput(yum_update_command)
            print output
            logging.info(G + 'Done' + END)
        except Exception, error:
            logging.error(R + 'Cannot update packages %s\n\n' % error + END)
            sys.exit(1)
        try:
            for pkg in list_of_pkg:
                logging.info(G + 'Installing %s...' % pkg + END)
                output = commands.getoutput(yum_install_command % pkg)
                print output
                logging.info(G + 'Done' + END)
        except Exception, error:
            logging.error(R + 'Cannot install package %s\n\n' % error + END)
            sys.exit(1)

    def ip_forwarding(self):
        """
        Method enables IP Forwarding

        """

        get_cur_status_comm = ''' sysctl -a | egrep "net.ipv4.ip_forward" '''
        validata_sysctl_comm = ''' sysctl -p'''
        new_output = ''
        ip_forward_status = int((commands.getoutput(get_cur_status_comm)).split(" = ")[1])
        if ip_forward_status == 0:
            logging.info(G + 'Enabling ip_forward...' + END)
            # Edit /etc/sysctl.conf
            # Edit the “net.ipv4.ip_forward” line and set it to 1
            pattern = re.compile(r'net.ipv4.ip_forward = 0')
            with open('/etc/sysctl.conf', 'rb+') as configfile:
                output = configfile.read()
                if pattern.search(output):
                    match = pattern.search(output)
                    new_output = output.replace(output[match.start():match.end()], 'net.ipv4.ip_forward = 1')
                configfile.truncate(0)
                configfile.seek(0, 0)
                configfile.write(new_output)
            # Validate the new setting
            commands.getoutput(validata_sysctl_comm)
            logging.info(G + 'Done' + END)
        elif ip_forward_status == 1:
            logging.info(G + 'IP Forwarding is already enabled' + END)

    def selinux(self):
        """
        Method disables SELINUX

        """

        get_cur_status_comm = ''' sestatus | awk '{print $3}' '''
        disable_selinux_comm = ''' setenforce 0 '''
        selinux_status = commands.getoutput(get_cur_status_comm)
        new_output = ''
        if selinux_status != 'disabled':
            logging.info(G + 'Disabling SELINUX...' + END)
            # Edit /etc/selinux/config
            # Edit the “SELINUX=disabled” line and set it to disabled
            pattern = re.compile(r'SELINUX=\S+')
            with open('/etc/selinux/config', 'rb+') as configfile:
                output = configfile.read()
                if pattern.search(output):
                    match = pattern.search(output)
                    new_output = output.replace(output[match.start():match.end()], 'SELINUX=disabled')
                configfile.truncate(0)
                configfile.seek(0, 0)
                configfile.write(new_output)
            # Turn selinux off immediately, without rebooting
            commands.getoutput(disable_selinux_comm)
            logging.info(G + 'Done' + END)
        else:
            logging.info(G + 'SELINUX is already disabled' + END)

    def sshd_config(self):
        """
        Method that creates custom config for SSH
        """

        # First, create backup of original sshd_config
        logging.info(G + 'Creating customer sshd_config' + END)

        try:
            logging.info(G + 'Backuping original sshd_config' + END)
            shutil.move('/etc/ssh/sshd_config', '/etc/ssh/sshd_config_bak')
            logging.info(G + 'Done' + END)
        except Exception, error:
            logging.error(R + '/etc/ssh/ssdh_config does not exist!!!' + END)
        try:
            logging.info(G + 'Creating new sshd_config' + END)
            shutil.copy('sshd_config', '/etc/ssh/sshd_config')
            logging.info(G + 'Done' + END)
        except Exception, error:
            logging.error(R + '/etc/ssh/ssdh_config does not exist!!!\n%s\n\n' % error + END)
        # Restarting SSH with new config
        logging.info(G + 'Restarting SSH with new config...' + END)
        #commands.getoutput('''/etc/init.d/sshd restart''')
        logging.info(G + 'Done' + END)

    def bash_profile(self):
        """
        Method that does customization of bash_profile
        """

        custom_profile = """export PS1="\[\e[32;1m\]\u\[\e[0m\]\[\e[32m\]@\h\[\e[36m\]\w\[\e[33m\]\$ \[\e[0m\][\\t]"

function psgrep ()
{
    ps aux | grep "$1" | grep -v 'grep'
}

function psterm ()
{
    [ ${#} -eq 0 ] && echo "usage: $FUNCNAME STRING" && return 0
    local pid
    pid=$(ps ax | grep "$1" | grep -v grep | awk '{ print $1}')
    echo -e "terminating '$1' / process(es):\\n$pid"
    kill -SIGTERM $pid
}
        """

        logging.info(G + 'Customizing bash profile /root/.bash_profile ...' + END)
        if os.path.exists('/root/.bash_profile'):
            if custom_profile in open('/root/.bash_profile', 'r').read():
                logging.warning(O + 'Bash profile is already configured' + END)
                pass
            else:
                with open('/root/.bash_profile', 'a+') as filename:
                    filename.write(custom_profile)
        else:
            with open('/root/.bash_profile', 'a+') as filename:
                filename.write(custom_profile)
        logging.info(G + 'Done' + END)

    def spam_protection(self):
        """
        Method that adds IPTABLES rule to block SMTP abuse by mail spammers on VPN
        """

        iptables_check_rule = """iptables-save | grep -- "%s" """
        check_string = """-A OUTPUT -p tcp -m multiport --dports 25,465 -j REJECT --reject-with icmp-port-unreachable"""
        iptables_comm = """-A OUTPUT -p tcp -d 0/0 -m multiport --dport 25,465 -j REJECT"""
        logging.info(G + 'Adding Spam Protection (iptables %s)...' % iptables_comm + END)
        logging.info(G + 'Checking if rule already exists ...' + END)
        output = commands.getoutput(iptables_check_rule % check_string)
        if output == "":
            logging.info(G + 'Found nothing' + END)
            logging.info(G + 'Adding rule ...' + END)
            commands.getoutput("""iptables %s""" % iptables_comm)
            logging.info(G + 'Done' + END)
        else:
            logging.warning(G + 'Rule already exists ...' + END)
        # Rules created with the iptables command are stored in memory. If the system is restarted before saving
        # the iptables rule set, all rules are lost. For netfilter rules to persist through a system reboot,
        # they need to be saved.
        logging.info(G + 'Saving iptables rules ...' + END)
        commands.getoutput("""iptables-save > /etc/sysconfig/iptables""")
        logging.info(G + 'Done' + END)

    def detect_inet_iface(self):
        """
        Method that determines which interface looking outside.

        """

        check_string = """-A POSTROUTING -s %s -o %s -j MASQUERADE"""
        iptables_comm = """-t nat -A POSTROUTING -s %s -o %s -j MASQUERADE"""
        iptables_check_rule = """iptables-save | grep -- "%s" """
        logging.info(G + 'Detecting Inet interface ...' + END)
        if self.iface_name != "":
            logging.info(BOLD + 'Found -> %s' % self.iface_name + END)
            logging.info(BOLD + 'Adding set iptables rules for %s' % self.iface_name + END)
            for ipnet in ['10.8.0.0/24', '10.20.0.0/24', '10.30.0.0/24']:
                output = commands.getoutput(iptables_check_rule % (check_string % (ipnet, self.iface_name)))
                if output == "":
                    logging.info("iptables %s" % (iptables_comm % (ipnet, self.iface_name)))
                    commands.getoutput("""iptables %s""" % (iptables_comm % (ipnet, self.iface_name)))
                else:
                    logging.warning(O + 'Rule %s already exists. Skipped' % (iptables_comm % (ipnet, self.iface_name)) + END)
            logging.info(G + 'Done' + END)
        else:
            logging.error('Cannot determine Inet interface ...' % self.iface_name)
            sys.exit(1)
        # Rules created with the iptables command are stored in memory. If the system is restarted before saving
        # the iptables rule set, all rules are lost. For netfilter rules to persist through a system reboot,
        # they need to be saved.
        logging.info(G + 'Saving iptables rules ...' + END)
        commands.getoutput("""iptables-save > /etc/sysconfig/iptables""")
        logging.info(G + 'Done' + END)

    def install_s5server(self):
        """
        Method that installs s5server

        """

        def get_ip_address(ifname):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                                                0x8915, # SIOCGIFADDR
                                                struct.pack('256s', ifname[:15])
                                                )[20:24])

        new_output = ""
        logging.info(G + 'Installing s5server ...' + END)
        if os.path.exists('s5server.zip'):
            logging.info(G + 's5server.zip found in current directory. Continue to work with it...' + END)
        else:
            logging.warning(O + 's5server.zip not found in current directory. Trying to download it from remote server...' + END)
            logging.info(BOLD + 'Connecting to 207.7.94.199:2200...' + END)
            try:
                commands.getoutput("""sshpass -p '8cXhRXEXx83i' scp -rp -P 2200 anson@207.7.94.199:./autoscript/s5server.zip s5server.zip 2>/dev/null""")
                logging.info(G + 'Done' + END)
            except Exception, error:
                logging.error(R + 's5server.zip not found\n%s\n\n' % error + END)
        try:
            if not os.path.exists('/s5server'):
                logging.info(G + 'Unziping s5server.zip to /s5server ...' + END)
                with zipfile.ZipFile('s5server.zip', "r") as ziprchive:
                    ziprchive.extractall("/s5server/")
                logging.info(G + 'Done' + END)
            else:
                if os.path.exists('/s5server/socks5.ini'):
                    logging.warning(O + 's5server is already installed' + END)
        except Exception, error:
            logging.error(R + 'File s5server.zip does not exist\n%s\n\n' % error + END)
        try:
            logging.info(G + 'Configuring SOCKS5 server ...' + END)
            pattern = re.compile(r'xxx.xxx.xxx.xxx|\d+.\d+.\d+.\d+')
            with open('/s5server/socks5.ini', 'rb+') as configfile:
                output = configfile.read()
                if pattern.search(output):
                    match = pattern.search(output)
                    new_output = output.replace(output[match.start():match.end()],
                                                '%s' % get_ip_address(self.iface_name))
                if new_output != "":
                    configfile.truncate(0)
                    configfile.seek(0, 0)
                    configfile.write(new_output)
            logging.info(G + 'Done' + END)
        except Exception, error:
            logging.error(R + 'Cannot get access to /s5server/socks5.ini\n%s\n\n' % error + END)

    def add_users(self):
        """
        Method that add new users

        """

        counter = 0
        adduser_comm = """useradd -d /home/shared/%s -m -s /sbin/nologin %s && echo "%s:%s" | chpasswd"""
        logging.info(G + 'Adding new users...' + END)
        with open('usr_passwd.csv', 'rb') as csvfile:
            datareader = csv.reader(csvfile, delimiter=',')
            for row in datareader:
                counter += 1
                check_exists = commands.getoutput("""grep "^%s:" /etc/passwd""" % row[0])
                if check_exists == '':
                    commands.getoutput(adduser_comm % (row[0], row[0], row[0], row[1]))
                    logging.info('%s /home/shared/%s /sbin/nologin added.' % (row[0], row[0]))
                else:
                    logging.error(R + 'User %s is already exists. Skipped...'% row[0] + END)
        logging.info(G + '%s users added. Done' % counter + END)

if __name__ == "__main__":
    try:
        child = VPS_Manager()
        child.install_epel_repo()
        child.install_pkgs()
        child.ip_forwarding()
        child.selinux()
        child.sshd_config()
        child.bash_profile()
        child.spam_protection()
        child.detect_inet_iface()
        child.install_s5server()
        child.add_users()
    except KeyboardInterrupt:
        logging.error('Program has been interrupted!!!')
    except SystemExit:
        logging.error('Program has been finished!!!')
    except Exception, error:
        logging.error(R + 'Cannot start configurator %s\n\n' % error + END)
        sys.exit(1)

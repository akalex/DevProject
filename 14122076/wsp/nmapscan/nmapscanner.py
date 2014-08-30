#!/usr/bin/env python
# -*- coding: utf-8 -*-

import commands
import os
import shutil
import re


class Nmap_Vuln_Scan(object):

    def __init__(self, target):
        self.target = target

    def check_mod(self):
        """
        Method that checks availability of pre-installed modules.

        """

        print "Checking pre-installed NMAP modules..."
        common_mods = ['cve.csv', 'exploitdb.csv', 'openvas.csv', 'osvdb.csv', 'scipvuldb.csv',
                       'securityfocus.csv', 'securitytracker.csv', 'xforce.csv', 'vulscan.nse']
        notinstalled_mods = []
        nmap_dir = "/usr/share/nmap/scripts/vulscan"
        if os.path.exists(nmap_dir):
            all_mods = os.listdir(nmap_dir)
            if all_mods:
                notinstalled_mods = [x for x in common_mods if x not in all_mods]
            else:
                notinstalled_mods = common_mods
            if len(notinstalled_mods) == len(common_mods):
                return notinstalled_mods
            else:
                return notinstalled_mods
        else:
            os.mkdir(nmap_dir)
            return notinstalled_mods

    def installer(self, list_of_pkg):
        """
        Method that installs missing modules

        """

        print "Installing additional NMAP modules..."
        release = "nmap_nse_vulscan-2.0.tar.gz"
        download_comm = """wget http://www.computec.ch/projekte/vulscan/download/%s"""
        unpack_comm = """tar -xf %s"""
        clean_comm = """rm -rf %s && rm -rf vulscan"""
        commands.getoutput(download_comm % release)
        commands.getoutput(unpack_comm % release)
        for row in list_of_pkg:
            print "\t missing component -> %s" % row
            shutil.copy2("vulscan/%s" % row, "/usr/share/nmap/scripts/vulscan")
            print "\t %s installation complete..." % row
        commands.getoutput(clean_comm % release)

    def run_scan(self):
        """Method that performs scanning of some host

        """

        nmap_comm = """ nmap -sV --script=vulscan/vulscan.nse -oX %s.xml %s """
        commands.getoutput(nmap_comm % (self.target, self.target))

    def add_to_report(self):
        """
        Method that correlate xml reports

        """

        input_file = './%s.xml' % self.target
        output_file = './%s_full_report.xml' % self.target
        insert_string = ""
        pattern = re.compile("^</vulnDB>$", re.MULTILINE)
        if os.path.exists(input_file):
            with open(input_file, 'rb') as infilename:
                for i, line in enumerate(infilename, start=1):
                    if i >= 4:
                        insert_string = ''.join([insert_string, line])
            with open(output_file, 'rb+') as outfilename:
                output = outfilename.read()
                has_pattern = [row for row in pattern.finditer(output)]
                if has_pattern:
                    for row in pattern.finditer(output):
                        match_pos = row.start()
                        outfilename.seek(match_pos)
                        outfilename.write(insert_string)
                        outfilename.write("</vulnDB>")
                else:
                    pass
        else:
            pass

    def cleaner(self):
        """Make sure that all temporary files will be deleted.

        """

        os.unlink('./%s.xml' % self.target)

    def engine(self):
        """
        Method where everything is happens

        """

        print "NMAP Vulnerability Scanner"
        miss_mods = self.check_mod()
        if miss_mods:
            self.installer(miss_mods)
            print "Installation complete!"
        else:
            print "All necessary modules for NMAP installed"
        self.run_scan()
        self.add_to_report()
        self.cleaner()

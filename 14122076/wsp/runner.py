#!/usr/bin/env python
# -*- coding: utf-8 -*-


from nmapscan.nmapscanner import Nmap_Vuln_Scan
from vulndb.vulndbscanner import VulnDB_Scan
from wpscan.wpscanner import WP_Scan


if __name__ == "__main__":
    list_of_classes = [VulnDB_Scan, Nmap_Vuln_Scan, WP_Scan]
    #list_of_classes = [VulnDB_Scan, Nmap_Vuln_Scan]
    for cls in list_of_classes:
        if cls == VulnDB_Scan:
            child = cls()
        else:
            child = cls("systransfer.com")
        child.engine()

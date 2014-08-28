#!/bin/bash
sudo apt-get install -y subversion git-core python-dnspython python-beautifulsoup
git clone git://github.com/appliedsec/pygeoip.git
cd pygeoip
python setup.py build
sudo python setup.py install
cd ..
sudo rm -rf pygeoip

hg clone https://code.google.com/p/simplekml/
mv simplekml simplekml.hg
mv simplekml.hg/simplekml simplekml
sudo rm -rf simplekml.hg

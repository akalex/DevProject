#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string
import re
import os


def main():
    if os.path.exists('combined.txt'):
        os.unlink('combined.txt')
    # Where to search text files
    dir_name = "."
    # Creates generator with files
    onlyfiles = (f_name for f_name in
	            [os.path.join(root, name) for root, subdirs, files in os.walk(dir_name)
	            for name in files if os.path.join(root, name).endswith('.txt')
                if not re.search('fix_', name)])
    # Iterate through generator
    for filename in onlyfiles:
        print "\nReading file: ", filename
        # Open each file and writes it into variable in_file
        with open(filename, 'r+') as in_file:
            output = in_file.read()
        print "Original text: ", output
        # String of ASCII characters which are considered punctuation characters in the C locale.
        for char in string.punctuation:
            if char == '!' or char == '?':
                output = re.sub('\s+|\d+', ' ', output.replace(char, '.').lower())
            else:
                output = re.sub('\s+|\d+', ' ', output.replace(char, ' ').lower())
        # Open file to writes result
        print "Corrected text: ", output
        #with open(''.join(['fix_', filename.split('/')[-1]]), 'w+') as out_file:
        with open('combined.txt', 'a+') as out_file:
            print >> out_file, output

if __name__ == "__main__":
    main()
#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys


def check_file_exist(*args):
    """Make sure a file exists.
    """

    for filename in args:
        if os.path.exists(filename):
            continue
        else:
            sys.stderr.write("File %s not found. Exiting..." % filename)
            sys.exit(1)

def main():
    # Input/Output file. Please change this parameter if it has different name
    input_output_file = "users"
    # File with expired users. Please change this parameter if it has different name
    expire_file = "expired"
    # File with users that are in file "expired" but not found in "users".
    failed_file = "failed.log"
    # Make sure that all files exist
    check_file_exist(input_output_file, expire_file)
    expired_user_list = []
    all_user_list = []
    active_users = ""
    total_users = 0
    total_expired_users = 0
    total_active_users = 0
    total_deleted_users = 0
    with open(expire_file, 'rb') as exp_user_file:
        expired_user_list = exp_user_file.readlines()
    expired_user_list = [name.strip() for name in expired_user_list]
    expired_user_list = filter(lambda name: name.strip, expired_user_list)
    total_expired_users = len(expired_user_list)
    with open(input_output_file, 'rb+') as in_out_file:
        user_passwd = in_out_file.read()
        user_array = user_passwd.split("\n")
        user_array = filter(lambda name: name.strip(), user_array)
        for line in user_array:
            total_users += 1
            user = line.split(":")[0]
            all_user_list.append(user)
            if user in expired_user_list:
                total_deleted_users += 1
            else:
                total_active_users += 1
                active_users = ''.join([active_users, line, '\n'])
        in_out_file.truncate(0)
        in_out_file.seek(0, 0)
        in_out_file.write(active_users)
    with open(failed_file, 'w') as failedlog_file:
        final_list = filter(None, list(set(expired_user_list) - set(all_user_list)))
        for usr in final_list:
            failedlog_file.write(''.join([usr, '\n']))
    print "Total number of users (before check): %s \n" \
          "Total number of expired users: %s \n" \
          "Total number of matched users: %s \n" \
          "Total number of users (after check): %s \n" \
          "Additional details: failed.log" % (total_users, total_expired_users,
                                                       total_deleted_users, total_users - total_deleted_users)

if __name__ == "__main__":
    main()
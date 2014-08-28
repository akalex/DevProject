#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# version 1.0

import boto
import urllib2
import MySQLdb
import re
import os
import shutil
import Image
import datetime


class MysqlConnector(object):

    def __init__(self):
        """Constructor with default variables like database connection arguments

        """

        self.dbhost = "localhost"
        self.dbuser = "root"
        self.dbpass = "12345"
        self.dbname = "mydb"
        try:
            self.mydb = MySQLdb.connect(self.dbhost, self.dbuser, self.dbpass, self.dbname)
        except Exception, error:
            print "Database connection failed! -> %s" % error

    def link(self, query):
        """Connect to database and execute SELECT only query

        """

        try:
            cursor = self.mydb.cursor()
            cursor.execute(query)
            info = cursor.fetchall()
            cursor.close()
            return info
        except:
            try:
                self.mydb = MySQLdb.connect(self.dbhost, self.dbuser, self.dbpass, self.dbname)
                cursor = self.mydb.cursor()
                cursor.execute(query)
                info = cursor.fetchall()
                cursor.close()
                return info
            except Exception, error:
                print "Database connection failed! -> %s" % error

    def insert(self, query):
        """Connect to database and execute INSERT/UPDATE/DELETE query

        """

        try:
            cursor = self.mydb.cursor()
            self.mydb.rollback()
            cursor.execute(query)
            self.mydb.commit()
            cursor.close()
        except Exception, error:
            print "Unable to perform query! -> %s" % error

    def connection_close(self):
        """Close database connection

        """

        self.mydb.close()

class ImageParser(object):
    """ImageParser - class to parses images by provided URL and creates thumbnails for them.
    Afterwards it uploads file to Amazon S3.

    """

    def __init__(self):
        self.s3key = 'AKIAIYZERMTB6Z5NPF5Q'
        self.s3secret = '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'
        self.bucket_name = "alexomyshev-test"
        self.for_upload = []
        self.tempdir = 'tmp'
        self.current_date = datetime.datetime.today().strftime("%Y-%m-%d")
        self.create_temp_dir()
        self.get_image_data()
        self.cleaner()

    def create_temp_dir(self):
        """For temporary files.

        """

        if os.path.exists(self.tempdir):
            pass
        else:
            os.mkdir(self.tempdir)

    def cleaner(self):
        """Сleans up after itself

        """

        if os.path.exists(self.tempdir):
            shutil.rmtree(self.tempdir)
        else:
            pass

    def get_image_data(self):
        """Get URLs of images from database

        """

        get_url_img_sql = """select id, image_url from cars where is_image_parsed=0;"""
        img_output = db_conn.link(get_url_img_sql)
        self.download_img(img_output)

    def update_record(self, url_dict):
        """Method that updates record in table 'cars'.
        It marks cars that have been processed.
        url_dict - dict

        """

        update_url_img_sql = """update cars set is_image_parsed=1, parsed_date='%s', number_of_images='%s' where id='%s';"""
        for urlid, urlcount in url_dict.iteritems():
            db_conn.insert(update_url_img_sql % (self.current_date, urlcount, urlid))

    def download_img(self, img_url_list):
        """Download images from remote server
        img_url_list - list

        """

        url_stats = {}
        for row in img_url_list:
            urlid = row[0]
            url = row[1]
            for num in xrange(1,31):
                if num <= 30:
                    url_stats.update({urlid: num})
                    img_url = re.sub('\{seq\}', str(num), url)
                    request = urllib2.Request(img_url)
                    try:
                        response = urllib2.urlopen(request)
                        img_name = img_url.split("/")[-1]
                        with open(os.path.join(self.tempdir, img_name), 'wb') as localfile:
                            localfile.write(response.read())
                        thumbnail_status = self.create_thumbnail(img_name)
                        print thumbnail_status, img_name
                    except urllib2.URLError, e:
                        if e.code == 404:
                            print "Not Found %s" % img_url
                            url_stats.update({urlid: num-1})
                            break
                else:
                    break
        self.aws_s3_uploader()
        self.update_record(url_stats)

    def create_thumbnail(self, img):
        """Thumbnail generator. Creates thumbnails by provided images

        """

        self.for_upload.append(img)
        size = 233, 175
        output_file = "thumbnail_%s" % img
        try:
            im = Image.open(os.path.join(self.tempdir, img))
            im.thumbnail(size)
            im.save(os.path.join(self.tempdir, output_file), "JPEG")
            self.for_upload.append(output_file)
            return "OK"
        except IOError, e:
            return e

    def aws_s3_uploader(self):
        """Upload images and thumbs to Amazon S3

        """

        s3_conn = boto.connect_s3(self.s3key, self.s3secret)
        bucket_obj = s3_conn.get_bucket(self.bucket_name)
        for filename in os.listdir(self.tempdir):
            full_key_name = os.path.join('test', filename)
            key = bucket_obj.new_key(full_key_name)
            key.set_contents_from_filename(os.path.join(self.tempdir, filename))
            print "Successfully uploaded to S3 bucket: %s, key: %s" % (self.bucket_name, full_key_name)
            # For public access
            #key.set_acl('public-read')

if __name__ == "__main__":
    db_conn = MysqlConnector()
    ImageParser()
    db_conn.connection_close()

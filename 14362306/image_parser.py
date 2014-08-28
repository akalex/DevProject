#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# version 1.0

import boto
import urllib2
import MySQLdb
import re
import os
import glob
import shutil
import Image
import datetime
import time
from threading import Thread, activeCount


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
        s3key = 'AKIAIYZERMTB6Z5NPF5Q'
        s3secret = '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'
        bucket_name = "hrachya-test"
        self.s3_conn = boto.connect_s3(s3key, s3secret)
        self.bucket_obj = self.s3_conn.get_bucket(bucket_name)
        self.for_upload = []
        self.url_stats = {}
        self.tempdir = 'tmp'
        self.current_date = datetime.datetime.today().strftime("%Y-%m-%d")
        self.create_temp_dir()
        self.get_image_data()

        #self.aws_s3_uploader()
        #self.update_record()
        #self.cleaner()

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

    def chunks(self, l, n):
        """ Yield successive n-sized chunks from l.
        """

        for i in xrange(0, len(l), n):
            yield l[i:i+n]

    def get_image_data(self):
        """Get URLs of images from database

        """

        get_url_img_sql = """select id, image_url from cars where is_image_parsed=0;"""
        img_output = db_conn.link(get_url_img_sql)
        for chunk in self.chunks(img_output, 50):
            worker = Thread(target=self.download_img, args=(chunk,))
            worker.setDaemon(True)
            worker.start()
        while (activeCount() > 1):
            time.sleep(5)
        for chunk in self.chunks(glob.glob1(self.tempdir, "*.jpg"), 50):
            worker = Thread(target=self.create_thumbnail, args=(chunk,))
            worker.setDaemon(True)
            worker.start()
        while (activeCount() > 1):
            time.sleep(5)
        #self.download_img(img_output)

    def update_record(self):
        """Method that updates record in table 'cars'.
        It marks cars that have been processed.

        """

        update_url_img_sql = """update cars set is_image_parsed=1, parsed_date='%s', number_of_images='%s' where id='%s';"""
        for urlid, urlcount in self.url_stats.iteritems():
            db_conn.insert(update_url_img_sql % (self.current_date, urlcount, urlid))

    def download_img(self, img_url_list):
        """Download images from remote server
        img_url_list - list

        """

        for row in img_url_list:
            urlid = row[0]
            url = row[1]
            for num in xrange(1,31):
                if num <= 30:
                    self.url_stats.update({urlid: num})
                    img_url = re.sub('\{seq\}', str(num), url)
                    request = urllib2.Request(img_url)
                    try:
                        response = urllib2.urlopen(request)
                        img_name = img_url.split("/")[-1]
                        with open(os.path.join(self.tempdir, img_name), 'wb') as localfile:
                            localfile.write(response.read())
                    except urllib2.URLError, e:
                        if e.code == 404:
                            print "Not Found %s" % img_url
                            self.url_stats.update({urlid: num-1})
                            break
                else:
                    break

    def create_thumbnail(self, img_list):
        """Thumbnail generator. Creates thumbnails by provided images

        """

        size = 233, 175
        for img in img_list:
            output_file = "thumbnail_%s" % img
            self.for_upload.append(img)
            try:
                im = Image.open(os.path.join(self.tempdir, img))
                im.thumbnail(size)
                im.save(os.path.join(self.tempdir, output_file), "JPEG")
                self.for_upload.append(output_file)
                print "OK", img
            except IOError, e:
                print "ERROR", img

    def aws_s3_uploader(self, list_files):
        """Upload images and thumbs to Amazon S3
        list_files - list

        """

        for filename in list_files:
            full_key_name = os.path.join('test', filename)
            key = self.bucket_obj.new_key(full_key_name)
            key.set_contents_from_filename(os.path.join(self.tempdir, filename))
            print "Successfully uploaded to S3 bucket: %s, key: %s" % (self.bucket_name, full_key_name)
            # For public access
            #key.set_acl('public-read')

if __name__ == "__main__":
    db_conn = MysqlConnector()
    ImageParser()
    db_conn.connection_close()

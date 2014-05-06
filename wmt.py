#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# version: 1.0

import gdata.webmastertools.service
import datetime
from datetime import timedelta
from bs4 import BeautifulSoup
from sqlalchemy import Table, Column, Sequence, Integer, ForeignKey, Numeric, String, MetaData, create_engine, Text, Date, \
    UniqueConstraint
from sqlalchemy.sql import select
from sqlalchemy import exc
import json
import xml.etree.ElementTree as xmlElementTree
import csv
import os
import sys
import glob
import re
import argparse
from selenium import webdriver
from pyvirtualdisplay import Display
#
#
class Collect_WMT(object):

    HOST = 'www.google.com'
    APP_NAME = 'Google-WMTdownloadscript-0.1'
    LIST_PATH = '/webmasters/tools/downloads-list?hl=%s&siteUrl=%s'
    SITE_LIST = '/webmasters/tools/feeds/sites/'
    FILE_NAME_HEADER = 'content-disposition'
    TEXT_BEFORE_NAME = 'attachment; filename='
    DATE_FILTER = '&db=%s&de=%s'
    _ATOM_INSTALL_CONSTANT = "{http://www.w3.org/2005/Atom}"

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._startDt = None
        self._endDt = None
        # Specify the website and the type of data to download
        # Valid values are 'TOP_QUERIES', 'TOP_PAGES', 'TOP_QUERIES_CHART',
        # 'EXTERNAL_LINKS', 'INDEX_STATUS', 'CRAWL_ERRORS'
        self.selected_downloads = ['TOP_QUERIES', 'TOP_PAGES', 'TOP_QUERIES_CHART', 'EXTERNAL_LINKS', 'INDEX_STATUS'
                                    'CRAWL_ERRORS']
        #### Date for reports
        self.end_date = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y%m%d"), "%Y%m%d").date()
        self.start_date = datetime.datetime.strptime((datetime.datetime.now() - datetime.timedelta(days=4)).strftime("%Y%m%d"), "%Y%m%d").date()
        self.oneday_delta = timedelta(days=1)
        self.frequencyday_delta = timedelta(days=1)
        self.SetDateRange((self.start_date).strftime('%Y%m%d'), (self.start_date + self.frequencyday_delta - self.oneday_delta).strftime('%Y%m%d'))
        ####
        # Create a client class which will make HTTP requests with Google WMT server
        self._client = gdata.webmastertools.service.GWebmasterToolsService()
        # Authenticate using your Google WMT email address and password.
        self._client.ClientLogin(self._username, self._password)
        # Call method "model" that contains description of database..
        self.model()

    def model(self):
        """
        Method that describes database model

        """
        # Create connection to PostgreSQL
        # login: wmt_admin
        # password: wmt_admin12345
        # database schema: wmt
        # host: localhost
        pgsql_engine = create_engine('postgresql+psycopg2://wmt_admin:wmt_admin12345@localhost/wmt')

        # Define our tables all within a catalog called MetaData
        metadata = MetaData()

        ### Description of tables ###
        # site
        self.site = Table('site', metadata,
            Column('id', Integer, Sequence('site_id_seq'), primary_key=True, autoincrement=True),
            Column('url', String(60), nullable=False, unique=True)
        )
        # messages
        self.messages = Table('messages', metadata,
            Column('id', Integer, Sequence('messages_id_seq'), primary_key=True, autoincrement=True),
            Column('site_id', Integer, ForeignKey('site.id', onupdate='CASCADE', ondelete='CASCADE', deferrable=True), nullable=False),
            Column('subject', Text, nullable=False),
            Column('date', Date, nullable=False),
            # explicit/composite unique constraint. 'name' is optional.
            UniqueConstraint('site_id', 'subject', 'date', name='messages_site_id_subject_date_key'),
        )
        # html_improvements
        self.html_improvements = Table('html_improvements', metadata,
            Column('id', Integer, Sequence('html_improvements_id_seq'), primary_key=True, autoincrement=True),
            Column('site_id', Integer, ForeignKey('site.id', onupdate='CASCADE', ondelete='CASCADE', deferrable=True), nullable=False),
            Column('num_page', Integer, nullable=False),
            Column('date', Date, nullable=False),
            # explicit/composite unique constraint. 'name' is optional.
            UniqueConstraint('site_id', 'date', name='html_improvements_site_id_date_key'),
        )
        # top_queries
        self.top_queries = Table('top_queries', metadata,
            Column('id', Integer, Sequence('top_queries_id_seq'), primary_key=True, autoincrement=True),
            Column('site_id', Integer, ForeignKey('site.id', onupdate='CASCADE', ondelete='CASCADE', deferrable=True), nullable=False),
            Column('query', Text, nullable=False),
            Column('impression', Integer, nullable=False),
            Column('click', Integer, nullable=False),
            Column('ctr', Integer, nullable=False),
            Column('avg_position', Numeric(7,1), nullable=False),
            Column('date', Date, nullable=False),
            # explicit/composite unique constraint. 'name' is optional.
            UniqueConstraint('site_id', 'query', 'date', name='top_queries_site_id_query_date_key'),
        )
        # top_pages
        self.top_pages = Table('top_pages', metadata,
            Column('id', Integer, Sequence('top_pages_id_seq'), primary_key=True, autoincrement=True),
            Column('site_id', Integer, ForeignKey('site.id', onupdate='CASCADE', ondelete='CASCADE', deferrable=True), nullable=False),
            Column('page', Text, nullable=False),
            Column('impression', Integer, nullable=False),
            Column('click', Integer, nullable=False),
            Column('ctr', Integer, nullable=False),
            Column('avg_position', Numeric(7,1), nullable=False),
            Column('date', Date, nullable=False),
            # explicit/composite unique constraint. 'name' is optional.
            UniqueConstraint('site_id', 'page', 'date', name='top_pages_site_id_page_date_key'),
        )
        # top_queries_chart
        self.top_queries_chart = Table('top_queries_chart', metadata,
            Column('id', Integer, Sequence('top_queries_chart_id_seq'), primary_key=True, autoincrement=True),
            Column('site_id', Integer, ForeignKey('site.id', onupdate='CASCADE', ondelete='CASCADE', deferrable=True), nullable=False),
            Column('impression', Integer, nullable=False),
            Column('click', Integer, nullable=False),
            Column('date', Date, nullable=False),
            # explicit/composite unique constraint. 'name' is optional.
            UniqueConstraint('site_id', 'date', name='top_queries_chart_site_id_date_key'),
        )
        # inbound_links
        self.inbound_links = Table('inbound_links', metadata,
            Column('id', Integer, Sequence('inbound_links_id_seq'), primary_key=True, autoincrement=True),
            Column('site_id', Integer, ForeignKey('site.id', onupdate='CASCADE', ondelete='CASCADE', deferrable=True), nullable=False),
            Column('link', Text, nullable=False),
            Column('first_discovered', Date, nullable=False),
            # explicit/composite unique constraint. 'name' is optional.
            UniqueConstraint('site_id', 'link', 'first_discovered', name='inbound_links_site_id_link_first_discovered_key'),
        )
        # index_status
        self.index_status = Table('index_status', metadata,
            Column('id', Integer, Sequence('index_status_id_seq'), primary_key=True, autoincrement=True),
            Column('site_id', Integer, ForeignKey('site.id', onupdate='CASCADE', ondelete='CASCADE', deferrable=True), nullable=False),
            Column('total_indexed', Integer, nullable=False),
            Column('ever_crawled', Integer, nullable=False),
            Column('blocked_by_robots', Integer, nullable=False),
            Column('removed', Integer, nullable=False),
            Column('date', Date, nullable=False),
            # explicit/composite unique constraint. 'name' is optional.
            UniqueConstraint('site_id', 'date', name='index_status_site_id_date_key'),
        )
        # crawl_errors
        self.crawl_errors = Table('crawl_errors', metadata,
            Column('id', Integer, Sequence('crawl_errors_id_seq'), primary_key=True, autoincrement=True),
            Column('site_id', Integer, ForeignKey('site.id', onupdate='CASCADE', ondelete='CASCADE', deferrable=True), nullable=False),
            Column('url', Text, nullable=False),
            Column('response_code', Integer, nullable=False),
            Column('news_error', String(100), nullable=True),
            Column('date_detected', Date, nullable=False),
            Column('category', String(100), nullable=True),
            # explicit/composite unique constraint. 'name' is optional.
            UniqueConstraint('site_id', 'url', 'date_detected', name='crawl_errors_site_id_date_key'),
        )
        # sitemaps
        self.sitemaps = Table('sitemaps', metadata,
            Column('id', Integer, Sequence('sitemaps_id_seq'), primary_key=True, autoincrement=True),
            Column('site_id', Integer, ForeignKey('site.id', onupdate='CASCADE', ondelete='CASCADE', deferrable=True), nullable=False),
            Column('sitemap', Text, nullable=False),
            Column('type', String(40), nullable=False),
            Column('date_processed', Date, nullable=False),
            Column('date_submitted', Date, nullable=False),
            Column('submitted_by_me', String(5), nullable=False),
            Column('number_of_warnings', Integer, nullable=False, default=0),
            Column('number_of_errors', Integer, nullable=False, default=0),
            Column('submitted_web', Integer, nullable=False, default=0),
            Column('indexed_web', Integer, nullable=False, default=0),
            Column('submitted_images', Integer, nullable=False, default=0),
            Column('indexed_images', Integer, nullable=False, default=0),
            Column('submitted_video', Integer, nullable=False, default=0),
            Column('indexed_video', Integer, nullable=False, default=0),
            Column('submitted_news', Integer, nullable=False, default=0),
            Column('indexed_news', Integer, nullable=False, default=0),
            Column('submitted_mobile', Integer, nullable=False, default=0),
            Column('indexed_mobile', Integer, nullable=False, default=0),
            Column('submitted_app_pages', Integer, nullable=False, default=0),
            Column('indexed_app_pages', Integer, nullable=False, default=0),
            # explicit/composite unique constraint. 'name' is optional.
            UniqueConstraint('site_id', 'sitemap', 'date_submitted', name='sitemaps_site_id_date_key'),
        )
        # Establishes a real DBAPI connection to the database, which is then used to emit the SQL.
        self.pgconn = pgsql_engine.connect()

    def get_site(self):
        """
        Method that retrieves a list of sites for a user account.

        """

        self.list_site = []
        self.dict_site = {}
        # Query the server for an Atom feed containing a list of your sites
        sitelist = self._client.GetSitesFeed()
        # Loop through the feed and extract each site entry.
        print "Collecting information about site(s):"
        for site_entry in sitelist.entry:
            # Add the title of the list to the list
            self.list_site.append(site_entry.title.text)
            print site_entry.title.text
            # Insert our site into table "site"
            insert_query = self.site.insert()
            try:
                # Try to insert data into table
                self.pgconn.execute(insert_query, url=site_entry.title.text)
            # Pass if an Integrity Error has occurred
            except exc.IntegrityError:
                pass
        # Create dict with url:id
        select_query = select([self.site])
        for row in self.pgconn.execute(select_query):
            self.dict_site.update({row[1]:row[0]})

    def collect_messages(self):
        """
        Method that retrieves the Messages feed, send an authenticated GET request to the following URL
        https://www.google.com/webmasters/tools/site-message-list?hl=en&siteUrl=http://www.criminology.com/

        """

        print "Collecting Site Messages..."
        url = 'https://www.google.com/webmasters/tools/site-message-list?hl=en&siteUrl=%s'
        for site in self.list_site:
            # Makes GET request
            response = self._client.request('GET', url % site)
            # Gets response and puts it into variable
            html_body = response.read()
            # Running document through Beautiful Soup
            soup = BeautifulSoup(html_body)
            # Check if domain does not have Messages
            tables = soup.find_all('div', {'class':'nodata'})
            if tables != []:
                pass
                #print "%s does not have messages" % site
            else:
                print tables

    def collect_html_improvements(self):
        """
        Method that retrieves the HTML improvements to the following URL
        https://www.google.com/webmasters/tools/html-suggestions?hl=en&siteUrl=http://www.psychologydegreeonline.net/

        """

        print "Collecting HTML Improvements..."
        url = 'https://www.google.com/webmasters/tools/html-suggestions?hl=en&siteUrl=%s'
        for site in self.list_site:
            # Makes a GET request
            response = self._client.request('GET', url % site)
            # Gets response and puts it into variable
            html_body = response.read()
            # Running document through Beautiful Soup
            soup = BeautifulSoup(html_body)
            date_object = ""
            # Navigate though data structure
            if soup.find('span', {'class':'timestamp'}):
                for line in soup.find('span', {'class':'timestamp'}):
                    string_date = line.strip('Last updated  ')
                    date_object = datetime.datetime.strptime(string_date, '%b %d, %Y').date()
                sum_improv = 0
                if soup.find_all('table', {'class':'content-problems'}):
                    for tables in soup.find_all('table', {'class':'content-problems'}):
                        for trs in tables.find_all('tr'):
                            tds = trs.find_all('td')
                            if tds != [] and len(tds) >= 2:
                                sum_improv += int(tds[1].string)
                                #print tds[0].string, tds[1].string
                else:
                    sum_improv = 0
                # Creates the Insert construct, which represents an INSERT statement.
                # This is typically created relative to its target table
                insert_query = self.html_improvements.insert()
                try:
                    # Try to insert data into table
                    self.pgconn.execute(insert_query, site_id=self.dict_site.get(site), num_page=sum_improv, date=date_object)
                # Pass if an Integrity Error has occurred
                except exc.IntegrityError:
                    pass
                # Pass any other exception
                except Exception:
                    pass

    def collect_top_queries(self):
        """
        Method that retrieves the Top Search queries

        """

        print "Collecting Top Queries..."
        url = 'https://www.google.com/webmasters/tools/top-search-queries?hl=en&siteUrl='
        url_tail = '&type=queries'
        for site in self.list_site:
            # Makes a GET request
            response = self._client.request('GET', url + site + url_tail)
            # Gets response and puts it into variable
            html_body = response.read()
            # Looking for download link
            if re.search("Download this table(.*).*46type", html_body):
                # Scan through string looking for a location where the regular expression pattern produces a match,
                # and return a corresponding MatchObject instance.
                m = re.search("Download this table(.*).*46type", html_body)
                match = {"TOP_QUERIES": (m.group(1).lstrip('", \'').rstrip("\\").replace("\\", "\\")).replace("\\75", "=").replace("\\075", "=").replace("\\46","&")}
                # Serialize obj to a JSON formatted str using this conversion table.
                available = json.dumps(match)
                # Deserialize s (a str or unicode instance containing a JSON document) to a Python
                # object using this conversion table.
                site_json = json.loads(available)
                # Call Method that downloads file
                self._DownloadFile(site_json.get("TOP_QUERIES"))

        # Open CSV files for parsing
        list_files = glob.glob('*TopSearchQueries_%s-%s.csv' % ((datetime.datetime.strftime(self.start_date, '%Y%m%d'),
                                                                 datetime.datetime.strftime(self.start_date, '%Y%m%d'))))
        # Creates the Insert construct, which represents an INSERT statement.
        # This is typically created relative to its target table
        insert_query = self.top_queries.insert()
        for file in list_files:
            # Gets site
            site = ''.join(["http://", (file.split("_")[0]).replace("-", "."), "/"])
            # Gets date
            fdate = (file.split("_")[-1]).split("-")[0]
            # Check if file contains only header (byte)
            if os.path.getsize(file) == 71:
                pass
            else:
                with open(file, 'rb') as csvfile:
                    # Skip first line. This is a header
                    # Return the next row of the reader’s iterable object as a list, parsed according to the current dialect.
                    next(csvfile)
                    # Return a reader object which will iterate over lines in the given csvfile.
                    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
                    for row in csv_reader:
                        try:
                            # Try to insert data into table
                            self.pgconn.execute(insert_query, site_id=self.dict_site.get(site),
                                                query=row[0], impression=row[1], click=row[3],
                                                ctr=str(row[5]).rstrip("%"), avg_position=row[7], date=fdate)
                        # Pass if an Integrity Error has occurred
                        except exc.IntegrityError:
                            pass
                        # Pass any other exception
                        except Exception:
                            pass

    def collect_top_pages(self):
        """
        Method that retrieves the Top Pages queries

        """

        print "Collecting Top Pages..."
        url = 'https://www.google.com/webmasters/tools/top-search-queries?hl=en&siteUrl='
        url_tail = '&type=urls'
        for site in self.list_site:
            # Makes a GET request
            response = self._client.request('GET', url + site + url_tail)
            # Gets response and puts it into variable
            html_body = response.read()
            # Looking for download link
            if re.search("Download this table(.*).*46type", html_body):
                # Scan through string looking for a location where the regular expression pattern produces a match,
                # and return a corresponding MatchObject instance.
                m = re.search("Download this table(.*).*46type", html_body)
                match = {"TOP_PAGES": (m.group(1).lstrip('", \'').rstrip("\\").replace("\\", "\\")).replace("\\75", "=").replace("\\075", "=").replace("\\46","&")}
                # Serialize obj to a JSON formatted str using this conversion table.
                available = json.dumps(match)
                # Deserialize s (a str or unicode instance containing a JSON document) to a Python
                # object using this conversion table.
                site_json = json.loads(available)
                # Call Method that downloads file
                self._DownloadFile(site_json.get("TOP_PAGES"))

        # Open CSV files for parsing
        list_files = glob.glob('*TopSearchUrls_%s-%s.csv' % ((datetime.datetime.strftime(self.start_date, '%Y%m%d'),
                                                                 datetime.datetime.strftime(self.start_date, '%Y%m%d'))))
        # Creates the Insert construct, which represents an INSERT statement.
        # This is typically created relative to its target table
        insert_query = self.top_pages.insert()
        for file in list_files:
            # Gets site
            site = ''.join(["http://", (file.split("_")[0]).replace("-", "."), "/"])
            # Gets date
            fdate = (file.split("_")[-1]).split("-")[0]
            # Check if file contains only header (byte)
            if os.path.getsize(file) == 71:
                pass
            else:
                with open(file, 'rb') as csvfile:
                    # Skip first line. This is a header
                    # Return the next row of the reader’s iterable object as a list, parsed according to the current dialect.
                    next(csvfile)
                    # Return a reader object which will iterate over lines in the given csvfile.
                    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
                    for row in csv_reader:
                        try:
                            # Try to insert data into table
                            self.pgconn.execute(insert_query, site_id=self.dict_site.get(site),
                                                page=row[0], impression=str(row[1]).lstrip('"').rstrip('"'), click=row[3],
                                                ctr=str(row[5]).rstrip("%"), avg_position=row[7], date=fdate)
                        # Pass if an Integrity Error has occurred
                        except exc.IntegrityError:
                            pass
                        # Pass any other exception
                        except Exception:
                            pass

    def collect_top_queries_chart(self):
        """
        Method that retrieves the Top Queries Chart.

        """

        print "Collecting Top Queries Chart..."
        url = 'https://www.google.com/webmasters/tools/top-search-queries?hl=en&siteUrl='
        for site in self.list_site:
            # Makes a GET request
            response = self._client.request('GET', url + site)
            # Gets response and puts it into variable
            html_body = response.read()
            # Looking for download link
            if re.search("Download chart data(.*).*46prop", html_body):
                # Scan through string looking for a location where the regular expression pattern produces a match,
                # and return a corresponding MatchObject instance.
                m = re.search("Download chart data(.*).*46prop", html_body)
                match = {"TOP_QUERIES_CHART": (m.group(1).lstrip('", \'').rstrip("\\").replace("\\", "\\")).replace("\\75", "=").replace("\\075", "=").replace("\\46","&")}
                # Serialize obj to a JSON formatted str using this conversion table.
                available = json.dumps(match)
                # Deserialize s (a str or unicode instance containing a JSON document) to a Python
                # object using this conversion table.
                site_json = json.loads(available)
                # Calls Method that downloads file
                self._DownloadFile(site_json.get("TOP_QUERIES_CHART"))

        # Open CSV files for parsing
        list_files = glob.glob('*TopSearchQueriesTimeseries_%s-%s.csv' % ((datetime.datetime.strftime(self.start_date, '%Y%m%d'),
                                                                 datetime.datetime.strftime(self.start_date, '%Y%m%d'))))
        # Creates the Insert construct, which represents an INSERT statement.
        # This is typically created relative to its target table
        insert_query = self.top_queries_chart.insert()
        for file in list_files:
            # Gets site
            site = ''.join(["http://", (file.split("_")[0]).replace("-", "."), "/"])
            # Gets date
            fdate = (file.split("_")[-1]).split("-")[0]
            # Check if file contains only header (byte)
            if os.path.getsize(file) == 21:
                pass
            else:
                with open(file, 'rb') as csvfile:
                    # Skip first line. This is a header
                    # Return the next row of the reader’s iterable object as a list, parsed according to the current dialect.
                    next(csvfile)
                    # Return a reader object which will iterate over lines in the given csvfile.
                    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
                    for row in csv_reader:
                        # Makes sure result is not empty
                        if row != []:
                            if len(row) == 4:
                                imp = ''.join([row[1], row[2]])
                                clk = row[3]
                            else:
                                imp = row[1]
                                clk = row[2]
                            try:
                                # Try to insert data into table
                                self.pgconn.execute(insert_query, site_id=self.dict_site.get(site),
                                                impression=str(imp).lstrip('"').rstrip('"'), click=clk,
                                                date=fdate)
                            # Pass if an Integrity Error has occurred
                            except exc.IntegrityError:
                                pass
                            # Pass any other exception
                            except Exception:
                                pass

    def collect_inbound_links(self):
        """
        Method that retrieves Links to Your Site.

        """

        print "Collecting Links to Site..."
        url = 'https://www.google.com/webmasters/tools/external-links-page?hl=en&siteUrl='
        for site in self.list_site:
            # Makes a GET request
            response = self._client.request('GET', url + site)
            # Gets response and puts it into variable
            html_body = response.read()
            # Looking for download link
            if re.search("Download latest links(.*)", html_body):
                # Scan through string looking for a location where the regular expression pattern produces a match,
                # and return a corresponding MatchObject instance.
                m = re.search("Download latest links(.*)", html_body)
                match = {"EXTERNAL_LINKS": (m.group(1).lstrip('", \'').rstrip("\');").replace("\\", "\\")).replace("\\75", "=").replace("\\075", "=").replace("\\46","&")}
                # Serialize obj to a JSON formatted str using this conversion table.
                available = json.dumps(match)
                # Deserialize s (a str or unicode instance containing a JSON document) to a Python
                # object using this conversion table.
                site_json = json.loads(available)
                # Calls Method that downloads file
                self._DownloadFile(site_json.get("EXTERNAL_LINKS"))

        # Open CSV files for parsing
        list_files = glob.glob('*ExternalLinks_SampleLinks.csv')

        # Creates the Insert construct, which represents an INSERT statement.
        # This is typically created relative to its target table
        insert_query = self.inbound_links.insert()
        for file in list_files:
            # Gets site
            site = ''.join(["http://", (file.split("_")[0]).replace("-", "."), "/"])
            # Gets date
            #fdate = (file.split("_")[-1]).split("-")[0]
            # Check if file contains only header (byte)
            if os.path.getsize(file) == 23:
                pass
            else:
                with open(file, 'rb') as csvfile:
                    # Skip first line. This is a header
                    # Return the next row of the reader’s iterable object as a list, parsed according to the current dialect.
                    next(csvfile)
                    # Return a reader object which will iterate over lines in the given csvfile.
                    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
                    for row in csv_reader:
                        # Makes sure result is not empty
                        if row != []:
                            try:
                                # Try to insert data into table
                                self.pgconn.execute(insert_query, site_id=self.dict_site.get(site),
                                                    link=row[0], first_discovered=row[1])
                            # Pass if an Integrity Error has occurred
                            except exc.IntegrityError:
                                pass
                            # Pass any other exception
                            except Exception:
                                pass

    def collect_index_status(self):
        """
        Method that retrieves Index Status.

        """

        print "Collecting Index Status..."
        url = 'https://www.google.com/webmasters/tools/index-status?hl=en&siteUrl='
        url_tail = '&is-view=a&is-indx=true&is-rbt=true'
        for site in self.list_site:
            # Makes a GET request
            response = self._client.request('GET', url + site + url_tail)
            # Gets response and puts it into variable
            html_body = response.read()
            # Looking for download link
            if re.search("Download chart data(.*)", html_body):
                # Scan through string looking for a location where the regular expression pattern produces a match,
                # and return a corresponding MatchObject instance.
                m = re.search("Download chart data(.*)", html_body)
                match = {"INDEX_STATUS": (m.group(1).lstrip('", \'').rstrip("\');").replace("\\", "\\")).replace("\\75", "=").replace("\\075", "=").replace("\\46","&")}
                # Serialize obj to a JSON formatted str using this conversion table.
                available = json.dumps(match)
                # Deserialize s (a str or unicode instance containing a JSON document) to a Python
                # object using this conversion table.
                site_json = json.loads(available)
                # Calls Method that downloads file
                self._DownloadFile(site_json.get("INDEX_STATUS"))

        # Open CSV files for parsing
        list_files = glob.glob('*IndexStatusTimeseries.csv')

        # Creates the Insert construct, which represents an INSERT statement.
        # This is typically created relative to its target table
        insert_query = self.index_status.insert()
        for file in list_files:
            # Gets site
            site = ''.join(["http://", (file.split("_")[0]).replace("-", "."), "/"])
            # Gets date
            #fdate = (file.split("_")[-1]).split("-")[0]
            # Check if file contains only header (byte)
            if os.path.getsize(file) == 58:
                pass
            else:
                with open(file, 'rb') as csvfile:
                    # Skip first line. This is a header
                    # Return the next row of the reader’s iterable object as a list, parsed according to the current dialect.
                    next(csvfile)
                    # Return a reader object which will iterate over lines in the given csvfile.
                    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
                    for row in csv_reader:
                        # Makes sure result is not empty
                        if row != []:
                            try:
                                # Try to insert data into table
                                self.pgconn.execute(insert_query, site_id=self.dict_site.get(site),
                                                    total_indexed=row[1], ever_crawled=row[1], blocked_by_robots=row[2],
                                                    removed=row[3], date=row[0])
                            # Pass if an Integrity Error has occurred
                            except exc.IntegrityError:
                                pass
                            # Pass any other exception
                            except Exception:
                                pass

    def collect_crawl_errors(self):
        """
        Method that retrieves Crawl Errors.

        """

        print "Collecting Crawl Errors..."
        insert_query = self.crawl_errors.insert()
        url = 'https://www.google.com/webmasters/tools/feeds/'
        url_tail = '/crawlissues/?start-index=1&max-results=100'
        for site in self.list_site:
            # Decoding string to URL
            site_dec = site.replace("://", "%3A%2F%2F").replace(".", "%2E").replace("/", "%2F")
            # Makes a GET request
            response = self._client.request('GET', url + site_dec + url_tail)
            # Gets response and puts it into variable
            html_body = response.read()
            # Parses an XML section from a string constant. Same as XML(). text is a string containing XML data.
            # Returns an Element instance.
            root = xmlElementTree.fromstring(html_body)
            # Finds all matching subelements, by tag name or path.
            # Returns a list containing all matching elements in document order.
            #total_results = int(root.findall('{http://a9.com/-/spec/opensearchrss/1.0/}totalResults')[0].text)
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')
            if entries != []:
                # Iterates via list of entries
                for entry in entries:
                    # Gets URL
                    t_url = entry[7].text
                    # Gets Response Code
                    t_resp_code = (entry[9].text).split(" (")[0]
                    # Gets News Error
                    t_news_err = entry[4].text
                    # Gets date
                    t_date = (entry[8].text).replace("T", " ").split(" ")[0]
                    # Gets Category
                    t_category = (entry[6].text).replace("-", " ").title()
                    try:
                        # Try to insert data into table
                        self.pgconn.execute(insert_query, site_id=self.dict_site.get(site),
                                            url=t_url, response_code=t_resp_code, new_error=t_news_err,
                                            date_detected=t_date, category=t_category)
                    # Pass if an Integrity Error has occurred
                    except exc.IntegrityError:
                        pass
                    # Pass any other exception
                    except Exception:
                        pass

    def collect_sitemaps(self):
        """
        Method that retrieves Sitemaps.

        """

        print "Collecting Sitemaps..."
        # Creates invisible virtual display 640x480 px
        display = Display(visible=0, size=(640, 480))
        # Starts virtual display
        display.start()

        # Creates Fiefox Profile
        fp = webdriver.FirefoxProfile()
        # Uses for the default download directory
        # 0: the desktop
        # 1 (default): the downloads folder
        # 2: the last folder specified for a download
        fp.set_preference("browser.download.folderList", 2)
        # The browser.download.dir option specify the directory where you want to download the files.
        # Gets current dir
        fp.set_preference("browser.download.dir", os.getcwd())
        # Determines the directory to download to when browser.download.useDownloadDir is false.
        # Appears to mirror browser.download.dir.
        fp.set_preference("browser.download.downloadDir", os.getcwd())
        # Path to the last directory used for a download via "Save As."
        fp.set_preference("browser.download.lastDir", os.getcwd())
        # True: Set the Download Manager window as active when starting a download
        # False (default): Leave the window in the background when starting a download
        fp.set_preference("browser.download.manager.showWhenStarting", True)
        # A comma-separated list of MIME types to save to disk without asking what to use to open the file.
        # Default value is an empty string.
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

        url = 'https://www.google.com/webmasters/tools/feeds/'
        url_tail = '/sitemaps/'
        sitemap_url = 'sitemap%2Exml'
        for site in self.list_site:
            # Decoding string to URL
            site_dec = site.replace("://", "%3A%2F%2F").replace(".", "%2E").replace("/", "%2F")
            # Makes a GET request
            response = self._client.request('GET', url + site_dec + url_tail + site_dec + sitemap_url)
            # Gets response and puts it into variable
            html_body = response.read()
            # Checks if result is empty
            if not re.search('not found', html_body):
                # Opens a new Firefox browser with FirefoxProfile "fp"
                try:
                    driver = webdriver.Firefox(firefox_profile=fp)
                    try:
                        # Loads the page at the given URL
                        driver.get("https://www.google.com/webmasters/tools/sitemap-list?hl=en&siteUrl=" + site)
                        # Find element Email and send our username (email)
                        driver.find_element_by_id("Email").send_keys(self._username)
                        # Find element Email and send our password
                        driver.find_element_by_id("Passwd").send_keys(self._password)
                        # Find element button with id signIn
                        signin = driver.find_element_by_id("signIn")
                        # Click button SignIn
                        signin.click()
                        # Wait until the page completely loaded. Equivalent of document.ready
                        driver.implicitly_wait(10) # 10 seconds

                        # Find element button with id gwt-uid-163
                        button = driver.find_element_by_id("gwt-uid-163")
                        # Click button Download All
                        button.click()
                        # Find element button with class GOJ0WDDBBU GOJ0WDDBMU
                        button_ok = driver.find_element_by_css_selector("button[class='GOJ0WDDBBU GOJ0WDDBMU']")
                        # Pressing first button. (OK)
                        button_ok.click()
                        # Quits the driver and close every associated window.
                        driver.quit()
                    except:
                        # Quits the driver and close every associated window.
                        driver.quit()
                except:
                    sys.exit()
        # Stops virtual display
        display.stop()

        # Open CSV files for parsing
        list_files = glob.glob('*_Sitemaps.csv')

        # Creates the Insert construct, which represents an INSERT statement.
        # This is typically created relative to its target table
        insert_query = self.sitemaps.insert()
        for file in list_files:
            # Gets site
            site = ''.join(["http://", (file.split("_")[0]).replace("-", "."), "/"])
            # Gets date
            #fdate = (file.split("_")[-1]).split("-")[0]
            # Check if file contains only header (byte)
            if os.path.getsize(file) == 271:
                pass
            else:
                with open(file, 'rb') as csvfile:
                    # Skip first line. This is a header
                    # Return the next row of the reader’s iterable object as a list, parsed according to the current dialect.
                    next(csvfile)
                    # Return a reader object which will iterate over lines in the given csvfile.
                    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
                    for row in csv_reader:
                        # Makes sure result is not empty
                        if row != []:
                            try:
                                # Try to insert data into table
                                self.pgconn.execute(insert_query, site_id=self.dict_site.get(site),
                                                    sitemap=row[0], type=row[1], date_processed=row[2],
                                                    date_submitted=row[3], submitted_by_me=row[4],
                                                    number_of_warnings=row[5], number_of_errors=row[6],
                                                    submitted_web=row[7], indexed_web=row[8], submitted_images=row[9],
                                                    indexed_images=row[10], submitted_video=row[11], indexed_video=row[12],
                                                    submitted_news=row[13], indexed_news=row[14], submitted_mobile=row[15],
                                                    indexed_mobile=row[16], submitted_app_pages=row[17],
                                                    indexed_app_pages=row[18])
                            # Pass if an Integrity Error has occurred
                            except exc.IntegrityError:
                                pass
                            # Pass any other exception
                            except Exception:
                                pass

    def SetDateRange(self, startDt = None, endDt = None):
        """
        Method sets Start date and End date. Default: None

        Args:
          startDt: string. Start period
          endDt: string. End period.

        """

        if startDt is not None:
            self._startDt = startDt
        if endDt is not None:
            self._endDt = endDt

    def _GetFullUrl(self, path):
        """Construct an absolute URL using path segment.

        Args:
          path: The path segment of a URL.

        Returns:
          A URL giving the absolute path to a resource.
        """
        return 'https://' + self.HOST + path

    def _DownloadFile(self, path):
        """Download the file and write it to disk.

        Downloads the file based on the given URL.  The file name of the download
        is included in the header.  Prints the file name to standard out.

        Args:
          path: The path segment of the URL to download.

        """

        new_path = None
        # List of object for download
        _downloaded = []
        # Set datetime period
        if self._startDt is not None and self._endDt is not None:
            new_path = path + self.DATE_FILTER % (self._startDt, self._endDt)
        else:
            new_path = path
        # Convert to Full URL
        url = self._GetFullUrl(new_path)
        # Make a GET request
        in_stream = self._client.request('GET', url)
        # Getting header from response
        file_name = in_stream.getheader(self.FILE_NAME_HEADER)
        # Looking for filename in header
        file_name = file_name.lstrip(self.TEXT_BEFORE_NAME)
        # Add filename into list of download
        _downloaded.append(file_name)
        new_file_name = file_name

        # Open a file for writing, and make sure to close it,
        with open(new_file_name, 'w') as out_file:
            print >> out_file, in_stream.read()

        in_stream.close()

    def cleaner(self):
        """
        Method cleans up after themselves. Removes temp files.
        """

        # Close connection to database
        self.pgconn.close()
        # Delete all downloaded csv files.
        for tmp in glob.glob('*.csv'):
            os.unlink(tmp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This is a tool for collecting information about site from Google WMT')
    parser.add_argument('-u', '--user', help='Google login', required=True)
    parser.add_argument('-p', '--password', help='Google password', required=True)
    args = parser.parse_args()
    #child = Collect_WMT('', '')
    child = Collect_WMT(args.user, args.password)
    try:
        child.get_site()
        child.collect_messages()
        child.collect_html_improvements()
        child.collect_top_queries()
        child.collect_top_pages()
        child.collect_top_queries_chart()
        child.collect_inbound_links()
        child.collect_index_status()
        child.collect_crawl_errors()
        child.collect_sitemaps()
        child.cleaner()
    except (KeyboardInterrupt, SystemExit):
        child.cleaner()
    except:
        child.cleaner()
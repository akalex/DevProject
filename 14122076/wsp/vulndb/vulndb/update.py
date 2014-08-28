import os,sys
import urllib2
import tarfile
import hashlib
from . import vulnDB
from . import config

'''
update.py -  Class to update the vulndb.db correlated and aggregated vulnerability database

'''

class vulnDBUpdate(object):
    '''
    Download the vulndb.db tgz'd file
    Check for the checksum and decompress
    Do not interrupt the process. If something wrong, it will flag it
    The support for proxy will be added later on (or if you got the guts to do it, be my guest)
    '''
    def __init__(self):
        
        self.configData = config.database['primary']
        self.vulndb_db_primary_url =  self.configData['url']
        self.vulndb_db_compressed  = self.configData['vulndb_db_compressed']
        self.vulndb_db  = self.configData['vulndb_db']
        self.updateStatus = self.configData['updateStatus']     
        self.urlCompressed = self.vulndb_db_primary_url + self.vulndb_db_compressed
        self.urlUpdate = self.vulndb_db_primary_url + self.updateStatus
        
    def update(self):
        '''
            Download the db and decompress it
            Output : vulndb.db
        '''
    
        if not os.path.isfile(self.vulndb_db):
            print '[install] getting fresh copy of %s. It may take a while ...' %self.vulndb_db
            self._updateDB(self.urlCompressed)
            print '\n[info] decompressing %s ...' %self.vulndb_db_compressed
            self._uncompress()
            self.cleaning()
            exit(0)
            
        if os.path.isfile(self.vulndb_db):
            print '[info] checking for the latest %s ' %self.vulndb_db
            self._checkDBversion()
    
    def _updateDB(self,url):
        '''
        This function was found on internet.
        So thanks to its author wherever he is.
        '''
        
        self.filename = url.split('/')[-1]
        self.u = urllib2.urlopen(url)
        self.f = open(self.filename, 'wb')
        self.meta = self.u.info()
        self.filesize = int(self.meta.getheaders("Content-Length")[0])
        
        self.filesize_dl = 0
        self.block_sz = 8192
        while True:
            sys.stdout.flush()
            self.buffer = self.u.read(self.block_sz)
            if not self.buffer:
                break
        
            self.filesize_dl += len(self.buffer)
            self.f.write(self.buffer)
            self.status = r"%10d [%3.0f %%]" % (self.filesize_dl, self.filesize_dl * 100. / self.filesize)
            self.status = self.status + chr(8)*(len(self.status)+1)
            sys.stdout.write("\r[progress %3.0f %%] receiving %d out of %s Bytes of %s " % (self.filesize_dl * 100. / self.filesize, self.filesize_dl,self.filesize,self.filename))
            sys.stdout.flush()
        
        self.f.close()
    
        
    def _uncompress(self):
        '''
        uncompress the tgz db
        '''        
        if not os.path.isfile(self.vulndb_db_compressed):
            print '[error] ' + self.vulndb_db_compressed + ' not found'
            print '[info] Get manually your copy from %s' % self.config.database['primary']['url']
            exit(0)
        
        try:
            tar = tarfile.open(self.vulndb_db_compressed, 'r:gz')
            tar.extractall('.')
            self.tar.close            
        except:
            print '[error] Database not extracted.'
         
     
    def _checkDBversion(self):
        '''
        updating the existing vulndb database if needed
        '''
        self._updateDB(self.urlUpdate)     
        self.hashLocal = self.checksumfile(self.vulndb_db)
        with open(self.updateStatus,'r') as f:
            self.output = f.read()
            self.hashRemote = self.output.split(',')[1]
        
        if self.hashRemote <> self.hashLocal:
            print '[New Update] Downloading the recent vulnDB Database %s from %s' %(self.vulndb_db_compressed,self.vulndb_db_primary_url)            
            self._updateDB(self.urlCompressed)
            print '[info] Decompressing %s ...' %self.vulndb_db_compressed
            self._uncompress()
            self.cleaning()
            exit(0)
            
        if self.hashRemote == self.hashLocal:
            print '\n[info] You have the latest %s vulnerability database' %self.vulndb_db
            self.cleaning()
            
    def checksumfile(self,file):
        '''
        returning the sha1 hash value 
        '''
        self.sha1 = hashlib.sha1()
        self.f = open(file, 'rb')
        try:
            self.sha1.update(self.f.read())
        finally:
            self.f.close()
        return self.sha1.hexdigest()
    
    def cleaning(self):
        '''
        Cleaning the tgz and .dat temporary files 
        '''
        print '[info] Cleaning compressed database and update file'
        try:
            if os.path.isfile(self.vulndb_db_compressed):
                os.remove(self.vulndb_db_compressed)
            if os.path.isfile(self.updateStatus):
                os.remove(self.updateStatus)
        except:
            print '[exception] Already cleaned'
    
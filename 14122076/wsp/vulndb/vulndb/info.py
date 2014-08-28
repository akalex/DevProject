from . import config

'''
info.py -  vulnDB - Open Source Cross-linked and Aggregated Local Vulnerability Database

Class vulnDBInfo : supplying the vulnDB information
'''


class vulnDBInfo(object):
    def __init__(self):
        self.vulnDBInfo = {}

    def get_version(self):
        self.vulnDBInfo['title'] = config.product['__title__']
        self.vulnDBInfo['build'] = config.product['__build__']
        return self.vulnDBInfo

    def get_owner(self):

        self.vulnDBInfo['author'] = config.author['__name__']
        self.vulnDBInfo['email'] = config.author['__email__']
        self.vulnDBInfo['website'] = config.author['__website__']
        return self.vulnDBInfo

    def get_config(self):

        self.vulnDBInfo['primary'] = config.database['primary']
        return self.vulnDBInfo
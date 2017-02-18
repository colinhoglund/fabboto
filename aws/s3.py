''' Tools for interacting with S3 '''

from . import utils


class Buckets(utils.CollectionBase):
    ''' Get S3 buckets '''

    CONNECTION_TYPE = 'resource'
    SERVICE = 's3'

    def _all(self):
        ''' Return a collection of S3 buckets '''
        return self.get_connection().buckets.all()

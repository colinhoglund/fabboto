''' Utilities for AWS library '''

import boto3
from itertools import izip_longest


class CollectionBase(object):
    ''' Mixin class for AWS service classes '''
    def __iter__(self):
        ''' Generic generator function that yields
            AWS resources using _all() method '''
        for i in self._all():
            yield i

    def get_connection(self):
        ''' Return an AWS connection object '''
        return get_connection(self.CONNECTION_TYPE, self.SERVICE)


class ProjectionFilter(object):
    ''' JMESPath projection based filtering '''

    def __init__(self):
        self._aggregates = {}
        self._filters = {}

    def add_aggregate(self, key, values):
        ''' add aggregates to JMESPath filter projection '''
        self._aggregates[key] = str_to_list(values)

    def add_filter(self, key, values):
        ''' add filters to JMESPath filter projection '''
        self._filters[key] = str_to_list(values)

    def __str__(self):
        ''' Output the JMESPath filter projection as a string '''
        query = ""
        if self._aggregates:
            query += "?("
            for key in self._aggregates.iterkeys():
                for value in self._aggregates[key]:
                    query += "{} == '{}' || ".format(key, value)
            # slice off the trailing OR ' || '
            query = query[:-4]
            query += ")"
        if self._filters:
            if self._aggregates:
                query += " && "
            else:
                query += "?"
            for key in self._filters.iterkeys():
                query += "("
                for value in self._filters[key]:
                    query += "{} == '{}' || ".format(key, value)
                # slice off the trailing OR ' || '
                query = query[:-4]
                query += ") && "
            # slice off the trailing AND ' && '
            query = query[:-4]

        return query


class CollectionFilter(object):
    ''' AWS resource filtering '''

    def __init__(self):
        self.filters = []

    def append(self, key, values):
        self.filters.append({'Name': key, 'Values': str_to_list(values)})

    def append_dict(self, dictionary, tags=False):
        ''' Translates dictionary into collection filters.

            Set tags=True when passed in dictionary keys are tag keys
            Example: append_dict({'environment': 'prod'}, tags=True)
        '''
        for key, val in dictionary.items():
            if tags:
                key = 'tag:{}'.format(key)
            self.append(key, val)


def get_connection(connection_type, service):
    ''' Return an AWS connection object '''
    if connection_type == 'resource':
        return boto3.resource(service)
    if connection_type == 'client':
        return boto3.client(service)


def get_account_id():
    ''' Return the current user's AWS account ID '''
    return boto3.client('sts').get_caller_identity()['Account']


def str_to_list(obj):
    ''' Check if obj is str or unicode and return a list '''
    if isinstance(obj, (str, unicode)):
        return obj.split()
    return obj


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)

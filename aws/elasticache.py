''' Tools for interacting with ElastiCache '''

from . import utils


class CacheClusters(utils.CollectionBase):
    ''' Get cache clusters '''

    CONNECTION_TYPE = 'client'
    SERVICE = 'elasticache'

    def __init__(self, ids=None, engines=None, classes=None):
        ''' Filter cache clusters based on kwargs '''
        self._jmes_filter = utils.ProjectionFilter()
        if ids:
            self._jmes_filter.add_aggregate('CacheClusterId',
                                            utils.str_to_list(ids))
        if engines:
            self._jmes_filter.add_filter('Engine', utils.str_to_list(engines))
        if classes:
            self._jmes_filter.add_filter('CacheNodeType',
                                         utils.str_to_list(classes))

    def _all(self):
        ''' Return a generator that yields cache cluster dictionaries '''
        return self.get_connection().get_paginator(
            'describe_cache_clusters').paginate(ShowCacheNodeInfo=True).search(
                'CacheClusters[{}]'.format(self._jmes_filter))


class ReplicationGroups(utils.CollectionBase):
    ''' Get replication groups '''

    CONNECTION_TYPE = 'client'
    SERVICE = 'elasticache'

    def __init__(self, ids=None):
        ''' Filter replication groups based on kwargs '''
        self._jmes_filter = utils.ProjectionFilter()
        if ids:
            self._jmes_filter.add_aggregate('ReplicationGroupId', ids)

    def _all(self):
        ''' Return a generator that yields replication group dictionaries '''
        return self.get_connection().get_paginator(
            'describe_replication_groups').paginate().search(
                'ReplicationGroups[{}]'.format(self._jmes_filter))

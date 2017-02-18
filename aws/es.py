''' Tools for interacting with ElasticSearch Service '''

from . import utils


class Domains(utils.CollectionBase):
    ''' Get Elasticsearch service domains '''

    CONNECTION_TYPE = 'client'
    SERVICE = 'es'

    def __init__(self, domain_names=None):
        ''' Filter ES domains based on kwargs '''
        self._kwargs = {}
        if domain_names:
            self._kwargs['DomainNames'] = utils.str_to_list(domain_names)
        else:
            self._kwargs['DomainNames'] = [
                i['DomainName']
                for i in self.get_connection().list_domain_names()['DomainNames']
            ]

    def _all(self):
        ''' Return a generator that yields ES domains '''
        return self.get_connection().describe_elasticsearch_domains(
            **self._kwargs)['DomainStatusList']

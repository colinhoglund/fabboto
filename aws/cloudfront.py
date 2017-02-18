''' Tools for interacting with CloudFront '''

from . import utils


class Distributions(utils.CollectionBase):
    ''' get CloudFront distributions '''

    CONNECTION_TYPE = 'client'
    SERVICE = 'cloudfront'

    def __init__(self, ids=None, domain_names=None):
        self._jmes_filter = utils.ProjectionFilter()
        if ids:
            self._jmes_filter.add_aggregate('Id', utils.str_to_list(ids))
        if domain_names:
            self._jmes_filter.add_aggregate('DomainName',
                                            utils.str_to_list(domain_names))

    def _all(self):
        return self.get_connection().get_paginator(
            'list_distributions').paginate().search(
                'DistributionList.Items[{}]'.format(self._jmes_filter))

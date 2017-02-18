''' Tools for interacting with AWS Route53 '''

import json
from . import utils


class Zones(utils.CollectionBase):
    ''' Get Hosted Zones '''

    CONNECTION_TYPE = 'client'
    SERVICE = 'route53'

    def __init__(self, domains=None):
        ''' Filter zones based on kwargs '''
        self._jmes_filter = utils.ProjectionFilter()
        if domains:
            self._jmes_filter.add_aggregate('Name',
                                            normalize_dnsnames(domains))

    def _all(self):
        ''' Return a generator that yields hosted zone dictionaries '''
        return self.get_connection().get_paginator(
            'list_hosted_zones').paginate().search(
                "HostedZones[{}]".format(self._jmes_filter))


class Records(utils.CollectionBase):
    ''' Get DNS Records '''

    CONNECTION_TYPE = 'client'
    SERVICE = 'route53'

    def __init__(self, names=None, domains=None, types=None):
        ''' Filter DNS records based on kwargs '''
        self._domains = domains
        self._jmes_filter = utils.ProjectionFilter()
        if names:
            self._jmes_filter.add_aggregate('Name', normalize_dnsnames(names))
        if types:
            self._jmes_filter.add_filter('Type', types)

    def _all(self):
        ''' Generator function that yields DNS records '''
        for zone in Zones(self._domains):
            records = self.get_connection().get_paginator(
                'list_resource_record_sets'
            ).paginate(
                HostedZoneId=zone['Id']
            ).search(
                "ResourceRecordSets[{}]".format(self._jmes_filter)
            )
            for record in records:
                yield record


class ChangeRecords(object):
    ''' Object for creating change batches to modify Route53 configuration '''

    def __init__(self):
        self._change_dict = {}

    def create(self, name, value, record_type, ttl=300):
        '''add UPSERT(create or update) to change batch'''

        zone_id = get_zone_id_from_fqdn(name)
        self._update_change_dict(zone_id)
        self._change_dict[zone_id]['changes'].append({
            'Action': 'UPSERT', 'ResourceRecordSet': {
                'Name': name,
                'Type': record_type,
                'TTL': ttl,
                'ResourceRecords': [{
                    'Value': value
                }]
            }})

    def delete(self, name):
        '''add DELETE to change batch'''

        zone_id = get_zone_id_from_fqdn(name)
        self._update_change_dict(zone_id)
        self._change_dict[zone_id]['deletes'].append(name)

    def commit(self, dry_run=False):
        '''commit all changes'''
        for zone in self._change_dict.items():
            zone_id = zone[0]
            changes = zone[1]['changes']
            deletes = zone[1]['deletes']

            # check if deletes list has items
            if deletes:
                # add deletes to change batch
                changes += [{'Action': 'DELETE', 'ResourceRecordSet': rec}
                            for rec in Records(deletes)]

            # check if changes list has items
            if changes:
                # output changes
                print json.dumps(changes, sort_keys=True,
                                 indent=2, separators=(',', ': '))
                if not dry_run:
                    # process changes per zone in batches of 50
                    for batch in utils.grouper(changes, 50):
                        utils.get_connection('client', 'route53').change_resource_record_sets(
                            HostedZoneId=zone_id,
                            # use filter to strip NoneType items from batches
                            ChangeBatch={'Changes': filter(None, batch)}
                        )

    def _update_change_dict(self, zone_id):
        '''Build dictionary of records using zone_id as the key'''
        if zone_id not in self._change_dict:
            self._change_dict[zone_id] = {'changes': [],
                                          'deletes': []}

    def __str__(self):
        return json.dumps(self._change_dict, sort_keys=True,
                          indent=2, separators=(',', ': '))


def get_zone_id_from_fqdn(fqdn):
    ''' Strip domain and get hosted zone id '''
    return list(Zones(
        '.'.join(normalize_dnsnames(fqdn).split('.')[-3:])
    ))[0]['Id']


def normalize_dnsnames(items):
    ''' Add . to DNS names. accepts strings and lists '''
    if isinstance(items, (str, unicode)):
        if items[-1] != '.':
            return '{}.'.format(items)
        return items
    return ['{}.'.format(item) if item[-1] != '.' else item for item in items]

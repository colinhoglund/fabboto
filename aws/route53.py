''' Functions for interacting with AWS Route53 '''

import json
import urllib2
import boto3
import ipaddress
from aws import ec2, utils

CONN = boto3.client('route53')

def get_zones(domains=None):
    '''return hosted zones generator'''

    # build JMESPath filter projection
    jmes_filter = utils.FilterProjection()
    if domains:
        jmes_filter.add_aggregate('Name', normalize_dnsnames(domains))

    # use zone paginator to gather all zones
    zone_iter = CONN.get_paginator('list_hosted_zones').paginate()
    return zone_iter.search("HostedZones[{}]".format(jmes_filter))

def get_zone_id_from_fqdn(fqdn):
    '''strip domain and get hosted zone id'''
    return get_zones('.'.join(normalize_dnsnames(fqdn).split('.')[-3:])).next()['Id']

def get_records(names=None, domains=None, types=None):
    '''return records generator'''

    # build JMESPath filter projection
    jmes_filter = utils.FilterProjection()
    if names:
        jmes_filter.add_aggregate('Name', normalize_dnsnames(names))
    if types:
        jmes_filter.add_filter('Type', types)

    # get a list of zone ids based on value of domains
    zone_ids = [zone['Id'] for zone in get_zones(domains)]

    # loop through zone_ids to gather records
    record_generators = []
    for zone_id in zone_ids:
        # use paginator for each zone
        rec_iter = CONN.get_paginator('list_resource_record_sets').paginate(HostedZoneId=zone_id)
        record_generators += rec_iter.search("ResourceRecordSets[{}]".format(jmes_filter))

    # use generator comprehension to return a new generator from a list of generators :D
    return (gen for gen in record_generators)

def get_unused_records():
    '''returns all records currently unused by ec2 instances
     this currently does not handle alias->alias records'''

    # create list of all existing EC2 IPs stopped instances don't have IP addresses
    instances = ec2.get_instances(state='running')
    running_ips = [i.private_ip_address for i in instances]
    running_ips += [i.public_ip_address for i in instances if i.public_ip_address]

    # create list of IPv4Network objects containing AWS cidr ranges
    amazon_json = json.loads(urllib2.urlopen(
        'https://ip-ranges.amazonaws.com/ip-ranges.json').read())['prefixes']
    networks = ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']
    networks += [net['ip_prefix'] for net in amazon_json]
    ranges = [ipaddress.ip_network(net.decode()) for net in networks]

    # add 'A' records with unused IP addresses to unused_records
    # add alias records to new list to be traversed next
    unused_records = []
    alias_records = []
    for record in get_records():
        if record['Type'] == 'A' and record.has_key('ResourceRecords'):
            ip_addr = record['ResourceRecords'][0]['Value']

            # only add to unused_records if IP is not used by a
            # running instance and IP is in an AWS address range
            if (ip_addr not in running_ips
                    and True in [ipaddress.ip_address(ip_addr.decode()) in net for net in ranges]):
                unused_records.append(record)
        elif record['Type'] == 'CNAME' or record.has_key('AliasTarget'):
            alias_records.append(record)

    # search for alias records that point at unused A records
    unused_names = [rec['Name'] for rec in unused_records]
    for record in alias_records:
        if (record.has_key('ResourceRecords')
                and record['ResourceRecords'][0]['Value'] in unused_names):
            unused_records.append(record)
        elif record.has_key('AliasTarget') and record['AliasTarget']['DNSName'] in unused_names:
            unused_records.append(record)

    return unused_records

class ChangeRecords(object):
    '''object used for creating change batches'''

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
                            for rec in get_records(deletes)]

            # check if changes list has items
            if changes:
                # output changes
                print json.dumps(changes, sort_keys=True, indent=2, separators=(',', ': '))
                if not dry_run:
                    batch_size = 50
                    batches = [changes[i:i+batch_size] for i in range(0, len(changes), batch_size)]
                    # process changes per zone in batches
                    for batch in batches:
                        CONN.change_resource_record_sets(HostedZoneId=zone_id,
                                                         ChangeBatch={'Changes': batch})

    def _update_change_dict(self, zone_id):
        '''build dictionary of records using zone_id as the key'''
        if not self._change_dict.has_key(zone_id):
            self._change_dict[zone_id] = {'changes': [],
                                          'deletes': []}

    def __str__(self):
        return json.dumps(self._change_dict, sort_keys=True, indent=2, separators=(',', ': '))

def normalize_dnsnames(items):
    ''' add . to DNS names. accepts strings and lists '''
    if isinstance(items, str):
        if items[-1] != '.':
            return '{}.'.format(items)
        return items
    return ['{}.'.format(item) if item[-1] != '.' else item for item in items]

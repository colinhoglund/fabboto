''' Functions for interacting with AWS Route53 '''

import json
import urllib2
import boto3
import ipaddress
from aws import ec2, utils

CONN = boto3.client('route53')

def get_zones(domains=None):
    '''return hosted zones'''

    # build JMESPath filter projection
    jmes_filter = utils.FilterProjection()
    if domains:
        jmes_filter.add_aggregate('Name', _normalize_dnsnames(domains))

    # use zone paginator to gather all zones
    zone_iter = CONN.get_paginator('list_hosted_zones').paginate()
    return list(zone_iter.search("HostedZones[{}]".format(jmes_filter)))

def get_zone_ids(domains=None):
    '''return a list of zone_ids'''
    return [zone['Id'] for zone in get_zones(domains)]

def get_records(names=None, domains=None, types=None):
    '''return records'''

    # build JMESPath filter projection
    jmes_filter = utils.FilterProjection()
    if names:
        jmes_filter.add_aggregate('Name', _normalize_dnsnames(names))
    if types:
        jmes_filter.add_filter('Type', types)

    # get a list of zone ids based on value of domains
    zone_ids = get_zone_ids(domains)

    # loop through zone_ids to gather records
    records = []
    for zone_id in zone_ids:
        # use paginator for each zone
        rec_iter = CONN.get_paginator('list_resource_record_sets').paginate(HostedZoneId=zone_id)
        records += list(rec_iter.search("ResourceRecordSets[{}]".format(jmes_filter)))
    return records

def get_unused_records():
    '''returns all records currently unused by ec2 instances
     this currently does not handle alias->alias records'''

    # create list of all existing EC2 IPs
    # stopped instances don't have IP addresses
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

def create_records():
    '''create records'''
    return None

def delete_records(names):
    '''delete records'''

    names = utils.str_to_list(names)

    # build dictionary of records using zone_id as the key
    records = {}
    for name in names:
        domain = '.'.join(_normalize_dnsnames(name).split('.')[-3:])
        if not records.has_key(domain):
            records[domain] = []
        records[domain].append(name)

    for domain in records.items():
        print domain
        print get_records(names=domain[1])

    return None

def _normalize_dnsnames(items):
    ''' add . to DNS names '''
    if isinstance(items, str):
        if items[-1] != '.':
            return '{}.'.format(items)
        return items
    return ['{}.'.format(item) if item[-1] != '.' else item for item in items]

''' Functions for interacting with AWS Route53 '''
import socket
import json
import urllib2
import boto3
import ipaddress
from aws import ec2, jmespath

CONN = boto3.client('route53')

def get_zones(domains=None):
    'return hosted zones'

    # get zones for specified domains
    jmes_filter = jmespath.FilterProjection()
    if domains:
        # convert string arg to list and normalize dns name with a .
        domains = _normalize_dnsname(_str_to_list(domains))

        jmes_filter.add_aggregate('Name', domains)

    # use zone paginator to gather all zones
    zone_iter = CONN.get_paginator('list_hosted_zones').paginate()
    return list(zone_iter.search("HostedZones[{}]".format(jmes_filter)))

def get_zone_ids(domains=None):
    'return a dict of {domain: zone_id}'
    return [zone['Id'] for zone in get_zones(domains)]

def get_records(names=None, domains=None, types=None):
    'return records'

    jmes_filter = jmespath.FilterProjection()
    if names:
        names = _normalize_dnsname(_str_to_list(names))
        jmes_filter.add_aggregate('Name', names)
    if types:
        types = _str_to_list(types)
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
    ips = [i.private_ip_address for i in instances]
    ips += [i.public_ip_address for i in instances if i.public_ip_address]

    # create list of all aws cidr ranges
    amazon_json = json.loads(urllib2.urlopen(
        'https://ip-ranges.amazonaws.com/ip-ranges.json').read())['prefixes']
    networks = ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']
    networks += [net['ip_prefix'] for net in amazon_json]
    # create list of IPv4Network objects
    ranges = [ipaddress.ip_network(net.decode()) for net in networks]

    unused_records = []
    alias_records = []
    # add records with unused IP addresses to unused_records
    # add alias records to new list to be traversed later
    for record in get_records():
        if record.has_key('ResourceRecords'):
            if record['Type'] == 'A':
                ip_addr = record['ResourceRecords'][0]['Value']
                ip_addr_obj = ipaddress.ip_address(ip_addr.decode())
                if [ip_addr_obj for net in ranges if ip_addr_obj in net]:
                    try:
                        socket.gethostbyaddr(ip_addr)
                    except socket.herror:
                        unused_records.append(record)
                elif ip_addr not in ips:
                    unused_records.append(record)
            if record['Type'] == 'CNAME':
                alias_records.append(record)
        if record.has_key('AliasTarget'):
            alias_records.append(record)

    # search for alias records that point at unused records
    unused_names = [rec['Name'] for rec in unused_records]
    for record in alias_records:
        if record.has_key('ResourceRecords'):
            target = record['ResourceRecords'][0]['Value']
            if target in unused_names:
                unused_records.append(record)
        if record.has_key('AliasTarget'):
            target = record['AliasTarget']['DNSName']
            if target in unused_names:
                unused_records.append(record)

    return unused_records

def delete_records(names):
    'create hosted zone'

    names = _str_to_list(names)

    # build dictionary of records using zone_id as the key
    records = {}
    for name in names:
        domain = '.'.join(name.split('.')[-2:])
        if not records.has_key(domain):
            records[domain] = []
        records[domain].append(name)

    for domain in records.items():
        print domain
        print get_records(names=domain[1])

    return None

def _str_to_list(obj):
    if isinstance(obj, str):
        return obj.split()
    return obj

def _normalize_dnsname(items):
    return ['{}.'.format(item) if item[-1] != '.' else item for item in items]

''' Functions for interacting with AWS Route53 '''
import boto3
from aws import ec2, jmespath

CONN = boto3.client('route53')

def get_zones(domains=None):
    'return hosted zones'

    # get zones for specified domains
    jmes_filter = jmespath.FilterProjection()
    if domains:
        # convert string arg to list and normalize dns name with a .
        domains = _str_to_list(domains)
        domains = ['{}.'.format(x) if x[-1] != '.' else x for x in domains]

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

def get_unused_records(domains=None, types=None):
    'returns all records currently unused by ec2 instances'
    # this currently only checks running instances
    #instances = ec2.get_instances()
    instances = ec2.get_instances(state='running')
    ips = []
    for instance in instances:
        if instance.private_ip_address:
            ips.append(instance.private_ip_address)
        if instance.public_ip_address:
            ips.append(instance.public_ip_address)

    unused_records = []
    # this needs to be refactored to do checks after the list of
    # unused_records is complete. Likely in the following order
    # A -> CNAME -> Alias -> CNAME again
    for record in get_records(domains, types)['ResourceRecordSets']:
        if record.has_key('ResourceRecords'):
            if record['Type'] == 'A':
                if record['ResourceRecords'][0]['Value'] not in ips:
                    unused_records.append(record['Name'])
            if record['Type'] == 'CNAME':
                if record['ResourceRecords'][0]['Value'] in unused_records:
                    unused_records.append(record['Name'])

        if record.has_key('AliasTarget'):
            if record['AliasTarget']['DNSName'] in unused_records:
                unused_records.append(record['Name'])

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

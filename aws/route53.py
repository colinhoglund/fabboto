""" Functions for interacting with AWS Route53 """
import boto3
from aws import ec2

CONN = boto3.client('route53')

def get_zones(domain=None):
    'return all hosted zones'

    # append missing period from domain
    if domain and domain[-1] != '.':
        domain += '.'

    # use zone paginator to determine HostedZoneId
    zone_iter = CONN.get_paginator('list_hosted_zones').paginate()

    # build out own zone dictionary when domain in specified
    zones = {u'HostedZones': []}
    if domain:
        zone = zone_iter.search("HostedZones[?Name == '{}']".format(domain))
        zones['HostedZones'].append(list(zone)[0])
        return zones
    return list(zone_iter)[0]

def get_records(domain=None, type=None):
    'return records'

    domain_id = get_zones(domain)['HostedZones'][0]['Id']
    # use record paginator to return list of RecordSets
    rec_iter= CONN.get_paginator('list_resource_record_sets').paginate(HostedZoneId=get_zones(domain))
    if type:
        return list(rec_iter.search("ResourceRecordSets[?Type == '{}']".format(type)))
    return list(rec_iter.search('ResourceRecordSets'))

    if domain:
        return CONN.list_resource_record_sets(HostedZoneId=get_zones(domain))

    zones = {zone['Name']: zone['Id'] for zone in get_zones()['HostedZones']}

    records = {u'ResourceRecordSets': []}
    for zone in zones.items():
        tmp_records = CONN.list_resource_record_sets(HostedZoneId=zones[zone[0]])
        records['ResourceRecordSets'] += tmp_records['ResourceRecordSets']
    return records

def get_unused_records(domain=None):
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
    for record in get_records(domain)['ResourceRecordSets']:
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

''' Functions for interacting with AWS Route53 '''
import boto3
from aws import ec2

CONN = boto3.client('route53')

def get_zones(domains=None):
    'return hosted zones'

    # use zone paginator to gather all zones
    zone_iter = CONN.get_paginator('list_hosted_zones').paginate()
    zones = list(zone_iter)[0]

    # get zones for specified domains
    if domains:
        # cast domains to list to accept str or list
        if isinstance(domains, str):
            domains = domains.split()

        zone_list = []
        for domain in domains:
            # append missing period
            if domain[-1] != '.':
                domain += '.'

            # append domain to zones
            zone_list += list(zone_iter.search("HostedZones[?Name == '{}']".format(domain)))
        zones['HostedZones'] = zone_list
    return zones

def get_records(domains=None, record_types=None):
    'return records'

    # get a list of zone ids based on value of domains
    zone_ids = [zone['Id'] for zone in get_zones(domains)['HostedZones']]

    # use record paginator to initialize return value
    rec_iter = CONN.get_paginator('list_resource_record_sets').paginate(HostedZoneId=zone_ids[0])
    records = list(rec_iter)[0]

    # loop through zone_ids to gather records
    rec_list = []
    for zone_id in zone_ids:
        # use paginator for each zone
        rec_iter = CONN.get_paginator('list_resource_record_sets').paginate(HostedZoneId=zone_id)

        # search only for specified record types
        if record_types:
            # cast records_types to list to accept str or list
            if isinstance(record_types, str):
                record_types = record_types.split()

            # search for specified record types and add them to rec_list
            for rec_type in record_types:
                rec_search = rec_iter.search("ResourceRecordSets[?Type == '{}']".format(rec_type))
                rec_list += list(rec_search)
        # add all records in zone to rec_list
        else:
            rec_list += list(rec_iter)[0]['ResourceRecordSets']

    # update records and return
    records['ResourceRecordSets'] = rec_list
    return records

def get_unused_records(domains=None, record_types=None):
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
    for record in get_records(domains, record_types)['ResourceRecordSets']:
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

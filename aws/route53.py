""" Functions for interacting with AWS Route53 """
import boto3

CONN = boto3.client('route53')

def get_record_sets(zone, record_type=None):
    """ Get a list of record sets for a specified zone """

    # add trailing dot
    if zone[-1] != '.':
        zone += '.'

    # use zone paginator to determine HostedZoneId
    zone_iter = CONN.get_paginator('list_hosted_zones').paginate()
    zone = list(zone_iter.search("HostedZones[?Name == '{}'].Id".format(zone)))[0]

    # use record paginator to return list of RecordSets
    rec_paginator = CONN.get_paginator('list_resource_record_sets').paginate(HostedZoneId=zone)
    if record_type:
        rec_iter = rec_paginator.search("ResourceRecordSets[?Type == '{}']".format(record_type))
    else:
        rec_iter = rec_paginator.search('ResourceRecordSets')
    return list(rec_iter)

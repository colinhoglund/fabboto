""" Functions for interacting with EC2 """
import boto3

def get_instances(state=None, tags=None):
    """ Get ec2 instances based on filters. """
    ec2 = boto3.resource('ec2')
    ec2_filter = []

    # apply filters based on arguments
    if state:
        ec2_filter.append({'Name': 'instance-state-name', 'Values': [state]})
    if tags:
        _add_tag_filters(tags, ec2_filter)

    #return a collection of ec2 instances
    return ec2.instances.filter(Filters=ec2_filter)

def get_snapshots(owner_id, status=None, tags=None):
    """ Get ec2 snapshots based on filters """
    ec2 = boto3.resource('ec2')
    ec2_filter = []

    # apply filters based on arguments
    ec2_filter.append({'Name': 'owner-id', 'Values': [owner_id]})

    if status:
        ec2_filter.append({'Name': 'status', 'Values': [status]})
    if tags:
        _add_tag_filters(tags, ec2_filter)

    #return a collection of ec2 snapshots
    return ec2.snapshots.filter(Filters=ec2_filter)

def _add_tag_filters(tags, ec2_filter):
   for tag in tags.iteritems():
       ec2_filter.append({'Name': 'tag:{0}'.format(tag[0]), 'Values': [tag[1]]})

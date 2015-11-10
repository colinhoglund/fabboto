""" Functions for interacting with EC2 """
import boto3

def get_instances(state=None, tags=None):
    """
    Get ec2 instances based on filters.

    Parameters
        state: string
        tags: dictionary
            ex: {'Name': 'web2', 'InVPC': 'True'}

    Returns a boto3 collection
    """
    ec2 = boto3.resource('ec2')
    ec2_filter = []

    # apply filters based on arguments
    if state:
        ec2_filter.append({'Name': 'instance-state-name', 'Values': [state]})
    if tags:
        for tag in tags.iteritems():
            ec2_filter.append({'Name': 'tag:{0}'.format(tag[0]), 'Values': [tag[1]]})

    #return a collection of ec2 instances
    return ec2.instances.filter(Filters=ec2_filter)

def get_snapshots(owner_id):
    """
    Get ec2 snapshots based on filters
    """
    ec2 = boto3.resource('ec2')
    ec2_filter = []

    ec2_filter.append({'Name': 'owner-id', 'Values': [owner_id]})

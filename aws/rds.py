""" Functions for interacting with RDS """
import boto3
#from aws import exceptions
#from botocore.exceptions import ClientError

CONN = boto3.client('rds')

#def get_instances(ids=None, state=None, tags=None):
#    """ Get rds instances. """

def get_snapshots(instance_id=None, snapshot_id=None, snapshot_type=None):
    """ Get rds snapshots """

    # build pagination arguments
    kwargs = {}
    if instance_id:
        kwargs['DBInstanceIdentifier'] = instance_id
    if snapshot_id:
        kwargs['DBSnapshotIdentifier'] = snapshot_id
    if snapshot_type:
        kwargs['SnapshotType'] = snapshot_type

    iterator = CONN.get_paginator('describe_db_snapshots').paginate(**kwargs)
    return list(iterator.search('DBSnapshots[].DBSnapshotIdentifier'))

#def resize_instances(instances, instance_type, force=False, dry_run=False):

#def _valid_rds_instance_type(instance_type):
#    """ verify that instance_type is valid """
#    try:
#        CONN.create_instances(DryRun=True, ImageId='ami-d05e75b8',
#                              MinCount=1, MaxCount=1, InstanceType=instance_type)
#    except ClientError as ex:
#        if 'InvalidParameterValue' in ex.message:
#            return False
#        return True

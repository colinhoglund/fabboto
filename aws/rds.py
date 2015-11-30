""" Functions for interacting with RDS """
import boto3
#from aws import exceptions
#from botocore.exceptions import ClientError

CONN = boto3.client('rds')

def get_instances(instance_id=None):
    """ Get rds instances. """

    kwargs = {}
    if instance_id:
        kwargs['DBInstanceIdentifier'] = instance_id

    iterator = CONN.get_paginator('describe_db_instances').paginate(**kwargs)
    return list(iterator.search('DBInstances[?].DBInstanceIdentifier'))

def get_snapshots(instance_ids=None, snapshot_ids=None, snapshot_type=None):
    """ Get rds snapshots """

    # build JMESPath query
    jmes_query = "? "
    if instance_ids:
        for inst in instance_ids:
            jmes_query += "DBInstanceIdentifier == '{}' || ".format(inst)
    if snapshot_ids:
        for snap in snapshot_ids:
            jmes_query += "DBSnapshotIdentifier == '{}' || ".format(snap)
   # slice off the trailing OR ' || '
    jmes_query = jmes_query[:-4]

    # build pagination arguments
    kwargs = {}
    if snapshot_type:
        kwargs['SnapshotType'] = snapshot_type

    iterator = CONN.get_paginator('describe_db_snapshots').paginate(**kwargs)
    return list(iterator.search('DBSnapshots[{}].DBSnapshotIdentifier'.format(jmes_query)))

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

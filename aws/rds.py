""" Functions for interacting with RDS """
import boto3
#from aws import exceptions
#from botocore.exceptions import ClientError

CONN = boto3.client('rds')

def get_instances(ids=None):
    """ Get rds instances

    Returns a list of RDS instances. Calling with no arguments returns all RDS instances.

    Args:
        ids (list): a list of RDS instance identifiers

    Returns:
        list: a list of DBInstanceIdentifiers
    """

    # build JMESPath query
    jmes_query = "? "
    if ids:
        for inst in ids:
            jmes_query += "DBInstanceIdentifier == '{}' || ".format(inst)
    # slice off the trailing OR ' || '
    jmes_query = jmes_query[:-4]

    iterator = CONN.get_paginator('describe_db_instances').paginate()
    return list(iterator.search('DBInstances[{}].DBInstanceIdentifier'.format(jmes_query)))

def get_snapshots(instance_ids=None, snapshot_ids=None, snapshot_type=None):
    """ Get rds snapshots

    Returns a list of RDS snapshots. Calling with no arguments returns all RDS snapshots.

    Args:
        instance_ids (Optional[list]): a list of RDS instance identifiers. Defaults to None
        snapshot_ids (Optional[list]): a list of RDS snapshot identifiers. Defaults to None
        snapshot_type (Optional[str]): type of snapshot (manual, automated). Defaults to None

    Returns:
        list: a list of DBSnapshotIdentifiers
    """

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

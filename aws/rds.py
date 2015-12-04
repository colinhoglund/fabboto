""" Functions for interacting with RDS """
import boto3
from aws import jmespath
#from aws import exceptions
#from botocore.exceptions import ClientError

CONN = boto3.client('rds')

def get_instances(ids=None, engines=None, classes=None):
    """ Get RDS instances

    Returns a list of RDS instances. Calling with no arguments returns all RDS instances.
    Since boto3 does not provide a service resource or collection object for RDS,
    this function uses JMESPath queries for filtering.

    Args:
        ids (Optional[list]): list of RDS instance identifiers. Defaults to None
        engines (Optional[list]): list of database engine types
        classes (Optional[list]): list of DB instance types

    Returns:
        list: a list of DBInstance dictionaries
    """

    # build JMESPath filter projection
    jmes_query = jmespath.FilterProjection()
    if ids:
        jmes_query.add_aggregate('DBInstanceIdentifier', ids)
    if engines:
        jmes_query.add_filter('Engine', engines)
    if classes:
        jmes_query.add_filter('DBInstanceClass', classes)

    iterator = CONN.get_paginator('describe_db_instances').paginate()
    #print jmes_query
    return list(iterator.search('DBInstances[{}]'.format(jmes_query)))

def get_snapshots(instance_ids=None, snapshot_ids=None, snapshot_type=None):
    """ Get rds snapshots

    Returns a list of RDS snapshots. Calling with no arguments returns all RDS snapshots.
    Since boto3 does not provide a service resource or collection object for RDS,
    this function uses JMESPath queries for filtering.

    Args:
        instance_ids (Optional[list]): a list of RDS instance identifiers. Defaults to None
        snapshot_ids (Optional[list]): a list of RDS snapshot identifiers. Defaults to None
        snapshot_type (Optional[str]): type of snapshot (manual, automated). Defaults to None

    Returns:
        list: a list of DBSnapshotIdentifiers
    """

    # build JMESPath query
    jmes_query = jmespath.FilterProjection()
    if instance_ids:
        jmes_query.add_aggregate('DBInstanceIdentifier', instance_ids)
    if snapshot_ids:
        jmes_query.add_aggregate('DBSnapshotIdentifier', snapshot_ids)

    # build pagination arguments
    kwargs = {}
    if snapshot_type:
        kwargs['SnapshotType'] = snapshot_type

    iterator = CONN.get_paginator('describe_db_snapshots').paginate(**kwargs)
    #print jmes_query
    return list(iterator.search('DBSnapshots[{}]'.format(jmes_query)))

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

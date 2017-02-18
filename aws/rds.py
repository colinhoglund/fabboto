''' Tools for interacting with RDS '''

from operator import itemgetter
from . import utils


class Instances(utils.CollectionBase):
    ''' Get RDS instances

    Builds a list of RDS instances. Calling with no arguments
    returns all RDS instances. Since boto3 does not provide a service
    resource or collection object for RDS, this function uses JMESPath
    queries for filtering.

    Args:
        ids (Optional[list]):
            list of RDS instance identifiers. Default: None
        engines (Optional[list]):
            list of database engine types. Default: None
        classes (Optional[list]):
            list of DB instance types. Default: None
        status (Optional[list]):
            list of DB instance statuses. Default: None
    '''

    CONNECTION_TYPE = 'client'
    SERVICE = 'rds'

    def __init__(self, ids=None, engines=None, classes=None, status=None):
        ''' Filter RDS instances based on kwargs '''
        self._jmes_filter = utils.ProjectionFilter()
        if ids:
            self._jmes_filter.add_aggregate('DBInstanceIdentifier',
                                            utils.str_to_list(ids))
        if engines:
            self._jmes_filter.add_filter('Engine',
                                         utils.str_to_list(engines))
        if classes:
            self._jmes_filter.add_filter('DBInstanceClass',
                                         utils.str_to_list(classes))
        if status:
            self._jmes_filter.add_filter('DBInstanceStatus',
                                         utils.str_to_list(status))

    def _all(self):
        ''' Return a generator that yields RDS instance dictionaries '''
        return self.get_connection().get_paginator(
            'describe_db_instances').paginate().search(
                'DBInstances[{}]'.format(self._jmes_filter))


class Snapshots(utils.CollectionBase):
    ''' Get RDS snapshots

    Builds a list of RDS snapshots. Calling with no arguments
    returns all RDS snapshots. Since boto3 does not provide a service
    resource or collection object for RDS, this function uses
    JMESPath queries for filtering.

    Args:
        instance_ids (Optional[list]):
            a list of RDS instance identifiers. Default: None
        snapshot_ids (Optional[list]):
            a list of RDS snapshot identifiers. Default: None
        snapshot_type (Optional[str]):
            type of snapshot (manual, automated). Default: None
        status (Optional[list]):
            list of DB snapshot statuses. Default: None
    '''

    CONNECTION_TYPE = 'client'
    SERVICE = 'rds'

    def __init__(self, instance_ids=None,
                 snapshot_ids=None, snapshot_type=None,
                 status=None):
        ''' Filter RDS snapshots based on kwargs '''
        self._kwargs = {}
        self._jmes_filter = utils.ProjectionFilter()
        if instance_ids:
            self._jmes_filter.add_aggregate('DBInstanceIdentifier',
                                            utils.str_to_list(instance_ids))
        if snapshot_ids:
            self._jmes_filter.add_aggregate('DBSnapshotIdentifier',
                                            utils.str_to_list(snapshot_ids))
        if status:
            self._jmes_filter.add_filter('Status',
                                         utils.str_to_list(status))
        if snapshot_type:
            self._kwargs['SnapshotType'] = snapshot_type

    def _all(self):
        ''' Return a generator that yields RDS snapshots '''
        return self.get_connection().get_paginator(
            'describe_db_snapshots').paginate(**self._kwargs).search(
                'DBSnapshots[{}]'.format(self._jmes_filter))

    def latest(self):
        ''' Return the most recent snapshot '''
        # avoid snapshots that are currently being created
        available_snaps = [snap for snap in self._all() if snap['Status'] == 'available']
        return sorted(available_snaps, key=itemgetter('SnapshotCreateTime'))[-1]


class SecurityGroups(utils.CollectionBase):
    ''' Get RDS security groups '''

    CONNECTION_TYPE = 'client'
    SERVICE = 'rds'

    def __init__(self, names=None):
        ''' Filter RDS security groups based on kwargs '''
        self._jmes_filter = utils.ProjectionFilter()
        if names:
            self._jmes_filter.add_aggregate('DBSecurityGroupName', utils.str_to_list(names))

    def _all(self):
        ''' Return a generator that yields RDS security group dictionaries '''
        return self.get_connection().get_paginator(
            'describe_db_security_groups').paginate().search(
                'DBSecurityGroups[{}]'.format(self._jmes_filter))

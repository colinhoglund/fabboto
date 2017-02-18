''' Tools for interacting with EC2 '''

from botocore.exceptions import ClientError
from operator import attrgetter
from . import utils


class Instances(utils.CollectionBase):
    ''' Get EC2 instances'''

    CONNECTION_TYPE = 'resource'
    SERVICE = 'ec2'

    def __init__(self, ids=None, state=None, tags=None, filters=None):
        ''' Filter instances based on kwargs '''
        self._kwargs = {}
        self._collection_filter = utils.CollectionFilter()
        if state:
            self._collection_filter.append('instance-state-name', state)
        if tags:
            self._collection_filter.append_dict(tags, tags=True)
        if filters:
            self._collection_filter.append_dict(filters)
        if self._collection_filter.filters:
            self._kwargs['Filters'] = self._collection_filter.filters
        if ids:
            self._kwargs['InstanceIds'] = utils.str_to_list(ids)

    def _all(self):
        ''' Return a collection of EC2 instances '''
        return self.get_connection().instances.filter(**self._kwargs)


class Snapshots(utils.CollectionBase):
    ''' Get EC2 snapshots '''

    CONNECTION_TYPE = 'resource'
    SERVICE = 'ec2'

    def __init__(self, owner_ids=utils.get_account_id(), snapshot_ids=None,
                 volume_ids=None, status=None, tags=None):
        ''' Filter snapshots based on kwargs '''
        self._kwargs = {}
        self._collection_filter = utils.CollectionFilter()
        self._collection_filter.append('owner-id', owner_ids)
        if volume_ids:
            self._collection_filter.append('volume-id', volume_ids)
        if status:
            self._collection_filter.append('status', status)
        if tags:
            self._collection_filter.append_dict(tags, tags=True)
        if snapshot_ids:
            self._kwargs['SnapshotIds'] = utils.str_to_list(snapshot_ids)
        self._kwargs['Filters'] = self._collection_filter.filters

    def _all(self):
        ''' Return a collection of ec2 snapshots '''
        return self.get_connection().snapshots.filter(**self._kwargs)

    def latest(self):
        ''' Return the most recent snapshot in the collection '''
        return sorted(self._all(), key=attrgetter('start_time'))[-1]


class Images(utils.CollectionBase):
    ''' Get AMIs '''

    CONNECTION_TYPE = 'resource'
    SERVICE = 'ec2'

    def __init__(self, owner_ids=utils.get_account_id(), image_ids=None,
                 tags=None, state=None, filters=None):
        ''' Filter AMIs based on kwargs '''
        self._kwargs = {}
        self._collection_filter = utils.CollectionFilter()
        if state:
            self._collection_filter.append('state', state)
        if tags:
            self._collection_filter.append_dict(tags, tags=True)
        if filters:
            self._collection_filter.append_dict(filters)
        if self._collection_filter.filters:
            self._kwargs['Filters'] = self._collection_filter.filters
        if image_ids:
            self._kwargs['ImageIds'] = utils.str_to_list(image_ids)
        if owner_ids:
            self._kwargs['Owners'] = utils.str_to_list(owner_ids)

    def _all(self):
        ''' Return a collection of AMIs '''
        return self.get_connection().images.filter(**self._kwargs)


class ElasticLoadBalancers(utils.CollectionBase):
    ''' Get ELBs '''

    CONNECTION_TYPE = 'client'
    SERVICE = 'elb'

    def __init__(self, names=None):
        ''' Filter ELBs based on kwargs '''
        self._kwargs = {}
        if names:
            self._kwargs['LoadBalancerNames'] = utils.str_to_list(names)

    def _all(self):
        ''' Return a generator that yields ELB dictionaries '''
        return self.get_connection().get_paginator(
            'describe_load_balancers').paginate(**self._kwargs).search(
                'LoadBalancerDescriptions[]')


def valid_instance_type(instance_type):
    ''' Verify that instance_type is valid.
        Invalid types raise a ClientError '''
    try:
        utils.get_connection('resource', 'ec2').create_instances(
            DryRun=True, ImageId='ami-d05e75b8',
            MinCount=1, MaxCount=1, InstanceType=instance_type
        )
    except ClientError as e:
        if 'would have succeeded' in e.message:
            return True
        if 'InvalidParameterValue' in e.message:
            return False
        raise e

''' Functions for interacting with EC2 '''

import boto3
from botocore.exceptions import ClientError
from aws import exceptions, utils

CONN = boto3.resource('ec2')

def get_instances(ids=None, state=None, tags=None, filters=None):
    ''' Get ec2 instances based on filters. '''

    # apply filters based on arguments
    filter_list = []
    if state:
        filter_list.append({'Name': 'instance-state-name', 'Values': [state]})
    if tags:
        utils.add_tag_filters(tags, filter_list)
    if filters:
        utils.add_filters(filters, filter_list)

    # build collection filter arguments
    kwargs = {}
    if filter_list:
        kwargs['Filters'] = filter_list
    if ids:
        kwargs['InstanceIds'] = ids

    #return a collection of ec2 instances
    return CONN.instances.filter(**kwargs)

def get_snapshots(owner_id, status=None, tags=None):
    ''' Get ec2 snapshots based on filters '''
    #TODO: volume_ids, snapshot_ids arguments

    # apply filters based on arguments
    filter_list = []
    filter_list.append({'Name': 'owner-id', 'Values': [owner_id]})
    if status:
        filter_list.append({'Name': 'status', 'Values': [status]})
    if tags:
        utils.add_tag_filters(tags, filter_list)

    #return a collection of ec2 snapshots
    return CONN.snapshots.filter(Filters=filter_list)

def resize_instances(instances, instance_type, force=False, dry_run=False):
    ''' Resize instances in ec2.instancesCollection

        WARNING: Use 'force=True' with caution, it potentially scripts at outage!
    '''
    # create a list of instance ids to allow removal of instances from collection
    instance_ids = [i.instance_id for i in list(instances)]
    running_ids = []
    skipped_ids = []

    # return False if instance type is not valid
    if not _valid_ec2_instance_type(instance_type):
        raise exceptions.InvalidInstanceType(
            '{} is not a valid instance type.'.format(instance_type)
        )

    for instance in instances:
        # drop instances from collection that are already the specified instance_type
        if instance.instance_type == instance_type:
            instance_ids.remove(instance.instance_id)
        elif instance.state['Name'] != 'stopped':
            # move running instances to running_ids
            if force and instance.state['Name'] == 'running':
                running_ids.append(instance.instance_id)
            # move all other instances to skipped_ids
            else:
                skipped_ids.append(instance.instance_id)
            # remove from instance_ids
            instance_ids.remove(instance.instance_id)

    # modify stopped instances
    if len(instance_ids) > 0:
        stopped_instances = instances.filter(InstanceIds=instance_ids)
        if dry_run:
            print 'DRYRUN: stopped instances to modify: {}'.format(instance_ids)
        else:
            for instance in stopped_instances:
                instance.modify_attribute(Attribute='instanceType', Value=instance_type)

    # modify running instances with force
    if force and len(running_ids) > 0:
        running_instances = instances.filter(InstanceIds=running_ids)
        if dry_run:
            print 'DRYRUN: running instances to modify: {}'.format(running_ids)
        else:
            # create list of pending changes
            pending_ids = [i.instance_id for i in list(running_instances)]

            # stop running instances (fingers crossed...)
            running_instances.stop()

            '''
            repeatedly loop through instances until all pending_ids have been processed.
            this allows instances to come up as they're ready, rather than waiting for
            the previous item in running_instances
            '''
            while len(pending_ids) > 0:
                for instance in running_instances:
                    try:
                        instance.modify_attribute(Attribute='instanceType', Value=instance_type)
                        instance.start()
                        pending_ids.remove(instance.instance_id)
                    except ClientError:
                        continue

    # print out skipped instances
    if len(skipped_ids) > 0:
        skipped_instances = instances.filter(InstanceIds=skipped_ids)
        for instance in skipped_instances:
            print '{} skipped due to {} state'.format(instance.instance_id, instance.state['Name'])

def _valid_ec2_instance_type(instance_type):
    ''' verify that instance_type is valid '''
    try:
        CONN.create_instances(DryRun=True, ImageId='ami-d05e75b8',
                              MinCount=1, MaxCount=1, InstanceType=instance_type)
    except ClientError as ex:
        if 'InvalidParameterValue' in ex.message:
            return False
        return True

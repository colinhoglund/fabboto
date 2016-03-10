''' Functions for interacting with EC2 '''

import boto3
from botocore.exceptions import ClientError
from aws import utils

CONN = boto3.resource('ec2')

def get_instances(ids=None, state=None, tags=None, filters=None):
    ''' Get ec2 instances based on filters. '''

    # apply filters based on arguments
    filter_list = []
    if state:
        filter_list.append({'Name': 'instance-state-name', 'Values': utils.str_to_list(state)})
    if tags:
        utils.add_tag_filters(tags, filter_list)
    if filters:
        utils.add_filters(filters, filter_list)

    # build collection filter arguments
    kwargs = {}
    if filter_list:
        kwargs['Filters'] = filter_list
    if ids:
        kwargs['InstanceIds'] = utils.str_to_list(ids)

    #return a collection of ec2 instances
    return CONN.instances.filter(**kwargs)

def get_snapshots(owner_id, snapshot_ids=None, volume_ids=None, status=None, tags=None):
    ''' Get ec2 snapshots based on filters '''

    # apply filters based on arguments
    filter_list = []
    filter_list.append({'Name': 'owner-id', 'Values': utils.str_to_list(owner_id)})
    if volume_ids:
        filter_list.append({'Name': 'volume-id', 'Values': utils.str_to_list(volume_ids)})
    if status:
        filter_list.append({'Name': 'status', 'Values': utils.str_to_list(status)})
    if tags:
        utils.add_tag_filters(tags, filter_list)

    kwargs = {}
    if filter_list:
        kwargs['Filters'] = filter_list
    if snapshot_ids:
        kwargs['SnapshotIds'] = utils.str_to_list(snapshot_ids)

    #return a collection of ec2 snapshots
    return CONN.snapshots.filter(**kwargs)

def get_amis(owner_ids, image_ids=None, tags=None, state=None, filters=None):
    ''' get AMIs based on filters '''

    # apply filters based on arguments
    filter_list = []
    if state:
        filter_list.append({'Name': 'state', 'Values': utils.str_to_list(state)})
    if tags:
        utils.add_tag_filters(tags, filter_list)
    if filters:
        utils.add_filters(filters, filter_list)

    # build collection filter arguments
    kwargs = {}
    if filter_list:
        kwargs['Filters'] = filter_list
    if image_ids:
        kwargs['ImageIds'] = utils.str_to_list(image_ids)
    if owner_ids:
        kwargs['Owners'] = utils.str_to_list(owner_ids)

    #return a collection of ec2 instances
    return CONN.images.filter(**kwargs)

def resize_instances(instances, instance_type, force=False, dry_run=False):
    ''' Resize instances in ec2.instancesCollection

        WARNING: Use 'force=True' with caution, it potentially scripts at outage!
    '''
    # create a list of instance ids to allow removal of instances from collection
    instance_ids = [i.instance_id for i in list(instances)]
    running_ids = []
    skipped_ids = []

    # raises ClientError if instance type is not valid
    _validate_ec2_instance_type(instance_type)

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

def _validate_ec2_instance_type(instance_type):
    ''' verify that instance_type is valid. Invalid types raise a ClientError '''
    try:
        CONN.create_instances(DryRun=True, ImageId='ami-d05e75b8',
                              MinCount=1, MaxCount=1, InstanceType=instance_type)
    except ClientError as ex:
        if 'InvalidParameterValue' in ex.message:
            raise ex

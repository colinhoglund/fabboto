""" Functions for interacting with EC2 """
import boto3
from botocore.exceptions import ClientError

def get_instances(ids=[], state=None, tags=None):
    """ Get ec2 instances based on filters. """
    ec2 = boto3.resource('ec2')
    ec2_filter = []

    # apply filters based on arguments
    if state:
        ec2_filter.append({'Name': 'instance-state-name', 'Values': [state]})
    if tags:
        _add_tag_filters(tags, ec2_filter)

    #return a collection of ec2 instances
    return ec2.instances.filter(Filters=ec2_filter, InstanceIds=ids)

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

def resize_instances(instances, instance_type, force=False, dry_run=False):
    """ Resize instances in ec2.instancesCollection

        !!!!Use 'force=True' with caution, it potentially scripts at outage!!!!
    """
    # create a list of instance ids to allow removal of instances from collection
    instance_ids = [ i.instance_id for i in list(instances) ]
    running_ids = []
    skipped_ids = []

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
            print 'DRYRUN: stopped instances to modify: {0}'.format(instance_ids)
        else:
            for instance in stopped_instances:
                instance.modify_attribute(Attribute='instanceType', Value=instance_type)

    # modify running instances with force
    if force and len(running_ids) > 0:
        running_instances = instances.filter(InstanceIds=running_ids)
        if dry_run:
            print 'DRYRUN: running instances to modify: {0}'.format(running_ids)
        else:
            pending_ids = [ i.instance_id for i in list(running_instances) ]
            print pending_ids
            # stop running instances (fingers crossed...)
            running_instances.stop()

            # wait for instances to stop and modify instance_type
            while len(pending_ids) > 0:
                for instance in running_instances:
                    print len(pending_ids)
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
            print '{0} skipped due to {1} state'.format(instance.instance_id, instance.state['Name'])

def _add_tag_filters(tags, ec2_filter):
   for tag in tags.iteritems():
       ec2_filter.append({'Name': 'tag:{0}'.format(tag[0]), 'Values': [tag[1]]})
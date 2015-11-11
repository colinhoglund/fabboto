""" fabfile.py """
from aws import ec2

def resize_dev():
    """ resize all dev hosts """
    instances = ec2.get_instances(tags={'environment':'dev'})
    # dry_run: print out potential changes
    # force: reboot running instances
    ec2.resize_instances(instances, 'm3.large', dry_run=True, force=True)

def print_instances(state=None, tags=None, filters=None):
    """
    Print ec2 instances using ec2.get_instances().

    tags/filters parameter requires special formatting because
    fabric passes all arguments as strings. The 'quotes' are required
    so that the pipe is not parsed by the shell.
        tags='Key:Value|Key:Value|...'

    Example:
    fab print_instances:tags='env:prod|InVPC:True',filters='instance-type:t2.micro|tenancy:default'
    """
    def _create_dict(items):
        """ builds a dict from command line arg """
        item_dict = {}
        for i in items.split('|'):
            arr = i.split(':')
            item_dict[arr[0]] = arr[1]
        return item_dict

    tag_dict = {}
    filter_dict = {}
    # setup filter dictionaries
    if tags:
        tag_dict = _create_dict(tags)
    if filters:
        filter_dict = _create_dict(filters)

    instances = ec2.get_instances(state=state, tags=tag_dict, filters=filter_dict)

    # print all matching names and ids
    for i in instances:
        for tag in i.tags:
            if tag['Key'] == 'Name':
                print '{0}: {1}'.format(tag['Value'], i.instance_id)

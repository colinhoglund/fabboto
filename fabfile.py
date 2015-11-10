from aws import ec2

def resize_dev():
    """ resize all dev hosts """
    instances = ec2.get_instances(tags={'environment':'dev'})
    # dry_run: print out potential changes
    # force: reboot running instances
    ec2.resize_instances(instances, 'm3.large', dry_run=True, force=True)

def print_instances(state=None, tags=None):
    """
    Print ec2 instances using ec2.get_instances().

    tags parameter requires special formatting because
    fabric passes all arguments as strings.
        tags=Key:Value-Key:Value-...

        ex: fab print_instances:state=running,tags=Environment:mgmt-InVPC:True
    """
    # setup tag dictionary
    tag_dict = {}
    if tags:
        for tag in tags.split('-'):
            tag_arr = tag.split(':')
            tag_dict[tag_arr[0]] = tag_arr[1]

    instances = ec2.get_instances(state=state, tags=tag_dict)

    # print all matching names and ids
    for i in instances:
        for tag in i.tags:
            if tag['Key'] == 'Name':
                print '{0}: {1}'.format(tag['Value'], i.instance_id)

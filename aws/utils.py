''' Utilities for AWS library '''

class FilterProjection(object):
    ''' Create JMESPath filter projections '''

    def __init__(self):
        self._aggregates = {}
        self._filters = {}

    def add_aggregate(self, key, values):
        ''' add aggregates to JMESPath filter projection '''
        values = str_to_list(values)
        self._aggregates[key] = values

    def add_filter(self, key, values):
        ''' add filters to JMESPath filter projection '''
        values = str_to_list(values)
        self._filters[key] = values

    def __str__(self):
        ''' Output the JMESPath filter projection as a string '''
        query = ""
        if self._aggregates:
            query += "?("
            for key in self._aggregates.iterkeys():
                for value in self._aggregates[key]:
                    query += "{} == '{}' || ".format(key, value)
            # slice off the trailing OR ' || '
            query = query[:-4]
            query += ")"
        if self._filters:
            if self._aggregates:
                query += " && "
            else:
                query += "?"
            for key in self._filters.iterkeys():
                query += "("
                for value in self._filters[key]:
                    query += "{} == '{}' || ".format(key, value)
                # slice off the trailing OR ' || '
                query = query[:-4]
                query += ") && "
            # slice off the trailing AND ' && '
            query = query[:-4]

        return query

def add_filters(filters, filter_list):
    ''' Translates dictionary object into an collection filter '''
    filters = str_to_list(filters)
    for item in filters.iteritems():
        filter_list.append({'Name': '{}'.format(item[0]), 'Values': [item[1]]})

def add_tag_filters(tags, filter_list):
    ''' Translates dictionary object of tags into an collection filter '''
    tags = str_to_list(tags)
    for tag in tags.iteritems():
        filter_list.append({'Name': 'tag:{}'.format(tag[0]), 'Values': [tag[1]]})

def str_to_list(obj):
    ''' return string arg as a list '''
    if isinstance(obj, str):
        return obj.split()
    return obj

""" Create JMESPath filter projections """

class JMESPath(object):
    """ Create JMESPath filter projections """

    def __init__(self):
        self.aggregates = {}
        self.filters = {}

    def add_aggregate(self, key, values):
        """ add aggregates to JMESPath filter projection """
        self.aggregates[key] = values

    def add_filter(self, key, values):
        """ add filters to JMESPath filter projection """
        self.filters[key] = values

    def __str__(self):
        """ Output the JMESPath filter projection as a string """
        query = "?"
        if self.aggregates:
            query += "("
            for key in self.aggregates.iterkeys():
                for value in self.aggregates[key]:
                    query += "{} == '{}' || ".format(key, value)
            # slice off the trailing OR ' || '
            query = query[:-4]
            query += ")"
        if self.filters:
            if self.aggregates:
                query += " && "
            for key in self.filters.iterkeys():
                query += "("
                for value in self.filters[key]:
                    query += "{} == '{}' || ".format(key, value)
                # slice off the trailing OR ' || '
                query = query[:-4]
                query += ") && "
            # slice off the trailing AND ' && '
            query = query[:-4]

        return query

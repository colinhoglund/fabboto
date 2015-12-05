""" Create JMESPath filter projections """

class FilterProjection(object):
    """ Create JMESPath filter projections """

    def __init__(self):
        self._aggregates = {}
        self._filters = {}

    def add_aggregate(self, key, values):
        """ add aggregates to JMESPath filter projection """
        self._aggregates[key] = values

    def add_filter(self, key, values):
        """ add filters to JMESPath filter projection """
        self._filters[key] = values

    def __str__(self):
        """ Output the JMESPath filter projection as a string """
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

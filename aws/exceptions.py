class InvalidInstanceType(Exception):
    ''' Raised when  an invalid instance type is used '''

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

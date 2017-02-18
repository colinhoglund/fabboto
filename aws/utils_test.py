import unittest
from utils import str_to_list, ProjectionFilter


class UtilsTestCase(unittest.TestCase):
    ''' Test aws.utils objects and functions'''

    def test_str_to_list(self):
        string = 'test'
        self.assertEqual(str_to_list(string), [string])
        self.assertEqual(str_to_list([string]), [string])

    def test_ProjectionFilter(self):
        pfilter = ProjectionFilter()
        pfilter.add_aggregate('DBInstanceIdentifier', 'instance')
        pfilter.add_aggregate('DBSnapshotIdentifier', ['snapshot'])
        pfilter.add_filter('Engine', 'mysql')
        pfilter.add_filter('DBInstanceClass', ['db.t1.micro'])
        self.assertEqual(
            str(pfilter),
            "?(DBSnapshotIdentifier == 'snapshot' || DBInstanceIdentifier == 'instance') && (Engine == 'mysql') && (DBInstanceClass == 'db.t1.micro')"
        )

if __name__ == '__main__':
    unittest.main()

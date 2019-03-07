#!/usr/bin/python3

import unittest

from kolobok.utils import sys_utils


class TestSysUtils(unittest.TestCase):

    def test_get_hardware_id(self):
        try:
            id = sys_utils.get_hardware_id()
            self.assertTrue(isinstance(id, str))
        except Exception as err:
            msg = ' - test_get_hardware_id failed.\n [ %s ]'
            self.assertTrue(False, msg % err)



if __name__ == '__main__':
    unittest.main()
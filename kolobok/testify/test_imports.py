#!/usr/bin/python3
import unittest
import os
import sys
from pdb import set_trace

#path to root of this project where the flask_fat folder is
this_file = os.path.dirname(os.path.abspath(__file__)) + '/../../'
sys.path.insert(0, this_file)

class TestImports(unittest.TestCase):

    def test_import_all(self):
        try:
            import kolobok
            kolobok.utils
            kolobok.utils.sys_utils
            from kolobok import utils
            from kolobok.utils import sys_utils
            self.assertTrue(True, 'Imports: all good.')
        except Exception as err:
            self.assertTrue(False, err)

if __name__ == '__main__':
    unittest.main()

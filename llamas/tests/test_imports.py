#!/usr/bin/python3
import unittest
import os
import sys
from pdb import set_trace

class TestImports(unittest.TestCase):

    def test_import_all(self):
        try:
            import llamas
            from llamas import utils
            from llamas.utils import sys_utils
            self.assertTrue(True, 'Imports: all good.')
        except Exception as err:
            self.assertTrue(False, err)

if __name__ == '__main__':
    unittest.main()

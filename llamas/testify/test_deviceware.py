#!/usr/bin/python3
import unittest
from pdb import set_trace

from app_test import AppTesting
from llamas.controls import deviceware

class TestDeviceware(AppTesting):

    def setUp(self):
        pass


    def test_init(self):
        dv = deviceware.Device({})


if __name__ == '__main__':
    unittest.main()

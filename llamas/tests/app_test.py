#!/usr/bin/python3
import flask
import os
import unittest
from pdb import set_trace

import llamas
TESTS_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
MOCK_PATH = os.path.join(TESTS_DIR_PATH, 'mock')

class AppTesting(unittest.TestCase):

    CONFIG_PATH = os.path.join(MOCK_PATH, 'server_test.cfg')
    ALPAKA_CFG_PATH = os.path.join(MOCK_PATH, 'alpaka_test.cfg')


#!/usr/bin/python3
import flask
import os
import unittest
from pdb import set_trace

import llamas
MODULE_PATH = os.path.dirname(kolobok.__file__)

class AppTesting(unittest.TestCase):

    CONFIG_PATH = os.path.join(MODULE_PATH, 'config')

#!/usr/bin/python3
import flask
import os
import unittest
from pdb import set_trace

from app_test import AppTesting
from llamas import llamas_api
# MODULE_PATH = os.path.dirname(kolobok_api.__file__)

class TestInfoBp(AppTesting):

    def setUp(self):
        pass
        # self.app = flask.Flask(__name__)


    def test_get_id(self):
        # result = blueprint.get_id()
        app = llamas_api.KolobokServer(self.CONFIG_PATH)
        url = '/api/v1/%s' % ('info/id/')
        with app.test_client() as cli:
            result = cli.get(url)
            print(result.json)


if __name__ == '__main__':
    unittest.main()

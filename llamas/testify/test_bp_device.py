#!/usr/bin/python3
import flask
import os
import unittest
from pdb import set_trace

from app_test import AppTesting
from llamas import llamas_api


class TestDeviceBp(AppTesting):

    def test_get_id(self):
        app = llamas_api.LlamasServer(self.CONFIG_PATH)
        url = '/api/v1/%s' % ('device/add')
        result = None
        with app.test_client() as cli:
            result = cli.post(url)

        self.assertTrue(result.status_code < 300, 'Status code %s' % result.status_code)
        print(result.json)


if __name__ == '__main__':
    unittest.main()

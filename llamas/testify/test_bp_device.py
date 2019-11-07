#!/usr/bin/python3
import os
import random
import unittest
from pdb import set_trace
import flask

from llamas import llamas_api
from app_test import AppTesting


class TestDeviceBp(AppTesting):

    def test_add_cmp(self):
        app = llamas_api.LlamasServer(self.CONFIG_PATH)
        url = '/api/v1/%s' % ('device/add')
        body = {
            'gcid': random.randrange(1000, 7000),
            'cclass': random.randrange(1, 100),
            'uuid': '12345678123456781234567812345678'
        }
        result = None
        with app.test_client() as cli:
            result = cli.post(url, data=body)

        self.assertTrue(result.status_code < 300,
                        'Status code %s' % result.status_code)
        print('\n----- TestDeviceBp: test_add_cmp ----')
        print(result.json)


if __name__ == '__main__':
    unittest.main()

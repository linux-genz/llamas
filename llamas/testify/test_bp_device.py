#!/usr/bin/python3
import os
import random
import unittest
from pdb import set_trace
import flask
import json

from llamas import llamas_api
from app_test import AppTesting


class TestDeviceBp(AppTesting):

    def test_add_cmp(self):
        app = llamas_api.LlamasServer(self.CONFIG_PATH)
        url = '/api/v1/%s' % ('device/add')

        memory = {
            'start': 0xdeadbeefdeadbeef,
            'length': 2048,
            'type': 0x0, #FIXME: hardcoded because reasons.Fabric Manager will figure it out
            "cclass": 11, # block storage (non-boot)
        }#memory

        body = {
            'gcid': random.randrange(1000, 7000),
            'cclass': 11, # block storage (non-boot)
            'fabric': 5,
            'mgr_uuid': '00000000-1111-2222-3333-444455556666',
            'fru_uuid': '0',
            'uuid': -1,

            'resources': {
                'uuid': '12345678123456781234567812345678',
                'class': 0x2, #FIXME: hardcoded because reasons.Fabric Manager will figure it out
                'memory': [memory]
            },
        }#body

        result = None
        with app.test_client() as cli:
            result = cli.post(url, data=json.dumps(body))

        self.assertTrue(result.status_code < 300,
                        'Status code %s' % result.status_code)
        print('\n----- TestDeviceBp: test_add_cmp ----')
        print(result.json)


if __name__ == '__main__':
    unittest.main()

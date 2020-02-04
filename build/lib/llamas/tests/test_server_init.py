#!/usr/bin/python3
import os
import random
import unittest
from pdb import set_trace
import flask
import json

from llamas import llamas_api
from app_test import AppTesting


class TestServerInit(AppTesting):

    APP_NAME = 'llamas_test_init'

    def test_init(self):
        app = None
        try:
            app = llamas_api.LlamasServer(self.APP_NAME,
                                        cfg=self.CONFIG_PATH,
                                        alpaka_cfg=self.ALPAKA_CFG_PATH)
            self.assertTrue(True)
        except Exception as err:
            self.assertTrue(False, str(err))
            return

        self.assertTrue(isinstance(app.config, dict))
        self.assertTrue(app.config['TESTING'] == True)


if __name__ == '__main__':
    unittest.main()

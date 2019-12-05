#!/usr/bin/python3
import os
import random
import unittest
from pdb import set_trace
import flask

from llamas import llamas_api
from app_test import AppTesting
from llamas.middleware import json_to_struct as jts


class TestDeviceBp(AppTesting):

    def test_read_json(self):
        json_path = '../message_model/add.json'
        data = jts.generate_model(json_path)
        set_trace()
        print('???')


if __name__ == '__main__':
    unittest.main()

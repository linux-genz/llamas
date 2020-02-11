#!/usr/bin/python3

import unittest
from pdb import set_trace
from llamas.utils import utils


class TestSysUtils(unittest.TestCase):

    def test_is_valid_url(self):
        targets = [
            ['http://somevalid.com', True],
            ['http://somevalid.com:1234', True],
            ['http://somevalid.com:1234/something', True],
            ['https://somevalid.com:1234/something', True],
            ['ftp://somevalid.com:1234/something', True],
            ['some_invalid', False],
            ['aa://some_invalid', False],
            ['http://some_invalid:-asdf', False],
        ]
        failed = []

        for url in targets:
            is_valid = utils.is_valid_url(url[0])
            is_assert = is_valid == url[1]
            if not is_assert:
                failed.append(url[0])

        self.assertTrue(len(failed) == 0, 'Failed asserts: %s' % failed)


    def test_is_port_url(self):
        targets = [
            ['http://somevalid.com:10', True],
            ['http://somevalid.com:1020', True],
            ['http://somevalid.com:102030', True],
            ['http://invalid.com', False],
        ]
        failed = []

        for url in targets:
            is_valid = utils.is_port_in_url(url[0])
            is_assert = is_valid == url[1]
            if not is_assert:
                failed.append(url[0])

        self.assertTrue(len(failed) == 0, 'Failed asserts: %s' % failed)

if __name__ == '__main__':
    unittest.main()
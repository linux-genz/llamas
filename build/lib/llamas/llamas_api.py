#!/usr/bin/python3
import argparse
import os
import json
import logging

#https://github.com/FabricAttachedMemory/flask-api-template.git
import flask_fat
from flask_fat.config_builder import ConfigBuilder

from llamas import middleware
logging.basicConfig(level=logging.DEBUG)

class LlamasServer(flask_fat.APIBaseline):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alpaka_cfg_builder = ConfigBuilder(self.name, 'alpaka.conf')
        cfg_path = kwargs.get('alpaka_cfg', None)
        if cfg_path is None:
            cfg_path = self.alpaka_cfg_builder.priority_cfg_path

        # try:
        self.netlink = middleware.NetlinkManager(config=cfg_path)
        # except Exception as err:
        #     msg = 'Failed creating NetlinkManager! ->\n%s' % err
        #     logging.error(msg)
        #     raise RuntimeError(msg)

def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ignore',
                        help='blueprints to be ignored/not-loaded by server. ' +\
                            '--ignore "bp1,bp2,bp2"', default=None)
    parser.add_argument('-v', '--verbosity', action='count', default=0,
                        help='increase output verbosity')
    parser.add_argument('-c', '--cfg', default=None,
                            help='Path to a llamas RestAPI server config.')
    parser.add_argument('-a', '--alpaka-cfg', default=None,
                            help='Path to an alpaka config.')

    parsed = parser.parse_args()
    if parsed.ignore is not None:
        parsed.ignore = parsed.ignore.replace(' ', '').split(',')
    return vars(parsed)


def main(args=None):
    args = {} if args is None else args
    cmd = parse_cmd()
    args.update(cmd)

    mainapp = LlamasServer('llamas', **args)
    if args.get('verbose', False):
        for endpoint in mainapp.app.url_map.iter_rules():
            logging.info(endpoint.rule)

    if not args.get('dont_run', False):
        mainapp.run()
    return mainapp


if __name__ == '__main__':
    main()

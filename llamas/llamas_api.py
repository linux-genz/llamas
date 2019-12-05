#!/usr/bin/python3
import argparse
import os
import json
import logging

#https://github.com/FabricAttachedMemory/flask-api-template.git
import flask_fat
from llamas import middleware
logging.basicConfig(level=logging.DEBUG)

class LlamasServer(flask_fat.APIBaseline):

    def __init__(self, cfg, **kwargs):
        super().__init__(cfg, **kwargs)
        this_file = os.path.abspath(__file__)
        this_dir = os.path.dirname(this_file)
        cfg_path = os.path.join(this_dir, 'alpaka.cfg')
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

    parser.add_argument('--verbose', help='You know it.', action='store_true')
    parsed = parser.parse_args()
    if parsed.ignore is not None:
        parsed.ignore = parsed.ignore.replace(' ', '').split(',')
    return vars(parsed)


def main(args=None):
    args = {} if args is None else args
    cmd = parse_cmd()
    args.update(cmd)

    mainapp = LlamasServer('./llamas.cfg', **args)
    if not args.get('dont_run', False):
        mainapp.run()
    return mainapp


if __name__ == '__main__':
    main()

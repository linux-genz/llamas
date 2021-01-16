#!/usr/bin/python3
import argparse
import os
import json
import logging
from pathlib import Path
from uuid import UUID
from pdb import set_trace

#https://github.com/FabricAttachedMemory/flask-api-template.git
import flask_fat
from flask_fat import ConfigBuilder

from llamas import middleware
logging.basicConfig(level=logging.DEBUG)

class LlamasServer(flask_fat.APIBaseline):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alpaka_cfg_builder = ConfigBuilder('alpaka',
                                            self.__file__,
                                            path=kwargs.get('alpaka_cfg', None))
        cfg_path = self.alpaka_cfg_builder.priority_path

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
    parser.add_argument('--logging-cfg', default=None,
                        help='Path to a python3.logging config.')
    parser.add_argument('--alpaka-cfg', default=None,
                        help='Path to an alpaka config.')
    parser.add_argument('--alias', default=None,
                        help='This server alias name to use for the event subscription.')
    parser.add_argument('--event-add', default=None,
                        help='Add Event subscription endpoint. This will ' +\
                            'override the config ENDPOINTS value.')

    parsed = parser.parse_args()
    if parsed.ignore is not None:
        parsed.ignore = parsed.ignore.replace(' ', '').split(',')
    return vars(parsed)

def get_gcid(comp_path):
    gcid = comp_path / 'gcid'
    with gcid.open(mode='r') as f:
        return GCID(str=f.read().rstrip())

def get_cuuid(comp_path):
    cuuid = comp_path / 'c_uuid'
    with cuuid.open(mode='r') as f:
        return UUID(f.read().rstrip())

def get_cclass(comp_path):
    cclass = comp_path / 'cclass'
    with cclass.open(mode='r') as f:
        return int(f.read().rstrip())

def get_serial(comp_path):
    serial = comp_path / 'serial'
    with serial.open(mode='r') as f:
        return f.read().rstrip()

def find_local_bridges():
    sys_devices = Path('/sys/devices')
    dev_fabrics = sys_devices.glob('genz*')
    local_bridges = []
    for fab in dev_fabrics:
        bridges = fab.glob('bridge*')
        for br in bridges:
            cuuid = get_cuuid(br)
            serial = get_serial(br)
            local_bridges.append(str(cuuid) + ':' + serial)
    return local_bridges

def main(args=None):
    args = {} if args is None else args
    cmd = parse_cmd()
    args.update(cmd)

    local_bridges = find_local_bridges()
    args['bridges'] = local_bridges

    mainapp = LlamasServer('llamas', **args)
    if args.get('verbose', False):
        for endpoint in mainapp.app.url_map.iter_rules():
            logging.info(endpoint.rule)

    if not args.get('dont_run', False):
        mainapp.run()
    return mainapp


if __name__ == '__main__':
    main()

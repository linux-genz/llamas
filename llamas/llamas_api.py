#!/usr/bin/python3
import argparse
import os
import json
import logging
import re
import socket
import sys
from pathlib import Path
from uuid import UUID
from genz.genz_common import GCID
from setproctitle import getproctitle, setproctitle
from pdb import set_trace

#https://github.com/FabricAttachedMemory/flask-api-template.git
import flask_fat
from flask_fat import ConfigBuilder

from llamas import middleware
logging.basicConfig(level=logging.DEBUG)

MGR_UUID_0 = UUID('00000000-0000-0000-0000-000000000000')
TEMP_SUBNET = 0xffff  # where we put uninitialized local bridges

comp_num_re = re.compile(r'.*/([^0-9]+)([0-9]+)')

def component_num(comp_path):
    match = comp_num_re.match(str(comp_path))
    return int(match.group(2))

def fabric_num(comp_path):
    match = comp_num_re.match(str(comp_path.parent))
    return int(match.group(2))

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
        self.init_socket()

    def init_socket(self):
        # choose a random available port by setting config PORT to 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.config['HOST'], self.config['PORT']))
        self.sock.listen()
        # tell the underlying WERKZEUG server to use the socket we just created
        os.environ['WERKZEUG_SERVER_FD'] = str(self.sock.fileno())
        _, self.port = self.sock.getsockname()
        self.hostname = socket.gethostname()
        self.ip = socket.gethostbyname(self.hostname)


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

def get_mgr_uuid(comp_path):
    mgr_uuid = comp_path / 'mgr_uuid'
    with mgr_uuid.open(mode='r') as f:
        return UUID(f.read().rstrip())

def get_cclass(comp_path):
    cclass = comp_path / 'cclass'
    with cclass.open(mode='r') as f:
        return int(f.read().rstrip())

def get_serial(comp_path):
    serial = comp_path / 'serial'
    with serial.open(mode='r') as f:
        return f.read().rstrip()


class Bridge():
    def __init__(self, path: Path):
        self.path = path
        self.cuuid = get_cuuid(path)
        self.serial = get_serial(path)
        self.fab = fabric_num(path)
        self.tmp_gcid = GCID(sid=TEMP_SUBNET, cid=component_num(path))
        self.hostname = socket.gethostname()

    def update(self, path: Path):
        '''Update this bridge's path and fix up its fab number
        '''
        self.path = path
        self.fab = fabric_num(path)

    @property
    def cuuid_serial(self):
        return str(self.cuuid) + ':' + self.serial

    @property
    def gcid(self):
        return get_gcid(self.path)

    @property
    def mgr_uuid(self):
        return get_mgr_uuid(self.path)

    @property
    def bridge_name(self):
        return f'{self.hostname}:{self.path.name}'

    def __eq__(self, other):
        if type(self) != type(other):
            return NotImplemented
        return self.cuuid_serial == other.cuuid_serial

    def __hash__(self):
        return hash(self.cuuid_serial)


class Bridges():
    def __init__(self):
        self.by_cuuid_serial = {}  # key: cuuid_serial, value: Bridge
        self.by_mgr_uuid = {}      # key: mgr_uuid, value: set(Bridge)
        self.by_mgr_uuid[MGR_UUID_0] = set()

    def add(self, br: Bridge) -> None:
        self.by_cuuid_serial[br.cuuid_serial] = br
        mgr_uuid = br.mgr_uuid # read HW MGR-UUID (once)
        if mgr_uuid not in self.by_mgr_uuid:
            self.by_mgr_uuid[mgr_uuid] = set()
        self.by_mgr_uuid[mgr_uuid].add(br)

    def update(self, br: Bridge) -> None:
        mgr_uuid = br.mgr_uuid # read updated HW MGR-UUID (once)
        if mgr_uuid not in self.by_mgr_uuid:
            self.by_mgr_uuid[mgr_uuid] = set()
        if mgr_uuid != MGR_UUID_0:
            self.by_mgr_uuid[mgr_uuid].add(br)
            self.by_mgr_uuid[MGR_UUID_0].discard(br)
        else:
            brs = [b for b in self.by_mgr_uuid if br in self.by_mgr_uuid[b]]
            for b in brs:
                self.by_mgr_uuid[b].discard(br)
            self.by_mgr_uuid[MGR_UUID_0].add(br)

    def update_bridges(self):
        """
        Update the paths of the bridges and add any missing ones
        """
        new_bridges = find_local_bridges()
        for br in new_bridges:
            if br in self:
                prev = self.find(br.cuuid_serial)
                prev.update(br.path)
            else:
                self.add(br)
        # end for

    def find(self, cuuid_serial: str):
        try:
            return self.by_cuuid_serial[cuuid_serial]
        except KeyError:
            return None

    def match(self, mgr_uuid: UUID):
        try:
            for br in self.by_mgr_uuid[mgr_uuid]:
                yield br
        except KeyError:
            return

    def uninitialized(self):
        return self.match(MGR_UUID_0)

    def __iter__(self):
        for br in self.by_cuuid_serial.values():
            yield br


def find_local_bridges():
    sys_devices = Path('/sys/devices')
    dev_fabrics = sys_devices.glob('genz*')
    local_bridges = Bridges()
    for fab in dev_fabrics:
        bridges = fab.glob('bridge*')
        for br in bridges:
            local_bridges.add(Bridge(br))
    return local_bridges

def main(args=None):
    script_name = Path(__file__).name
    proc_title = script_name + ' ' + ' '.join(sys.argv[1:])
    setproctitle(proc_title)
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

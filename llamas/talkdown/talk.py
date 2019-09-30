#!/usr/bin/python3
import ctypes
import socket
import uuid
import os
from pprint import pprint

from pyroute2.common import map_namespace

import alpaka
from pdb import set_trace


class Talker(alpaka.ZooKeeper):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def build_msg(self, **kwargs):
        """ Overriding ZooKeeper's function. """
        cmd = kwargs['cmd']
        GCID = kwargs['gcid']
        CCLASS = kwargs['cclass']
        UUID = kwargs['uuid']

        if not isinstance(UUID, uuid.UUID):
            raise RuntimeError('UUID must be type uuid.UUID')

        msg = self.msg_model()
        msg['cmd'] = self.cfg.cmd_opts[cmd]
        msg['pid'] = os.getpid()
        msg['version'] = self.cfg.version

        # The policy map in the kernel code says always send three.
        msg['attrs'].append([ 'GENZ_A_GCID', GCID ])
        msg['attrs'].append([ 'GENZ_A_CCLASS', CCLASS ])
        msg['attrs'].append([ 'GENZ_A_UUID', UUID.bytes ])

        return msg


def YodelAyHeHUUID(random=True):
    """Return a uuid.UUID object."""
    if random:
        return uuid.uuid4()

    # Pick your favorite constructor, and refactor this routine accordingly.

    this = uuid.UUID('12345678123456781234567812345678')
    this = uuid.UUID(int=0x12345678123456781234567812345678)
    this = uuid.UUID('urn:uuid:12345678-1234-5678-1234-567812345678')
    this = uuid.UUID(bytes=b'\x12\x34\x56\x78' * 4)
    this = uuid.UUID(bytes_le=b'\x78\x56\x34\x12\x34\x12\x78\x56' +
                            b'\x12\x34\x56\x78\x12\x34\x56\x78')
    this = uuid.UUID(
        fields=(0x12345678, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678))
    this = uuid.UUID('{12345678-1234-5678-1234-567812345678}')
    this = uuid.UUID('12345678-1234-5678-1234-567812345678')
    return this


if __name__ == "__main__":
    genznl = Talker(config='/home/bender/dev/llamas/llamas/config')
    UUID = YodelAyHeHUUID()
    msg = genznl.build_msg(cmd=genznl.cfg.get('ADD'), gcid=4242, cclass=43, uuid=UUID)
    print('Sending PID=%d UUID=%s' % (msg['pid'], str(UUID)))
    try:
        # If it works, get a packet.  If not, raise an error.
        retval = genznl.sendmsg(msg)
        resperr = retval[0]['header']['error']
        if resperr:
            pprint(retval)
            raise RuntimeError(resperr)
        print('Success')
    except Exception as exc:
        raise SystemExit(str(exc))

    raise SystemExit(0)
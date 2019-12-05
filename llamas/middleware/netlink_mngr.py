#!/usr/bin/python3
import ctypes
import socket
import uuid
import logging
import os

from pprint import pprint
from pdb import set_trace

import alpaka
from llamas.message_model.add_component import ModelAddComponent


class NetlinkManager(alpaka.Messenger):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def build_msg(self, cmd, **kwargs):
        """
            @param cmd->data: {
                'gcid': init.uuid.gcid,
                'cclass': 11, # block storage (non-boot)
                'fabric': 5,
                'mgr_uuid': '9af8190f-1b4c-4be8-8732-e8d48e883396',
                'fru_uuid': 0,

                'resources': {
                    'uuid': str(init.uuid),
                    'class': 0x2, #FIXME: hardcoded because reasons.Fabric Manager will figure it out
                    'memory': memory
                },
            }
        """
        """ Overriding alpaka's function.
        output: {
            'cmd': 1,
            'version': 1,
            'reserved': 0,
            'attrs': [
                    ['GENZ_A_GCID', 4242],
                    ['GENZ_A_CCLASS', 43],
                    ['GENZ_A_UUID', b'\t\xc6{/L\xc9N\xec\x93X&\xce\xae\x8e\xbe\xda']
                ],
                'value': <class 'pyroute2.netlink.NotInitialized'>,
            'header': {},
            'pid': 20365
        }
        """
        data = kwargs.get('data', None)
        attrs = []
        err_msg = 'build_msg required "%s" parameter is None or missing!'
        if cmd is None:
            logging.error(err_msg % 'cmd')
            return None
        if data is None:
            logging.error(err_msg % 'data')
            return None

        cmd_index = self.cfg.cmd_opts.get(cmd)

        contract = self.cfg.get('CONTRACT', {}).get(cmd_index)
        if contract is None:
            contract = data

        kwargs['model'] = ModelAddComponent
        super().build_msg(cmd, **kwargs)
        msg = self.msg_model()

        #Convert a data structure into the parameters that kernel understands
        # for key, value in data.items():
        #     nl_key_name = contract[key] #key must be there at this point
        #     if isinstance(value, str):
        #         if value.isdigit():
        #             #parse digit str into float or int. Assume '.' in str is a float.
        #             if '.' in value: value = float(value)
        #             else: value = int(value)

        #     #This is a Hack to extract UUID! Wait for a precedent to break this.
        #     if 'uuid' in nl_key_name.lower():
        #         value = uuid.UUID(str(value)).bytes

        #     attrs.append([ nl_key_name, value ])

        attrs.append(['GENZ_A_FABRIC_NUM', data['fabric']])
        attrs.append(['GENZ_A_CCLASS', data['cclass']])
        attrs.append(['GENZ_A_GCID', data['gcid']])
        attrs.append(['GENZ_A_FRU_UUID', data['fru_uuid']])
        attrs.append(['GENZ_A_MGR_UUID', data['mgr_uuid']])

        #FIXME: the message building below needs to be refactored somehow for
        #better usability and reusability
        mrl_attrs = []
        for memory in data['resources']['memory']:
            pprint(memory)
            GENZ_A_MRL = ['GENZ_A_MRL', {
                    'attrs' :
                    [
                        ['GENZ_A_MR_CLASS', memory['cclass']],
                        ['GENZ_A_MR_START', memory['start']],
                        ['GENZ_A_MR_LENGTH', memory['length']],
                        ['GENZ_A_MR_TYPE', memory['type']],
                    ]
                },
            ]#GENZ_A_MRL
            mrl_attrs.append(GENZ_A_MRL)

        mrl_list = [
            'GENZ_A_U_MRL', {
                'attrs' : mrl_attrs
            }#resource list
        ]

        attrs.append([
            'GENZ_A_RESOURCE_LIST', {
                'attrs' : [
                    [
                        'GENZ_A_UL', {
                            'attrs' : [
                                ['GENZ_A_U_UUID', data['resources']['uuid']],
                                ['GENZ_A_U_CLASS', data['resources']['class']],
                                mrl_list,
                            ]
                        },
                    ],
                ],#attrs
            }#resource list
        ])

        msg['attrs'] = attrs
        msg['cmd'] = cmd_index
        msg['pid'] = os.getpid()
        msg['version'] = self.cfg.version
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
    genznl = NetlinkManager()
    # genznl = Talker(config='../config')
    UUID = YodelAyHeHUUID()
    msg = genznl.build_msg(genznl.cfg.get('ADD'), gcid=4242, cclass=43, uuid=UUID)
    print('Sending PID=%d UUID=%s' % (msg['pid'], str(UUID)))
    try:
        # If it works, get a packet.  If not, raise an error.
        retval = genznl.sendmsg(msg)
        resperr = retval[0]['header']['error']
        if resperr:
            print('--------!!netlink_mngr: __main__!!!-------')
            pprint(retval)
            raise RuntimeError(resperr)
        print('Success')
    except Exception as exc:
        raise SystemExit(str(exc))

    raise SystemExit(0)
#!/usr/bin/python3
import ctypes
import socket
import uuid
import logging
import os

from pdb import set_trace

import alpaka
from llamas.message_model.add_component import ModelAddComponent


class NetlinkManager(alpaka.Messenger):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def build_mrl_list(self, resource):
        mrl_attrs = []
        for memory in resource['memory']:
            GENZ_A_MRL = ['GENZ_A_MRL', {
                'attrs':
                [
                    ['GENZ_A_MR_START', memory['start']],
                    ['GENZ_A_MR_LENGTH', memory['length']],
                    ['GENZ_A_MR_TYPE', memory['type']],
                    ['GENZ_A_MR_RO_RKEY', memory['ro_rkey']],
                    ['GENZ_A_MR_RW_RKEY', memory['rw_rkey']],
                ]
            },
            ]#GENZ_A_MRL
            mrl_attrs.append(GENZ_A_MRL)

        mrl_list = [
            'GENZ_A_U_MRL', {
                'attrs' : mrl_attrs
            }
        ]
        return mrl_list

    def build_resource_list(self, data):
        res_attrs = []
        for res in data['resources']:
            GENZ_A_UL = ['GENZ_A_UL', {
                'attrs':
                [
                    ['GENZ_A_U_CLASS_UUID', uuid_str_to_bytearray(res['class_uuid'])],
                    ['GENZ_A_U_INSTANCE_UUID', uuid_str_to_bytearray(res['instance_uuid'])],
                    ['GENZ_A_U_FLAGS', res['flags']],
                    ['GENZ_A_U_CLASS', res['class']],
                    self.build_mrl_list(res),
                ]
            },
            ]#GENZ_A_UL
            res_attrs.append(GENZ_A_UL)

        res_list = [
            'GENZ_A_RESOURCE_LIST', {
                'attrs' : res_attrs
            }
        ]
        return res_list

    def build_msg(self, cmd, **kwargs):
        """
            @param kwargs->data: {
                'br_gcid': bridge.gcid,
                'gcid': init.uuid.gcid,
                'serial': 12345678,
                'cclass': 2, # Memory (Explicit OpClass)
                'cuuid':    'e3331770-6648-4def-8100-404d844298d3',
                'mgr_uuid': '9af8190f-1b4c-4be8-8732-e8d48e883396',
                'fru_uuid': '00000000-0000-0000-0000-000000000000',

                'resources': [
                    {
                      'class_uuid': str(init.uuid), # driver matched against this
                      'instance_uuid': str(init.uuid),
                      'flags': 0,
                      'class': 11, # block storage (non-boot)
                      'memory': [
                          {
                            'start': 'number',
                            'length': 'number',
                            'type': 'number',  # 0 = GENZ_CONTROL, 1 = GENZ_DATA
                            'ro_rkey': 'number',
                            'rw_rkey': 'number',
                          }
                      ]
                    },
                ]
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

        # Convert the passed json data into the netlink parameters that kernel understands

        attrs.append(['GENZ_A_CCLASS', data['cclass']])
        attrs.append(['GENZ_A_GCID', data['gcid']])
        attrs.append(['GENZ_A_BRIDGE_GCID', data['br_gcid']])
        attrs.append(['GENZ_A_SERIAL', data['serial']])
        attrs.append(['GENZ_A_CUUID', uuid_str_to_bytearray(data['cuuid'])])
        attrs.append(['GENZ_A_FRU_UUID', uuid_str_to_bytearray(data['fru_uuid'])])
        attrs.append(['GENZ_A_MGR_UUID', uuid_str_to_bytearray(data['mgr_uuid'])])
        attrs.append(self.build_resource_list(data))

        msg['attrs'] = attrs
        msg['cmd'] = cmd_index
        msg['pid'] = os.getpid()
        msg['version'] = self.cfg.version
        return msg


def uuid_str_to_bytearray(uuid_str):
    """
        Convert a UUID string format (e.g. 00000000-0000-0000-0000-000000000000)
    into bytes that netlink pyroute2 library can understand and send properly.
    """
    uuid_obj = uuid.UUID(uuid_str)
    bytes = uuid_obj.bytes
    return bytes


# def YodelAyHeHUUID(random=True):
#     """Return a uuid.UUID object."""
#     if random:
#         return uuid.uuid4()

#     # Pick your favorite constructor, and refactor this routine accordingly.

#     this = uuid.UUID('12345678123456781234567812345678')
#     this = uuid.UUID(int=0x12345678123456781234567812345678)
#     this = uuid.UUID('urn:uuid:12345678-1234-5678-1234-567812345678')
#     this = uuid.UUID(bytes=b'\x12\x34\x56\x78' * 4)
#     this = uuid.UUID(bytes_le=b'\x78\x56\x34\x12\x34\x12\x78\x56' +
#                             b'\x12\x34\x56\x78\x12\x34\x56\x78')
#     this = uuid.UUID(
#         fields=(0x12345678, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678))
#     this = uuid.UUID('{12345678-1234-5678-1234-567812345678}')
#     this = uuid.UUID('12345678-1234-5678-1234-567812345678')
#     return this


# if __name__ == "__main__":
#     genznl = NetlinkManager()
#     # genznl = Talker(config='../config')
#     UUID = YodelAyHeHUUID()
#     msg = genznl.build_msg(genznl.cfg.get('ADD'), gcid=4242, cclass=43, uuid=UUID)
#     print('Sending PID=%d UUID=%s' % (msg['pid'], str(UUID)))
#     try:
#         # If it works, get a packet.  If not, raise an error.
#         retval = genznl.sendmsg(msg)
#         resperr = retval[0]['header']['error']
#         if resperr:
#             print('--------!!netlink_mngr: __main__!!!-------')
#             pprint(retval)
#             raise RuntimeError(resperr)
#         print('Success')
#     except Exception as exc:
#         raise SystemExit(str(exc))

#     raise SystemExit(0)

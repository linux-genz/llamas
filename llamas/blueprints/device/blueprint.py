#!/usr/bin/python3
import flask
import os
import json
import jsonschema
import requests as HTTP_REQUESTS
import logging
import uuid
from pdb import set_trace

import flask_fat
# from llamas.utils import sys_utils
# from llamas.controls import deviceware
Journal = self = flask_fat.Journal(__file__, url_prefix='/api/v1')


def subscribe_to_redfish():
    print('Subscribing')
    url = 'http://localhost:5000/redfish/v1/EventService'
    data = {
        '@odata.context': '/redfish/v1/$metadata#EventDestination.EventDestination',
        '@odata.id': '/redfish/v1/EventService',
        '@odata.type': '#EventService.v1_0_0.EventService',

        'Id': '1',
        'Name': 'EventSubscription1',
        'Description': 'asdfasdfasdf',

        'RegistryPrefixes' : 'ResourceAdded',
        'RegistryVersion' : '1.0.0',

        'EventTypes' : [ 'ResourceAdded' ],
        'Destination' : 'http://localhost:1991/%s/add' % Journal.name,

        'Context': 'Device add event',
        'Protocol': 'Redfish'
    }
    try:
        resp = HTTP_REQUESTS.post(url, data)
    except Exception:
        print('---- !!ERROR!! Failed to subscribe to redfish event! ---- ')
        pass

# subscribe_to_redfish()


''' ------------------------------- ROUTES ------------------------------- '''


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


@Journal.BP.route('/%s/add' % (Journal.name), methods=['POST'])
def add_cmp():
    '''
        Return nodes ID this API is running on.
    '''
    logging.info('%s/add route is called.' % Journal.name)

    response = {}
    status = 'nothing happened'
    code = 300

    UUID = YodelAyHeHUUID()
    zoo = Journal.mainapp.zookeeper
    msg = zoo.build_msg(cmd=zoo.cfg.get('ADD'), gcid=4242, cclass=43, uuid=UUID)

    logging.info('Sending PID=%d UUID=%s' % (msg['pid'], str(UUID)))

    try:
        # If it works, get a packet.  If not, raise an error.
        retval = zoo.sendmsg(msg)
        resperr = retval[0]['header']['error']
        if resperr:
            logging.error(retval)
            response['error'] = resperr
            code = 400
        else:
            status = 'success'
            code = 200
    except Exception as exc:
        response['error'] = str(exc)
        code = 401

    response['status'] = status

    return flask.make_response(flask.jsonify(response), code)
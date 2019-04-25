#!/usr/bin/python3
import flask
import os
import json
import jsonschema
import requests as HTTP_REQUESTS
from pdb import set_trace

import flask_fat
from llamas.utils import sys_utils
from llamas.controls import deviceware
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

subscribe_to_redfish()
''' ------------------------------- ROUTES ------------------------------- '''

@Journal.BP.route('/%s/add' % (Journal.name), methods=['GET', 'PUSH', 'POST'])
def get_id():
    '''
        Return nodes ID this API is running on.
    '''
    return flask.make_response(flask.jsonify({
        'updated' : [] }), 300)
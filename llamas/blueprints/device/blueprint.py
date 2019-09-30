#!/usr/bin/python3
import flask
import os
import json
import jsonschema
import posixpath
import requests as HTTP_REQUESTS
import logging
import uuid
import socket
import time
import threading
from pdb import set_trace

import flask_fat

class DeviceJournal(flask_fat.Journal):


    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self._is_pinging = False


    def on_post_register(self):
        self.subscribe_to_redfish()


    def check_event_server(self, iteration_time):
        if not self._is_pinging:
            return
        #FIXME: this called twice per iteration. IDK why. Probably something obvious.
        t = threading.Timer(iteration_time, self.check_event_server, [iteration_time])
        print('Trying to subscribe to event... [%s]' % (time.ctime()))
        self.subscribe_to_redfish()
        t.start()


    def subscribe_to_redfish(self):
        cfg = self.mainapp.config
        port = cfg['PORT']
        url = posixpath.join(cfg['ENDPOINTS']['base'], cfg['ENDPOINTS']['event_add'])
        callback_endpoint = posixpath.join('http://',
                                '%s:%s' % (socket.gethostname(), port),
                                'api/v1',
                                self.name,
                                'add')
        # data = {
        #     '@odata.context': '/redfish/v1/$metadata#EventDestination.EventDestination',
        #     '@odata.id': '/redfish/v1/EventService',
        #     '@odata.type': '#EventService.v1_0_0.EventService',

        #     'Id': '1',
        #     'Name': 'EventSubscription1',
        #     'Description': 'asdfasdfasdf',

        #     'RegistryPrefixes' : 'ResourceAdded',
        #     'RegistryVersion' : '1.0.0',

        #     'EventTypes' : [ 'ResourceAdded' ],
        #     'Destination' : 'http://localhost:1991/%s/add' % Journal.name,

        #     'Context': 'Device add event',
        #     'Protocol': 'Redfish'
        # }
        data = {
            'callback' : callback_endpoint
        }
        try:
            HTTP_REQUESTS.post(url, data)
            self._is_pinging = False
            logging.info('--- Subscribed to callback at %s' % callback_endpoint)
        except Exception:
            logging.error('---- !!ERROR!! Failed to subscribe to redfish event! ---- ')
            if not self._is_pinging:
                self._is_pinging = True
                self.check_event_server(cfg.get('SUBSCRIBE_INTERVAL', 5))


Journal = self = DeviceJournal(__file__, url_prefix='/api/v1')


''' ------------------------------- ROUTES ------------------------------- '''


@Journal.BP.route('/%s/add' % (Journal.name), methods=['POST'])
def add_cmp():
    '''
        Return nodes ID this API is running on.
    '''
    logging.info('%s/add route is called.' % Journal.name)
    response = {}
    status = 'nothing happened'
    code = 300

    body = flask.request.form
    gcid = body.get('gcid', '-1')
    cclass = body.get('cclass', '-1')
    uuid_val = body.get('uuid', '-1')
    uuid_val = uuid.UUID('12345678123456781234567812345678')

    zoo = Journal.mainapp.zookeeper
    msg = zoo.build_msg(cmd=zoo.cfg.get('ADD'),
                        gcid=int(gcid),
                        cclass=int(cclass),
                        uuid=uuid_val)

    logging.info('Sending PID=%d UUID=%s' % (msg['pid'], str(uuid_val)))

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
#!/usr/bin/python3
import flask
import os
import json
# import jsonschema
import posixpath
import requests as HTTP_REQUESTS
import logging
# import uuid
import socket
import time
import threading
from pdb import set_trace

import flask_fat

class DeviceJournal(flask_fat.Journal):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self._is_pinging = True

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
        if not self._is_pinging: #already subscribed
            return

        cfg = self.mainapp.config
        port = cfg['PORT']
        url = cfg['ENDPOINTS']['event_add_cmp']
        this_hostname = self.mainapp.config.get('THIS_HOSTNAME', None)
        if this_hostname is None:
            this_hostname = socket.gethostname()

        callback_endpoint = posixpath.join('http://',
                                '%s:%s' % (this_hostname, port),
                                # '%s:%s' % ('localhost', port),
                                'api/v1',
                                self.name,
                                'add')

        data = {
            'callback' : callback_endpoint
        }

        try:
            resp = HTTP_REQUESTS.post(url, data)
        except Exception as err:
            resp = None
            logging.debug('subscribe_to_redfish(): %s' % err)

        is_success = resp is not None and resp.status_code < 300

        if is_success:
            self._is_pinging = False
            logging.info('--- Subscribed to %s to callback at %s' % \
                        (url, callback_endpoint))
        else:
            logging.error('---- !!ERROR!! Failed to subscribe to redfish event! ---- ')
            if resp is not None:
                #FIXME: log the actuall status message from the response
                logging.debug('subscription error reason [%s]: %s' %\
                                (resp.status_code, resp.reason))

            if not self._is_pinging:
                self._is_pinging = True
                self.check_event_server(cfg.get('SUBSCRIBE_INTERVAL', 5))


Journal = self = DeviceJournal(__file__, url_prefix='/api/v1')


""" ------------------------------- ROUTES ------------------------------- """


@Journal.BP.route('/%s/add' % (Journal.name), methods=['POST'])
def add_cmp():
    """
        Return nodes ID this API is running on.
    @param req.body: {
        'gcid' : <value>,
        'cclass' : <value>,
        'uuid' : <value>,
    }
    """
    logging.info('%s/add route is called.' % Journal.name)
    response = { 'msg' : { 'cmd' : -1, 'attr' : [] } }
    status = 'nothing happened'
    code = 300
    nl = Journal.mainapp.netlink
    body = flask.request.form
    if not body:
        #this happenes when using flask's test_client. It stors post data into
        #.data as a json string.
        body = json.loads(flask.request.data)

    cmd_name = nl.cfg.get('ADD')
    msg = nl.build_msg(cmd_name, data=body)

    logging.info('Sending PID=%d; cmd=%s' % (msg['pid'], cmd_name))
    #FIXME: move this try/except into a function out of here
    try:
        # If it works, get a packet.  If not, raise an error.
        retval = nl.sendmsg(msg)
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

    if code < 300:
        response['msg'] = {
            'cmd' : msg['cmd'],
            #convert pyroute2.netlink.nla_slot into tuple
            'attr' : [tuple(item) for item in msg['attrs']]
        }

    response['status'] = status
    return flask.make_response(flask.jsonify(str(response)), code)
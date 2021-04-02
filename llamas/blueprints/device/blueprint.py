#!/usr/bin/python3
import flask
import os
import json
import posixpath
import requests as HTTP_REQUESTS
import logging
import socket
import time
from threading import Timer
from pdb import set_trace

import flask_fat
from llamas.utils import utils


class RepeatedTimer():
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self, interval=None):
        if interval is not None:
            self.interval = interval
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        if self._timer is not None:
            self._timer.cancel()
        self.is_running = False


class DeviceJournal(flask_fat.Journal):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self._is_subscribed = False
        self._subscribe_timer = RepeatedTimer(None, self.subscribe_to_redfish)
        self._ready_timer = RepeatedTimer(0.5, self.check_server_ready)
        self._ready_timer.start()

    #def on_post_register(self):
    #    self.subscribe_to_redfish()

    def endpoint_url(self):
        cfg = self.mainapp.config
        port = cfg['PORT']
        url = cfg['ENDPOINTS']['event_add_cmp']
        mainapp_url = self.mainapp.kwargs.get('event_add', None)
        if mainapp_url is not None:
            url = mainapp_url

        this_hostname = self.mainapp.config.get('THIS_HOSTNAME', None)
        if this_hostname is None:
            this_hostname = 'http://localhost'

        if not utils.is_port_in_url(this_hostname):
            this_hostname = '%s:%s' % (this_hostname, port)
        if utils.is_valid_url(this_hostname) is False:
            raise RuntimeError('Invalid THIS_HOSTNAME url in config: %s ' % this_hostname)

        callback_endpoint = posixpath.join(this_hostname,
                                # '%s:%s' % ('localhost', port),
                                'api/v1',
                                self.name,
                                'add')

        return (url, callback_endpoint)

    def subscribe_to_redfish(self):
        if self._is_subscribed: # already subscribed
            return

        url, callback_endpoint = self.endpoint_url()
        bridges = self.mainapp.kwargs.get('bridges', [])

        data = {
            'callback' : callback_endpoint,
            'alias' : self.mainapp.kwargs.get('alias', ''),
            'bridges': bridges
        }

        try:
            resp = HTTP_REQUESTS.post(url, json=data)
        except Exception as err:
            resp = None
            logging.debug('subscribe_to_redfish(): %s' % err)

        is_success = resp is not None and resp.status_code < 300

        if is_success:
            self._is_subscribed = True
            self._subscribe_timer.stop()
            logging.info('--- Subscribed to %s to callback at %s' % \
                        (url, callback_endpoint))
        else:
            logging.error('---- !!ERROR!! Failed to subscribe to redfish event! {} {} ---- '.format(url, callback_endpoint))
            if resp is not None:
                #FIXME: log the actual status message from the response
                logging.error('subscription error reason [%s]: %s' %\
                                (resp.status_code, resp.reason))

            self._subscribe_timer.start(interval=cfg.get('SUBSCRIBE_INTERVAL', 5))

    def check_server_ready(self):
        _, endpoint = self.endpoint_url()
        try:
            resp = HTTP_REQUESTS.get(endpoint, timeout=0.1)
            logging.debug('GET {} returned {}'.format(endpoint, resp))
            self._ready_timer.stop()
            self.subscribe_to_redfish()
        except HTTP_REQUESTS.exceptions.ConnectionError:
            logging.debug('GET {} ConnectionError - restarting ready_timer'.format(endpoint))
            self._ready_timer.start()


Journal = self = DeviceJournal(__file__, url_prefix='/api/v1')


""" ------------------------------- ROUTES ------------------------------- """


@Journal.BP.route('/%s/add' % (Journal.name), methods=['GET', 'POST'])
def add_cmp():
    """
        Return nodes ID this API is running on.
    @param req.body: {
        'gcid' : <value>,
        'cclass' : <value>,
        'uuid' : <value>,
    }
    """
    logging.info('%s %s/add route is called.' % (flask.request.method, Journal.name))
    response = { 'msg' : { 'cmd' : -1, 'attr' : [] } }
    status = 'nothing happened'
    if flask.request.method == 'GET':
        code = 200
        status = 'success'
        response['status'] = status
        return flask.make_response(flask.jsonify(str(response)), code)
    code = 300
    nl = Journal.mainapp.netlink
    body = flask.request.form
    if not body:
        #this happens when using flask's test_client. It stores post data into
        #.data as a json string.
        body = json.loads(flask.request.data)

    cmd_name = nl.cfg.get('ADD')
    msg = nl.build_msg(cmd_name, data=body)
    pid = msg.get('pid', -1)

    logging.info('Sending netlink PID=%d; cmd=%s' % (pid, cmd_name))
    logging.debug('netlink msg={}'.format(msg))
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

#!/usr/bin/python3
import flask
import os
import json
import posixpath
import requests as HTTP_REQUESTS
from requests.exceptions import ConnectionError
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

    def endpoint_url(self, name):
        cfg = self.mainapp.config
        port = cfg['PORT']
        url = cfg['ENDPOINTS']['event_{}_cmp'.format(name)]
        mainapp_url = self.mainapp.kwargs.get('event_{}'.format(name), None)
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
                                name)

        return (url, callback_endpoint)

    def subscribe_to_redfish(self):
        if self._is_subscribed: # already subscribed
            return

        bridges = self.mainapp.kwargs.get('bridges', [])

        # Revisit: generalize this for an arbitrary number of endpoints
        add_url, add_callback_endpoint = self.endpoint_url('add')
        add_data = {
            'callback' : add_callback_endpoint,
            'alias' : self.mainapp.kwargs.get('alias', ''),
            'bridges': bridges
        }

        try:
            resp_add = HTTP_REQUESTS.post(add_url, json=add_data)
        except ConnectionError as err:
            resp_add = None
            retry = self.mainapp.config.get('SUBSCRIBE_INTERVAL', 5)
            logging.debug(f'retry subscribe_to_redfish() in {retry} seconds: {err}')
            self._subscribe_timer.start(interval=retry)
            return
        except Exception as err:
            resp_add = None
            logging.debug(f'subscribe_to_redfish(): {err}')

        is_success_add = resp_add is not None and resp_add.status_code < 300

        remove_url, remove_callback_endpoint = self.endpoint_url('remove')
        remove_data = {
            'callback' : remove_callback_endpoint,
            'alias' : self.mainapp.kwargs.get('alias', ''),
            'bridges': bridges
        }

        # Revisit: if resp_add failed, why do resp_rm?
        try:
            resp_rm = HTTP_REQUESTS.post(remove_url, json=remove_data)
        except Exception as err:
            resp_rm = None
            logging.debug(f'subscribe_to_redfish(): {err}')

        is_success_remove = resp_rm is not None and resp_rm.status_code < 300

        if is_success_add and is_success_remove:
            self._is_subscribed = True
            self._subscribe_timer.stop()
            logging.info(f'--- Subscribed to {add_url}, callback at {add_callback_endpoint}')
            logging.info(f'--- Subscribed to {remove_url}, callback at {remove_callback_endpoint}')
        else:
            if not is_success_add:
                logging.error('---- Failed to subscribe to redfish event! {} {} ---- '.format(add_url, add_callback_endpoint))
                if resp_add is not None:
                    #FIXME: log the actual status message from the response
                    logging.error('subscription error reason [%s]: %s' %\
                                  (resp_add.status_code, resp_add.reason))
            if not is_success_remove:
                logging.error('---- Failed to subscribe to redfish event! {} {} ---- '.format(remove_url, remove_callback_endpoint))
                if resp_rm is not None:
                    #FIXME: log the actual status message from the response
                    logging.error('subscription error reason [%s]: %s' %\
                                  (resp_rm.status_code, resp_rm.reason))

    def check_server_ready(self):
        _, endpoint = self.endpoint_url('add')
        try:
            resp = HTTP_REQUESTS.get(endpoint, timeout=0.1)
            logging.debug('GET {} returned {}'.format(endpoint, resp))
            self._ready_timer.stop()
            self.subscribe_to_redfish()
        except ConnectionError:
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
    logging.info(f'{flask.request.method} {Journal.name}/add is called.')
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


@Journal.BP.route('/%s/remove' % (Journal.name), methods=['GET', 'POST'])
def remove_cmp():
    """
        Return nodes ID this API is running on.
    @param req.body: {
        'gcid' : <value>,
        'cclass' : <value>,
        'uuid' : <value>,
    }
    """
    logging.info(f'{flask.request.method} {Journal.name}/remove is called.')
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

    cmd_name = nl.cfg.get('REMOVE')
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

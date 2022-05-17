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
from uuid import UUID
from genz.genz_common import DR_IFACE_NONE, INVALID_GCID
from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, Zeroconf

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


class FM():
    def __init__(self, info: ServiceInfo):
        self.is_subscribed = False
        self.info = info
        self.addresses = info.parsed_scoped_addresses()
        if info.properties:
            self.fab_uuid = UUID(bytes=info.properties[b'fab_uuid'])
            self.mgr_uuid = UUID(bytes=info.properties[b'mgr_uuid'])
            self.pfm = bool(int(info.properties[b'pfm']))
        self.bridges = []

    @property
    def port(self):
        return self.info.port

    @property
    def name(self):
        return self.info.name

    def __hash__(self): # Revisit: do we need this?
        return hash(self.name)


class DeviceJournal(flask_fat.Journal):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self._ready_timer = RepeatedTimer(0.5, self.check_server_ready)
        self._ready_timer.start()
        self.fms = {}

    def endpoints_url(self, fm: FM):
        cfg = self.mainapp.config
        port = self.mainapp.port
        eps = cfg['ENDPOINTS']
        mainapp_eps = self.mainapp.kwargs.get('endpoints', None)
        if mainapp_eps is not None:
            eps = mainapp_eps
        fm_subscribe = self.mainapp.config.get('FM_SUBSCRIBE', 'subscribe/llamas')
        # Revisit: multiple FM addresses
        url = (f'http://{fm.addresses[0]}:{fm.port}/{fm_subscribe}' if fm is not None
               else None)

        this_hostname = self.mainapp.config.get('THIS_HOSTNAME', None)
        if this_hostname is None:
            this_hostname = f'http://{self.mainapp.hostname}'

        if not utils.is_port_in_url(this_hostname):
            this_hostname = f'{this_hostname}:{port}'
        if utils.is_valid_url(this_hostname) is False:
            raise RuntimeError('Invalid THIS_HOSTNAME url in config: %s ' % this_hostname)

        endpoints = {}
        for k, v in eps.items():
            endpoints[k] = posixpath.join(this_hostname, v)

        return (url, endpoints)

    def subscribe_to_redfish(self, fm: FM) -> None:
        if fm.is_subscribed: # already subscribed
            return

        bridges = [br.cuuid_serial for br in fm.bridges]

        url, callback_endpoints = self.endpoints_url(fm)
        data = {
            'callbacks' : callback_endpoints,
            'alias'     : self.mainapp.kwargs.get('alias', ''),
            'bridges'   : bridges
        }

        try:
            resp = HTTP_REQUESTS.post(url, json=data)
        except Exception as err:
            resp = None
            logging.debug(f'subscribe_to_redfish(): {err}')

        is_success = resp is not None and resp.status_code < 300

        if is_success:
            fm.is_subscribed = True
            logging.info(f'--- Subscribed to {url}, callbacks at {callback_endpoints}')
        else:
            logging.error('---- Failed to subscribe to redfish event! {} {} ---- '.format(url, callback_endpoints))
            if resp is not None:
                #FIXME: log the actual status message from the response
                logging.error(f'subscription error reason [{resp.status_code}]: {resp.reason}')

    def check_server_ready(self):
        _, endpoints = self.endpoints_url(None)
        endpoint = endpoints['add'] # arbitrary local endpoint to GET
        try:
            resp = HTTP_REQUESTS.get(endpoint, timeout=0.1)
            logging.debug('check_server_ready: GET {} returned {}'.format(endpoint, resp))
            self._ready_timer.stop()
            self.zeroconf_setup()
        except ConnectionError:
            logging.debug('GET {} ConnectionError - restarting ready_timer'.format(endpoint))
            self._ready_timer.start()

    def zeroconf_setup(self):
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only) # Revisit
        services = ['_genz-fm._tcp.local.']
        self.browser = ServiceBrowser(self.zeroconf, services, self)

    def add_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        logging.debug(f'Service {name} of type {type} Added')
        info = zeroconf.get_service_info(type, name)
        logging.debug(f'Info from zeroconf.get_service_info: {info}')
        if name in self.fms:
            logging.error(f'duplicate FM name {name}')
            return
        fm = FM(info)
        self.fms[name] = fm
        if not fm.pfm:
            logging.info(f'ignoring non-PFM {name}')
            return
        local_bridges = self.mainapp.kwargs['bridges']
        local_bridges.update_bridges()
        # avoid "Set changed size during iteration"
        uninit = [br for br in local_bridges.uninitialized()]
        for br in uninit:
            local_bridges.update(br)
        for br in local_bridges.match(fm.mgr_uuid):
            fm.bridges.append(br)
        if len(fm.bridges) > 0:
            self.subscribe_to_redfish(fm)

    def remove_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        logging.debug(f'Service {name} of type {type} Removed')
        info = zeroconf.get_service_info(type, name)
        logging.debug(f'Info from zeroconf.get_service_info: {info}')
        try:
            fm = self.fms[name]
        except KeyError:
            logging.error(f'attempt to remove unknown FM {name}')
            return
        del self.fms[name]
        # Revisit: finish this

    def update_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        logging.debug(f'Service {name} of type {type} Updated')
        info = zeroconf.get_service_info(type, name)
        logging.debug(f'Info from zeroconf.get_service_info: {info}')
        unknown = False
        try:
            fm = self.fms[name]
        except KeyError:
            logging.warning(f'attempt to update unknown FM {name}')
            unknown = True
            fm = FM(info) # treat as if this was an 'add'
        # Revisit: finish this


Journal = self = DeviceJournal(__file__, url_prefix='/api/v1')


""" ------------------------------- ROUTES ------------------------------- """


@Journal.BP.route(f'/{Journal.name}/add', methods=['GET', 'POST'])
def add_cmp():
    """
        Add a component.
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
    logging.debug(f'cmd_name={cmd_name}')
    msg = nl.build_msg(cmd_name, data=body)
    logging.debug(f'after build_msg, msg={msg}')
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


@Journal.BP.route(f'/{Journal.name}/remove', methods=['GET', 'POST'])
def remove_cmp():
    """
        Remove a component.
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


@Journal.BP.route(f'/{Journal.name}/local_bridge', methods=['GET', 'POST'])
def local_bridge():
    """
        Move an FM-managed local bridge to its permanent fabric/GCID
    @param req.body: {
        'gcid'         : <value>,
        'cuuid_serial' : <value>,
        'mgr_uuid'     : <value>,
    }
    """
    logging.info(f'{flask.request.method} {Journal.name}/local_bridge is called.')
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

    # convert the zephyr cuuid:serial to tmp_gcid
    local_bridges = self.mainapp.kwargs['bridges']
    if local_bridges is None:
        code = 400
        status = 'no local bridges'
        logging.error(status)
        response['status'] = status
        return flask.make_response(flask.jsonify(str(response)), code)
    local_bridges.update_bridges()
    cuuid_serial = body['cuuid_serial']
    br = local_bridges.find(cuuid_serial)
    if br is None:
        code = 400
        status = f'local bridge {cuuid_serial} not found'
        logging.error(status)
        response['status'] = status
        return flask.make_response(flask.jsonify(str(response)), code)
    body['tmp_gcid'] = br.tmp_gcid.val
    logging.debug(f"moving local bridge {cuuid_serial} with tmp_gcid {br.tmp_gcid} to {body['gcid']}")
    # add other items netlink requires
    body['br_gcid'] = body['gcid'] # must match for netlink scenario 1
    body['dr_gcid'] = INVALID_GCID.val
    body['dr_iface'] = DR_IFACE_NONE
    cmd_name = nl.cfg.get('LOCAL_BRIDGE')
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
            #'attr' : [tuple(item) for item in msg['attrs']]
        }

    response['name'] = br.bridge_name
    response['status'] = status
    return flask.make_response(flask.jsonify(response), code)

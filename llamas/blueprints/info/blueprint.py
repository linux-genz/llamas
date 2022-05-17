#!/usr/bin/python3
import flask
import os
import json
import jsonschema
import requests as HTTP_REQUESTS
from pdb import set_trace

import flask_fat
from llamas.utils import sys_utils
Journal = self = flask_fat.Journal(__file__, url_prefix='/api/v1')

""" ------------------------------- ROUTES ------------------------------- """

@Journal.BP.route('/%s/id' % (Journal.name), methods=['GET'])
def get_id():
    """
        Return nodes ID this API is running on.
    """
    this_node_id = sys_utils.get_hardware_id()
    return flask.make_response(flask.jsonify({
        'id' : this_node_id }), 200)


@Journal.BP.route('/%s/nodes' % (Journal.name), methods=['GET'])
def get_nodes():
    """
        Return [{ 'node_name' : 'node_id' }] list of all currently known nodesids to
    this API.
    """
    # Revisit: this is broken
    endpoints = Journal.mainapp.config['ENDPOINTS']
    url = os.path.join(endpoints['base'], endpoints['registries'])
    registries = HTTP_REQUESTS.get(url)
    content = json.loads(registries.content)
    result = {}
    for node_name, node_id in content['Members'][0].items():
        node_name = node_name.split('@')[-1]
        result[node_name] = node_id.split('/')[-1]

    return flask.make_response(flask.jsonify({ 'nodes' : result }), 200)

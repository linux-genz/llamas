#!/usr/bin/python3
import flask
import json
import jsonschema
import requests as HTTP_REQUESTS
from pdb import set_trace

import flask_fat
Journal = self = flask_fat.Journal(__file__)


""" ------------------------------- ROUTES ------------------------------- """

@Journal.BP.route('/%s/register/<id>' % Journal.name, methods=['POST'])
def register_device(id=None):
    response_message: str = 'ID %s received.' % id

    return flask.make_response(flask.jsonify({
        'status' : response_message }), 200)
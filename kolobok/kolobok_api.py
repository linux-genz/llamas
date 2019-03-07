#!/usr/bin/python3
import argparse
import json

#https://github.com/FabricAttachedMemory/flask-api-template.git
import flask_fat


class KolobokServer(flask_fat.APIBaseline):

    def __init__(self, cfg, **kwargs):
        super().__init__(cfg, **kwargs)


def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ignore',
                        help='blueprints to be ignored/not-loaded by server. ' +\
                            '--ignore "bp1,bp2,bp2"', default=None)

    parser.add_argument('--verbose', help='You know it.', action='store_true')
    parsed = parser.parse_args()
    if parsed.ignore is not None:
        parsed.ignore = parsed.ignore.replace(' ', '').split(',')
    return vars(parsed)


def main(args=None):
    args = {} if args is None else args
    cmd = parse_cmd()
    args.update(cmd)

    mainapp = KolobokServer('./config', **args)
    if not args.get('dont_run', False):
        mainapp.run()
    return mainapp


if __name__ == '__main__':
    main()

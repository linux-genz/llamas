#/usr/lib/python3
"""
 Bunch of funtions that gets information from the System in one or or another.
"""

def get_hardware_id():
    id = ''
    with open('/etc/machine-id', 'r') as file_obj:
        id = file_obj.read().split('\n')[0]
    return id
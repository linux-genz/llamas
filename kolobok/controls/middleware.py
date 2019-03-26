#!/usr/bin/python3.6


class Device:
    '''
        Store information about created devices and notify kernel when this object
    is created.
    '''

    def __init__(self, json_data: dict):
        self._data: dict = json_data

        self.kernel_msg = self.notify_kernel()
        self.handle_kernel_response(kernel_msg)


    def notify_kernel(self):
        '''
            Send a message about the device state to a kernal and return its
        response (success of fail)
        '''
        raise NotImplementedError('notify_kernel - not today. Come back tomorrow.')


    def handle_kernel_response(self, msg):
        '''
            A kernel will return a status respons when it receives a message from
        user space. This function need to evaluate the message and take actions
        if a failur has happened.
        '''
        raise NotImplementedError('handle_kernel_response - not today. Come back tomorrow.')


    @property
    def cuuid(self) -> int:
        return self.get('CUUID')


    @property
    def suuid(self) -> int:
        return self.get('SUUID')


    def get(self, key, default=None):
        return self._data.get(key, default)



if __name__ == '__main__':
    d = Device({})
    print(d.cuuid)
    print(d.suuid)
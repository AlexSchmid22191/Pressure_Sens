from serial import Serial
from time import sleep
from threading import Lock


class CenterThree(Serial):
    def __init__(self, port, *args, **kwargs):
        Serial.__init__(self, port, timeout=1.5, baudrate=9600)
        self.com_lock = Lock()

        sleep(1)

        with self.com_lock:
            self.write('UNI,0\n'.encode())
            self.readline()
            self.write('\x05\n'.encode())
            self.readline()

    def read_pressure(self, channel):
        with self.com_lock:

            self.write('PR{:d}\n'.format(channel).encode())
            self.readline()
            self.write('\x05\n'.encode())
            answer = self.readline().decode()

            try:
                return float(answer.split(',')[-1])

            except ValueError:
                return answer

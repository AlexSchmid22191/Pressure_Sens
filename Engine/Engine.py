from datetime import datetime
from threading import Lock
from threading import Timer
from time import sleep
from time import time
from math import nan

from pubsub.pub import sendMessage, subscribe, unsubscribe
from serial import SerialException, SerialTimeoutException

from Devices.Leybold import CenterThree
from ThreadDecorators import in_new_thread


class LoggerEngine:
    def __init__(self):

        # To prevent multiple devices writing to the same variable
        self.com_lock = Lock()

        self.sensor_types = {'Leybold Center Three': CenterThree}

        self.sensor = None
        self.sensor_port = None

        self.sensor_pressures = [nan] * 3

        #self.datalogger = Datalogger(master=self)

        subscribe(self.add_sensor, 'gui.con.connect_sensor')
        subscribe(self.remove_sensor, 'gui.con.disconnect_sensor')

    def set_sensor_port(self, port):
        self.sensor_port = port

    def add_sensor(self, sensor_type, sensor_port):
        try:
            self.sensor = self.sensor_types[sensor_type](port=sensor_port)
            sleep(1)
            subscribe(self.get_sensor_pressure, 'gui.request.sensor_temp')
            sendMessage(topicName='engine.status', text='Sensor connected!')
        except SerialException:
            sendMessage(topicName='engine.status', text='Connection error!')

    def remove_sensor(self):
        self.sensor.close()
        unsubscribe(self.get_sensor_pressure, 'gui.request.sensor_temp')
        sendMessage(topicName='engine.status', text='Sensor disconnected!')

    @in_new_thread
    def get_sensor_pressure(self, channel):
        try:
            answer = self.sensor.read_temperature(channel=channel)
            if isinstance(answer, str):
                sendMessage(topicName='engine.status', text='Sensor error: ' + answer)
                self.sensor_pressures[channel] = nan
            else:
                self.sensor_pressures[channel] = answer
                sendMessage(topicName='engine.answer.sensor_pressure', channel=channel,
                            pressure=self.sensor_pressures[channel])
        except (SerialException, SerialTimeoutException):
            sendMessage(topicName='engine.status', text='Connection error!')


class Datalogger:
    def __init__(self, master):
        self.master = master

        self.logfile_path = 'Logs/Default.txt'
        self.is_logging = False

        self.interval = 1

        subscribe(self.set_interval, 'gui.log.interval')
        subscribe(self.start_log, 'gui.log.start')
        subscribe(self.stop_log, 'gui.log.stop')
        subscribe(self.continue_log, 'gui.log.continue')
        subscribe(self.set_logfile, 'gui.log.filename')

    @in_new_thread
    def write_log(self):
        answer = self.master.sensor.read_temperature()
        if isinstance(answer, str):
            self.master.sensor_temperature = nan
        else:
            self.master.sensor_temperature = answer

        abs_time = datetime.now()
        timestring = abs_time.strftime('%d.%m.%Y - %H:%M:%S')
        unixtime = float(time())

        with open(self.logfile_path, 'a') as logfile:
            logfile.write('{:s}\t{:.3f}\t{:5.1f}\n'.format(timestring, unixtime, self.master.sensor_temperature))

        if self.is_logging:
            log_timer = Timer(interval=self.interval, function=self.write_log)
            log_timer.start()

    def set_logfile(self, filename):
        self.logfile_path = filename

    def set_interval(self, inter):
        self.interval = inter

    def start_log(self):
        if not self.is_logging:
            self.is_logging = True
            with open(self.logfile_path, 'a') as logfile:
                logfile.write('Time\tUnixtime (s)\tPressure Channel 1 (mbar)\tPressure Channel 2 (mbar)\t'
                              'Pressure Channel 3 (mbar)\t \n')

            self.write_log()

    def stop_log(self):
        self.is_logging = False

    def continue_log(self):
        self.is_logging = True
        self.write_log()

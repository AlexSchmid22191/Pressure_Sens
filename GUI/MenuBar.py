import wx
import os
from pubsub.pub import sendMessage
from serial.tools.list_ports import comports


class Menubar(wx.MenuBar):
    def __init__(self, _=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        filemenu = wx.Menu()
        self.savefig = filemenu.Append(item='Save Plot', id=wx.ID_SAVEAS)
        filemenu.Append(item='Quit', id=wx.ID_CLOSE)

        self.channelmenu = wx.Menu()
        for channel in range(1, 4):
            self.channelmenu.Append(item=str(channel), id=wx.ID_ANY, kind=wx.ITEM_RADIO)

        self.logmenu = LoggingMenu()
        self.devmenu = DeviceMenu()
        self.plotmenu = PlottingMenu()
        self.stylmenu = StyleMenu()

        self.Append(filemenu, 'File')
        self.Append(self.devmenu, 'Device')
        self.Append(self.channelmenu, 'Channels')
        self.Append(self.logmenu, 'Logging')
        self.Append(self.plotmenu, 'Plotting')
        self.Append(self.stylmenu, 'Style')


class DeviceMenu(wx.Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sensor_type_menu = wx.Menu()
        self.sensor_type_menu.Append(item='Leybold Center Three', id=wx.ID_ANY, kind=wx.ITEM_RADIO)

        self.sensor_com_menu = PortMenu()
        self.AppendSubMenu(text='Sensor type', submenu=self.sensor_type_menu)
        self.AppendSubMenu(text='Sensor port', submenu=self.sensor_com_menu)
        sensor_connect = self.Append(id=wx.ID_ANY, item='Connect sensor', kind=wx.ITEM_CHECK)

        self.Bind(event=wx.EVT_MENU, handler=self.connect_sensor, source=sensor_connect)

    def connect_sensor(self, event):
        item = self.FindItemById(event.GetId())

        if item.IsChecked():
            sensor_port, sensor_type = None, None
            for port_item in self.sensor_com_menu.GetMenuItems():
                if port_item.IsChecked():
                    sensor_port = self.sensor_com_menu.port_dict[port_item.GetItemLabelText()]

            for type_item in self.sensor_type_menu.GetMenuItems():
                if type_item.IsChecked():
                    sensor_type = type_item.GetItemLabelText()

            sendMessage(topicName='gui.con.connect_sensor', sensor_type=sensor_type, sensor_port=sensor_port)

        else:
            sendMessage(topicName='gui.con.disconnect_sensor')


class PortMenu(wx.Menu):
    def __init__(self):
        super().__init__()

        self.portdict = self.port_dict = {port[1]: port[0] for port in comports()}
        self.portItems = [wx.MenuItem(parentMenu=self, id=wx.ID_ANY, text=port, kind=wx.ITEM_RADIO)
                          for port in list(self.port_dict.keys())]

        for item in self.portItems:
            self.Append(item)


class LoggingMenu(wx.Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        start = self.Append(item='Start', id=wx.ID_ANY)
        stop = self.Append(item='Stop', id=wx.ID_ANY)
        cont = self.Append(item='Continue', id=wx.ID_ANY)

        self.Bind(event=wx.EVT_MENU, source=start, handler=self.start_log)
        self.Bind(event=wx.EVT_MENU, source=stop, handler=self.stop_log)
        self.Bind(event=wx.EVT_MENU, source=cont, handler=self.continue_log)

        self.inter = wx.Menu()
        for inter in ('0.2', '0.5', '1', '2'):
            self.inter.Append(item=inter, id=wx.ID_ANY, kind=wx.ITEM_RADIO)

        self.inter.GetMenuItems()[2].Check()

        self.inter.Bind(wx.EVT_MENU, handler=self.set_interval)

        self.AppendSubMenu(submenu=self.inter, text='Update interval (ms)')

    def start_log(self, *args):
        dlg = wx.FileDialog(self.Parent, message="Choose log file destination", defaultDir='./Logs/',
                            style=wx.FD_SAVE | wx.FD_CHANGE_DIR)

        if dlg.ShowModal() == wx.ID_OK:
            log_path = dlg.GetPath()
            if not log_path[-4:] == '.dat':
                log_path += '.dat'
            sendMessage(topicName='gui.log.filename', filename=log_path)
            sendMessage(topicName='gui.log.start')
        dlg.Destroy()

        args[0].Skip()

    def set_interval(self, event):
        inter = float(self.FindItemById(event.GetId()).GetItemLabel())
        sendMessage('gui.log.interval', inter=inter)

    @staticmethod
    def stop_log(*args):
        sendMessage(topicName='gui.log.stop')

    @staticmethod
    def continue_log(*args):
        sendMessage(topicName='gui.log.continue')


class PlottingMenu(wx.Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.start = self.Append(item='Start', id=wx.ID_ANY)
        self.stop = self.Append(item='Stop', id=wx.ID_ANY)
        self.resume = self.Append(item='Resume', id=wx.ID_ANY)
        self.clear = self.Append(item='Clear', id=wx.ID_ANY)
        self.AppendSeparator()

        self.inter = wx.Menu()
        for inter in ('0.5', '1', '2', '5'):
            self.inter.Append(item=inter, id=wx.ID_ANY, kind=wx.ITEM_RADIO)

        self.inter.GetMenuItems()[1].Check()

        self.AppendSubMenu(submenu=self.inter, text='Update interval (s)')


class StyleMenu(wx.Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for style in os.listdir('Styles'):
            self.Append(item=os.path.splitext(style)[0], id=wx.ID_ANY, kind=wx.ITEM_RADIO)

        self.GetMenuItems()[0].Check()

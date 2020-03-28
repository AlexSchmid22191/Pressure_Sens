import wx
from pubsub.pub import sendMessage, subscribe
from ThreadDecorators import in_main_thread
from GUI.MenuBar import Menubar
from GUI.Matplot import MatplotWX


class LoggerInterface(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.SetTitle('Thermo Logger')

        self.status_bar = wx.StatusBar(parent=self)
        self.SetStatusBar(statusBar=self.status_bar)

        self.clear_timer = wx.Timer(self)
        self.clear_timer.Bind(event=wx.EVT_TIMER, handler=self.clear_status_bar)
        subscribe(listener=self.update_status_bar, topicName='engine.status')

        self.interval = 1000
        self.channels = 1

        self.request_timer = wx.Timer()
        self.request_timer.Bind(event=wx.EVT_TIMER, handler=self.request_data)
        self.request_timer.Start(milliseconds=self.interval)

        self.menu_bar = Menubar()
        self.SetMenuBar(self.menu_bar)

        self.Bind(event=wx.EVT_MENU, handler=self.on_quit, id=wx.ID_CLOSE)
        self.Bind(event=wx.EVT_MENU, handler=self.save_image, id=wx.ID_SAVEAS)

        self.Bind(wx.EVT_MENU_RANGE, handler=self.set_interval, id=self.menu_bar.plotmenu.inter.GetMenuItems()[0].GetId(),
                  id2=self.menu_bar.plotmenu.inter.GetMenuItems()[-1].GetId())

        self.Bind(wx.EVT_MENU_RANGE, handler=self.change_style, id=self.menu_bar.stylmenu.GetMenuItems()[0].GetId(),
                  id2=self.menu_bar.stylmenu.GetMenuItems()[-1].GetId())

        self.Bind(wx.EVT_MENU_RANGE, handler=self.set_number_of_channels,
                  id=self.menu_bar.channelmenu.GetMenuItems()[0].GetId(),
                  id2=self.menu_bar.channelmenu.GetMenuItems()[-1].GetId())

        self.matplot = MatplotWX(channels=self.channels, parent=self)
        self.Fit()

        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.start, handler=self.matplot.start_plotting)
        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.stop, handler=self.matplot.stop_plotting)
        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.clear, handler=self.matplot.clear_plot)
        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.resume, handler=self.matplot.cont_plotting)

        self.Show(True)

    def set_interval(self, event):
        inter = self.menu_bar.plotmenu.FindItemById(event.GetId()).GetItemLabel()
        self.interval = int(float(inter)*1000)
        self.request_timer.Start(milliseconds=self.interval)

    @in_main_thread
    def update_status_bar(self, text):
        self.status_bar.SetStatusText(text)
        self.clear_timer.Start(milliseconds=3000, oneShot=wx.TIMER_ONE_SHOT)

    @in_main_thread
    def clear_status_bar(self, *args):
        """Clear the status bar"""
        self.status_bar.SetStatusText('')

    def save_image(self, *args):
        dlg = wx.FileDialog(self.Parent, message="Choose file destination", defaultDir='./Pics/',
                            style=wx.FD_SAVE | wx.FD_CHANGE_DIR)

        if dlg.ShowModal() == wx.ID_OK:
            log_path = dlg.GetPath()
            self.matplot.figure.savefig(log_path)
        dlg.Destroy()

    def on_quit(self, *args):
        wx.GetApp().ExitMainLoop()
        self.Close()

    def request_data(self, *args):
        for channel in range(self.channels):
            sendMessage(topicName='gui.request.pressure', channel=channel)

    def change_style(self, event):
        self.matplot.set_style(self.menu_bar.stylmenu.FindItemById(event.GetId()).GetItemLabel())

    def set_number_of_channels(self, event):
        self.channels = int(self.menu_bar.channelmenu.FindItemById(event.GetId()).GetItemLabel())
        self.matplot.change_numberof_channels(self.channels)
        self.Fit()

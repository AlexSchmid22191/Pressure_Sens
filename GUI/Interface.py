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
        self.Bind(wx.EVT_TIMER, source=self.clear_timer, handler=self.clear_status_bar)
        subscribe(listener=self.update_status_bar, topicName='engine.status')

        self.interval = 1000

        self.timer = wx.Timer()
        self.timer.Bind(event=wx.EVT_TIMER, handler=self.request_data)
        self.timer.Start(milliseconds=self.interval)

        self.menu_bar = Menubar()
        self.SetMenuBar(self.menu_bar)

        self.Bind(event=wx.EVT_MENU, handler=self.on_quit, id=wx.ID_CLOSE)
        self.Bind(event=wx.EVT_MENU, handler=self.save_image, id=wx.ID_SAVEAS)

        self.Bind(wx.EVT_MENU_RANGE, handler=self.set_interval, id=self.menu_bar.plotmenu.inter.GetMenuItems()[0].GetId(),
                  id2=self.menu_bar.plotmenu.inter.GetMenuItems()[-1].GetId())

        self.Bind(wx.EVT_MENU_RANGE, handler=self.change_style, id=self.menu_bar.stylmenu.GetMenuItems()[0].GetId(),
                  id2=self.menu_bar.stylmenu.GetMenuItems()[-1].GetId())

        self.Bind(wx.EVT_MENU_RANGE, handler=self.draw_matplot, id=self.menu_bar.channelmenu.GetMenuItems()[0].GetId(),
                  id2=self.menu_bar.channelmenu.GetMenuItems()[-1].GetId())

        self.matplot = None
        self.draw_matplot()

        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.start, handler=self.matplot.start_plotting)
        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.stop, handler=self.matplot.stop_plotting)
        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.clear, handler=self.matplot.clear_plot)
        self.Bind(wx.EVT_MENU, source=self.menu_bar.plotmenu.resume, handler=self.matplot.cont_plotting)

        self.Show(True)

    def set_interval(self, event):
        inter = self.menu_bar.plotmenu.FindItemById(event.GetId()).GetItemLabel()
        self.interval = int(float(inter)*1000)
        self.timer.Start(milliseconds=self.interval)

    @in_main_thread
    def update_status_bar(self, text):
        self.status_bar.SetStatusText(text)
        self.clear_timer.Start(milliseconds=3000, oneShot=wx.TIMER_ONE_SHOT)

    @in_main_thread
    def clear_status_bar(self, *args):
        """Clear the status bar"""
        self.status_bar.SetStatusText('')

    def save_image(self, *args):
        dlg = wx.FileDialog(self.Parent, message="Choose log file destination", defaultDir='./Pics/',
                            style=wx.FD_SAVE | wx.FD_CHANGE_DIR)

        if dlg.ShowModal() == wx.ID_OK:
            log_path = dlg.GetPath()
            self.matplot.figure.savefig(log_path)
        dlg.Destroy()

    def on_quit(self, *args):
        self.Close()

    @staticmethod
    def request_data(*args):
        sendMessage(topicName='gui.request.sensor_temp')

    def change_style(self, event):
        self.matplot.set_style(self.menu_bar.stylmenu.FindItemById(event.GetId()).GetItemLabel())

    def draw_matplot(self, *event):

        # Infer number of channels if redraw is triggered by GUI, else use default of 1
        channels = int(self.menu_bar.channelmenu.FindItemById(event[0].GetId()).GetItemLabel()) if event else 1

        self.matplot = MatplotWX(channels=channels, parent=self)
        vbox = wx.BoxSizer(orient=wx.VERTICAL)
        vbox.Add(self.matplot, flag=wx.EXPAND | wx.FIXED_MINSIZE, proportion=1)

        vbox.Fit(self)
        self.SetSizer(vbox)
        self.SetMinSize((400*channels+16, 482))
        self.Fit()
        self.Raise()


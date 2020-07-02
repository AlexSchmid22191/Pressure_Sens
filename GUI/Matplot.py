import wx
import os
import numpy as np
import matplotlib as mpl; mpl.use('WXAgg')
import matplotlib.pyplot as plt
from datetime import datetime
from pubsub.pub import subscribe, unsubscribe, sendMessage
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from ThreadDecorators import in_main_thread


class MatplotWX(wx.Panel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        subscribe(listener=self.update_pressures, topicName='engine.answer.sensor_pressure')

        self.interval = 1000
        self.is_plotting = False
        self.startime = datetime.now()

        self.styles = {s_file[:-9]: mpl.rc_params_from_file(os.path.join('Styles', s_file), use_default_template=False)
                       for s_file in os.listdir('Styles')}
        self.current_style = list(self.styles)[1]

        self.request_timer = wx.Timer()
        self.request_timer.Bind(event=wx.EVT_TIMER, handler=self.request_data)
        self.request_timer.Start(milliseconds=self.interval)

        self.channel_states = {1: True, 2: False, 3: False}

        n_actives = sum(self.channel_states.values())
        actives = [channel for channel in self.channel_states if self.channel_states[channel]]

        self.figure = plt.Figure(figsize=(4*n_actives, 4))
        self.axes = {channel: self.figure.add_subplot(1, n_actives, position+1) for
                     (channel, position) in zip(actives, range(n_actives))}

        self.plots = {channel: self.axes[channel].plot([])[0] for channel in actives}
        self.texts = {channel: self.axes[channel].text(0.05, 0.9, '{:.2f} mbar'.format(0), transform=self.axes[channel].
                                                       transAxes, size=12) for channel in actives}

        for channel in self.axes:
            self.axes[channel].set_title('Channel {:d}'.format(channel))
            self.axes[channel].set_xlabel('Time (s)')
            self.axes[channel].set_ylabel('Pressure (mbar)')

        self.set_style(self.current_style)

        self.canvas = FigureCanvas(self, -1, self.figure)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, flag=wx.GROW | wx.FIXED_MINSIZE, proportion=2)
        self.SetSizer(self.sizer)
        self.Fit()
        self.figure.tight_layout()

    def request_data(self, *args):
        for channel in self.channel_states:
            if self.channel_states[channel]:
                sendMessage(topicName='gui.request.pressure', channel=channel)

    @in_main_thread
    def update_pressures(self, channel, pressure):
        self.texts[channel].set_text('{:.1f} mbar'.format(pressure))
        self.figure.canvas.draw()

    @in_main_thread
    def add_pressure_data_point(self, channel, pressure):
        delta_t = datetime.now() - self.startime
        time = delta_t.days*86400.0 + delta_t.seconds + delta_t.microseconds/1000000.0

        self.plots[channel].set_xdata(np.append(self.plots[channel].get_xdata(), time))
        self.plots[channel].set_ydata(np.append(self.plots[channel].get_ydata(), pressure))

        self.axes[channel].relim()
        self.axes[channel].autoscale_view()
        self.figure.canvas.draw()

    def start_plotting(self, *args):
        if not self.is_plotting:
            self.is_plotting = True
            self.startime = datetime.now()
            subscribe(topicName='engine.answer.sensor_pressure', listener=self.add_pressure_data_point)

    def stop_plotting(self, *args):
        self.is_plotting = False
        unsubscribe(topicName='engine.answer.sensor_pressure', listener=self.add_pressure_data_point)

    def cont_plotting(self, *args):
        self.is_plotting = True
        subscribe(topicName='engine.answer.sensor_pressure', listener=self.add_pressure_data_point)

    def clear_plot(self, *args):
        for plot in self.plots.values():
            plot.set_xdata([])
            plot.set_ydata([])
        self.figure.canvas.draw()

    def set_interval(self, interval):
        self.interval = interval
        self.request_timer.Start(milliseconds=self.interval)

    def set_style(self, style):
        self.current_style = style
        try:
            self.figure.set_facecolor(self.styles[style]['figure.facecolor'])

            for ax in self.axes.values():
                ax.set_facecolor(self.styles[style]['axes.facecolor'])
                ax.spines['top'].set_color(self.styles[style]['axes.edgecolor'])
                ax.spines['left'].set_color(self.styles[style]['axes.edgecolor'])
                ax.spines['right'].set_color(self.styles[style]['axes.edgecolor'])
                ax.spines['bottom'].set_color(self.styles[style]['axes.edgecolor'])

                ax.title.set_color(self.styles[style]['axes.edgecolor'])

                ax.xaxis.label.set_color(self.styles[style]['axes.labelcolor'])
                ax.yaxis.label.set_color(self.styles[style]['axes.labelcolor'])
                ax.tick_params(which='both', axis='x', labelcolor=self.styles[style]['xtick.color'],
                               color=self.styles[style]['xtick.color'])
                ax.tick_params(which='both', axis='y', labelcolor=self.styles[style]['ytick.color'],
                               color=self.styles[style]['ytick.color'])

            for plot in self.plots.values():
                plot.set_color(self.styles[style]['lines.color'])

            for text in self.texts.values():
                text.set_color(self.styles[style]['text.color'])

            self.figure.canvas.draw()

        except KeyError:
            print('error')
            # TODO: Implement a proper default styling case

    def change_active_channels(self, channel, state):

        self.channel_states[channel] = state

        n_actives = sum(self.channel_states.values())
        actives = [channel for channel in self.channel_states if self.channel_states[channel]]

        self.figure = plt.figure(figsize=(4 * n_actives, 4))
        self.axes = {channel: self.figure.add_subplot(1, n_actives, position + 1) for
                     (channel, position) in zip(actives, range(n_actives))}

        self.plots = {channel: self.axes[channel].plot([])[0] for channel in actives}
        self.texts = {channel: self.axes[channel].text(0.05, 0.9, '{:.2f} mbar'.format(0), transform=self.axes[channel].
                                                       transAxes, size=12) for channel in actives}

        for channel in self.axes:
            self.axes[channel].set_title('Channel {:d}'.format(channel))
            self.axes[channel].set_xlabel('Time (s)')
            self.axes[channel].set_ylabel('Pressure (mbar)')

        self.set_style(self.current_style)

        self.canvas = FigureCanvas(self, -1, self.figure)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, flag=wx.GROW | wx.FIXED_MINSIZE, proportion=2)
        self.SetSizer(self.sizer)
        self.Fit()
        self.figure.tight_layout()

import wx
from threading import Timer, enumerate
from GUI.Interface import LoggerInterface


def main():
    ex = wx.App()
    gui = LoggerInterface(parent=None)
    print('GUI initialized: {:s}'.format(str(gui.__class__)))
    ex.MainLoop()


if __name__ == '__main__':
    main()
    for thread in enumerate():
        if type(thread) == Timer:
            thread.cancel()

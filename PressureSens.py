import threading
import wx
from pubsub.pub import addTopicDefnProvider, TOPIC_TREE_FROM_CLASS

import Topic_Def
from GUI.Interface import LoggerInterface
from Engine.Engine import LoggerEngine

addTopicDefnProvider(Topic_Def, TOPIC_TREE_FROM_CLASS)


def main():
    ex = wx.App()
    gui = LoggerInterface(parent=None)
    engine = LoggerEngine()
    print('Engine initilized: {:s}'.format(str(engine.__class__)))
    print('GUI initialized: {:s}'.format(str(gui.__class__)))
    ex.MainLoop()


if __name__ == '__main__':
    main()
    for thread in threading.enumerate():
        if type(thread) == threading.Timer:
            thread.cancel()

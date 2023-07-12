'''
tk toplevel window wrapping a matplotlib figure
'''

from tkinter import BOTH, TOP, Toplevel, Frame
import numpy as np

from modules.windows.window import Window

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class pltwindow(Window):
    '''
    tk toplevel window wrapping a matplotlib figure
    '''

    def __init__(self, icon=None):
        super().__init__()
        self.initiated = None
        self.canvas_frame = None
        self.icon = icon

    def initTk(self, fig, title:str=None):
        self.initiated = True

        if self.main is None:
            self.main = Toplevel()
            # self.main.group(self.app.main.main)
            self.main.bind('<Escape>', lambda e: self._quit())
            if self.icon is not None:
                self.main.tk.call('wm', 'iconphoto', self.main._w, self.icon)

        # if the frame exists, detroy it
        if self.canvas_frame is not None:
            self.canvas_frame.destroy()
            # for item in self.canvas.get_tk_widget().find_all():
            #     self.canvas.get_tk_widget().delete(item)

        if title is not None:
            self.main.wm_title(title)

        self.canvas_frame = Frame(self.main, borderwidth=0)
        self.canvas_frame.pack(side=TOP, fill=BOTH, expand=1)
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)


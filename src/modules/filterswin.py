'''
Window for app's config
'''

from tkinter import ttk

import tkinter as tk
from tkinter.ttk import Button, Entry, OptionMenu, LabelFrame

from modules.window import Window

class Filterswindow(Window):
    '''
    Window for app's config
    '''

    def __init__(self, app, icon):
        super().__init__(icon)
        self.app = app
        self.root = None
        self.frame = None
        self.buttons = {}

    def show(self, filters_list):
        ### init the toplevel tk element
        if self.root is None or not self.root.winfo_exists():
            self.root = tk.Toplevel(self.app.main.root)
            self.root.group(self.app.main.root)
            self.root.bind('<Escape>', lambda e: self._quit())
            if self.icon is not None:
                self.root.tk.call('wm', 'iconphoto', self.root._w, self.icon)

        self.root.wm_title("Filters")

        # if the button exists, detroy it
        if self.buttons is not None and not len(self.buttons) == 0:
            print("self.buttons had: "+str(len(self.buttons))+" buttons")
            for dict_key in self.buttons:
                self.buttons[dict_key].destroy()
            self.buttons = {}
        
        self.buttons[0] = Button(self.root, text='New filter', style='Accent.TButton', command=lambda: Newfilterwindow(self, self.icon))
        self.buttons[0].pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=5, pady=5)

        # if the frame exists, detroy it
        if self.frame is not None:
            self.frame.destroy()
            
        self.frame = LabelFrame(self.root, text="Active filters")
        self.frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=5, pady=5)
        
        r = 1
        for filter_tuple in filters_list:
            c = 0
            tk.Label(self.frame, text=filter_tuple[0]).grid(row=r, column=c, padx=5, pady=5, sticky="w")
            c += 1
            tk.Label(self.frame, text=filter_tuple[1]).grid(row=r, column=c, padx=5, pady=5, sticky="w")
            c += 1
            self.buttons[r] = Button(self.frame, text='X', style='Red.TButton', command=lambda: self.remove_filter(filter_tuple))
            self.buttons[r].grid(row=r, column=c, padx=5, pady=5)
            r += 1

        self.buttons[r] = Button(self.root, text='Delete all filters', style='Red.TButton', command=self.remove_all_filters)
        self.buttons[r].pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=5, pady=5)

    def remove_filter(self, filter_tuple):
        self.app.filters_list.remove(filter_tuple)
        self.app.update_subset()
        if len(self.app.filters_list) == 0:
            self._quit()
        else:
            self.show(self.app.filters_list)

    def remove_all_filters(self):
        self.app.filters_list = []
        self.app.update_subset()
        self._quit()
        

class Newfilterwindow(Window):

    def __init__(self, master, icon):
        super().__init__(icon)
        self.master = master
        self.root = None
        self.root = tk.Toplevel(self.master.app.main.root)
        self.root.group(self.master.app.main.root)
        self.root.bind('<Escape>', lambda e: self._quit())
        self.root.tk.call('wm', 'iconphoto', self.root._w, self.icon)
        self.root.wm_title("Add new filter")
        self.tk_frame = tk.Frame(self.root, borderwidth=0)
        self.tk_frame.pack(side=tk.TOP, fill=tk.Y, expand=1)
        self.tk_column = tk.StringVar()
        self.tk_columns_opt = OptionMenu(self.tk_frame, self.tk_column, *self.master.app.config['display_columns']) # , command=self.app.group_change
        self.tk_columns_opt.grid(row=0, column=0, padx=5, pady=5)
        self.tk_value_entry = Entry(self.tk_frame)
        self.tk_value_entry.grid(row=1, column=0, padx=5, pady=5)
        self.tk_button = Button(self.tk_frame, text='Add', command=lambda: master.app.add_quick_filter(self.tk_column.get(), self.tk_value_entry.get()))
        self.tk_button.grid(row=2, column=0, padx=5, pady=5)

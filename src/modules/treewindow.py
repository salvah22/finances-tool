'''
tk toplevel window wrapping a treeview
'''

from tkinter import ttk
import tkinter as tk
import pandas as pd

from typing import List

from modules.window import Window

from utils.tk_inter import treeview_sort_column

class Treewindow(Window):
    '''
    tk toplevel window wrapping a treeview
    '''

    def __init__(self, app, icon=None):
        super().__init__()
        self.initiated = None
        self.tree_frame = None
        self.dataframe = None
        self.position = None
        self.title = None
        self.headings = None
        self.tree = None
        self.app = app
        self.icon = icon

    def close(self):
        if self.initiated:
            self.main.destroy()

    def update(self, dataframe: pd.DataFrame, title:str=None, position:list=None, headings=True):
        self.initiated = True
        self.headings = headings
        self.set_data_frame(dataframe)
        if self.main is None or not self.main.winfo_exists():
            self.main = tk.Toplevel(self.app.main.main)
            self.main.group(self.app.main.main)
            self.main.bind('<Escape>', lambda e: self._quit())
            if self.icon is not None:
                self.main.tk.call('wm', 'iconphoto', self.main._w, self.icon)
        self.title = title
        if self.title is not None:
            self.main.wm_title(title)
        self.position = position
        self.update_tk()

    def set_data_frame(self, dataframe):
        self.dataframe = dataframe

    def update_tk(self):

        # look
        width = 130 * self.dataframe.shape[1]
        
        # use a scroll bar for dataframes with more than 15 rows
        if self.dataframe.shape[0] > 15:
            scrollbar_bool=True
            width += 15 # for the scrollbar
            height = 450 + 25
        else:
            scrollbar_bool=False
            height = 30 * self.dataframe.shape[0] + 25 # 30 per row + 25 margin

        if self.position is not None:
            self.main.geometry(f'{width}x{height}+{self.position[0]}+{self.position[1]}') # (width, height, x, y)
        else:
            self.main.geometry(f'{width}x{height}')
        
        # frame
        if self.tree_frame is not None:
            self.tree_frame.destroy()

        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self.tree_frame = tk.Frame(self.main, borderwidth=0)
        self.tree_frame.grid(column=0, row=0, sticky="nsew")

        # treeview
        if self.headings:
            self.tree = ttk.Treeview(self.tree_frame, style="mystyle.Treeview", columns=list(self.dataframe.columns), height=self.dataframe.shape[0], show='headings')
        else:
            self.tree = ttk.Treeview(self.tree_frame, style="mystyle.Treeview", columns=list(self.dataframe.columns), height=self.dataframe.shape[0], show='tree')

        self.tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        self.tree.bind("<Double-Button-1>", self.do_popup)
        self.tree.bind("<Button-3>", self.do_popup)

        if scrollbar_bool:
            scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
            self.tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        for colname in (self.dataframe.columns):
            self.tree.column(colname, anchor='center', width=130, stretch=tk.YES)
            if self.headings:
                self.tree.heading(colname, text=colname, anchor='center', command=lambda _col=colname: treeview_sort_column(self.tree, _col, False))

        self.update_tree_records()

    def update_tree_records(self, columns: List[str] = []):
        self.tree.delete(*self.tree.get_children()) # delete data for next rendering)

        if columns == []:
            columns = list(self.dataframe.columns)
        
        for row in self.dataframe[columns].to_numpy():
            self.tree.insert("", 0, values=row.tolist())

    def do_popup(self, event):
        iid = self.tree.identify_row(event.y)
        try:
            if iid:
                self.tree.selection_set(iid)
                popup = Popup(self, self.tree.item(iid, 'values'))
                popup.tk_popup(event.x_root, event.y_root)

        finally:
            popup.grab_release()


class Popup(tk.Menu):
    def __init__(self, master, kvp):
        tk.Menu.__init__(self, master.main, tearoff=0)
        self.add_command(label="Filter with", command=lambda: master.app.add_quick_filter(kvp[0], kvp[1]))
        self.bind("<FocusOut>", lambda x: self.destroy())

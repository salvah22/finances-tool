'''
tk toplevel window wrapping a treeview
'''

from tkinter import ttk
import tkinter as tk
import pandas as pd

from typing import List

from .window import Window

from utils.tk_inter import treeview_sort_column

class Treewindow(Window):
    '''
    tk toplevel window wrapping a treeview, used for balances and details
    '''

    def __init__(self, app, icon=None, purpose=None):
        super().__init__(icon)
        self.initiated = None
        self.tree_frame = None
        self.dataframe = None
        self.position = None
        self.title = None
        self.headings = None
        self.tree = None
        self.app = app
        self.purpose = purpose
        self.tree_records = None
        self.width = None
        self.height = None
        self.scrollbar_bool = None


    def close(self):
        if self.initiated:
            self.root.destroy()


    def update_plus_tk(self,**args):
        self.update(**args)
        self.update_tk()


    def update(self, dataframe: pd.DataFrame, title:str=None, position:list=None, headings=True):
        self.initiated = True
        self.headings = headings
        self.dataframe = dataframe
        self.tree_records = self.dataframe.shape[0]
        self.position = position
        self.title = title


    def update_tk(self):

        if self.root is None or not self.root.winfo_exists():
            self.root = tk.Toplevel(self.app.main.root)
            self.root.group(self.app.main.root)
            self.root.bind('<Escape>', lambda e: self._quit())
            if self.icon is not None:
                self.root.tk.call('wm', 'iconphoto', self.root._w, self.icon)
        if self.title is not None:
            self.root.wm_title(self.title)

        # look
        self.width = 130 * self.dataframe.shape[1]
        self.height = self.tree_records * 30 + 25
        
        # use a scroll bar for dataframes with more than 15 rows
        if self.dataframe.shape[0] > self.tree_records:
            self.scrollbar_bool=True
            self.width += 15 # for the scrollbar
        else:
            self.scrollbar_bool=False

        if self.position is not None:
            self.root.geometry(f'{self.width+self.position[0]}x{self.height+self.position[1]}+{self.position[2]}+{self.position[3]}') # (width_offset, height_offset, x, y)
        else:
            self.root.geometry(f'{self.width}x{self.height}')
        
        if self.purpose != "group":
        
            # frame
            if self.tree_frame is not None:
                self.tree_frame.destroy()

            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)

            self.tree_frame = tk.Frame(self.root, borderwidth=0)
            self.tree_frame.grid(column=0, row=0, sticky="nsew")

            # treeview
            if self.headings:
                self.tree = ttk.Treeview(self.tree_frame, style="mystyle.Treeview", columns=list(self.dataframe.columns), height=self.dataframe.shape[0], show='headings')
            else:
                self.tree = ttk.Treeview(self.tree_frame, style="mystyle.Treeview", columns=list(self.dataframe.columns), height=self.dataframe.shape[0], show='tree')

            self.tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
            
            self.tree.bind("<Double-Button-1>", self.add_quick_filter_event)
            self.tree.bind("<Button-3>", self.do_popup)

            if self.scrollbar_bool:
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

    def add_quick_filter_event(self, event):
        iid = self.tree.identify_row(event.y)
        try:
            if iid:
                self.tree.selection_set(iid)
                values = self.tree.item(iid, 'values')
                self.add_quick_filter(values[0], values[1])
        finally:
            pass

    def do_popup(self, event):
        iid = self.tree.identify_row(event.y)
        try:
            if iid:
                self.tree.selection_set(iid)
                popup = Popup(self, self.tree.item(iid, 'values'))
                popup.tk_popup(event.x_root, event.y_root)

        finally:
            popup.grab_release()
    
    def add_quick_filter(self, column, value):
        if self.purpose == "balances":
            self.app.add_quick_filter("Account", column)
        else:
            self.app.add_quick_filter(column, value)

'''
To show the small rectangle saying "Filter With"
'''
class Popup(tk.Menu):
    def __init__(self, master, kvp):
        tk.Menu.__init__(self, master.root, tearoff=0)
        self.add_command(label="Filter with", command=lambda: master.add_quick_filter(kvp[0], kvp[1]))
        self.bind("<FocusOut>", lambda x: self.destroy())

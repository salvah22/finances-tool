'''
tk toplevel window wrapping both a treeview and a matplotlib figure
'''

from typing import List

from tkinter import ttk
import tkinter as tk
import pandas as pd

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .tree import Treewindow

from utils.tk_inter import treeview_sort_column

class Groupwindow(Treewindow):
    '''
    tk toplevel window wrapping both a treeview and a matplotlib figure
    '''

    def __init__(self, app, icon=None):
        super().__init__(app, icon)
        self.tree_records = 15
        self.canvas_frame = None
        self.combined_frame = None
        self.footer_frame = None
        self.tree_frame = None
        self.tree = None
        self.position = None
        self.fig = None
        self.initiated = None
        self.headings = None
        self.root = None

    def update(self, dataframe: pd.DataFrame, fig, title:str=None, position:list=None, headings=True):
        self.initiated = True
        self.headings = headings
        self.set_data_frame(dataframe)
        self.position = position
        self.fig = fig
        self.updateTk(title)

    def updateTk(self,title):
        
        ### init the toplevel tk element
        if self.root is None or not self.root.winfo_exists():
            self.root = tk.Toplevel(self.app.main.root)
            # self.root.group(self.app.main.root)
            self.root.bind('<Escape>', lambda e: self._quit())
            if self.icon is not None:
                self.root.tk.call('wm', 'iconphoto', self.root._w, self.icon)
        if title is not None:
            self.title = title
            self.root.wm_title(title)

        # if the frame exists, detroy it
        if self.combined_frame is not None:
            self.combined_frame.destroy()

        # look
        width = 130 * self.dataframe.shape[1]
        height = self.tree_records * 30 + 50
        
        ### scroll bar for dataframes with more than 15 rows
        if self.dataframe.shape[0] > self.tree_records:
            scrollbar_bool=True
            width += 15 # for the scrollbar
            # height = 450 + 25
        else:
            scrollbar_bool=False
            # height = 30 * self.dataframe.shape[0] + 25 # 30 per row + 25 margin

        if self.position is not None:
            self.root.geometry(f'{width + 500}x{height+60}+{self.position[0]}+{self.position[1]}') # (width, height, x, y)
        else:
            self.root.geometry(f'{width + 500}x{height+60}')
        
        if self.tree_frame is not None:
            self.tree_frame.destroy()

        # combined frame
        self.combined_frame = tk.Frame(self.root, borderwidth=0, width=width+500, height=height)
        self.combined_frame.pack(side=tk.TOP, fill=tk.Y, expand=1)

        # tree frame
        self.tree_frame = tk.Frame(self.combined_frame, borderwidth=0)
        self.tree_frame.pack(side=tk.LEFT, fill=tk.Y, expand=1)

        # treeview
        if self.headings:
            self.tree = ttk.Treeview(self.tree_frame, style="mystyle.Treeview", columns=list(self.dataframe.columns), height=self.tree_records, show='headings')
        else:
            self.tree = ttk.Treeview(self.tree_frame, style="mystyle.Treeview", columns=list(self.dataframe.columns), height=self.tree_records, show='tree')

        self.tree.pack(side=tk.LEFT, fill=tk.Y)

        if scrollbar_bool:
            scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
            self.tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        for colname in (self.dataframe.columns):
            self.tree.column(colname, anchor='center', width=130, stretch=tk.NO)
            if self.headings:
                self.tree.heading(colname, text=colname, anchor='center', command=lambda _col=colname: treeview_sort_column(self.tree, _col, False))

        self.updateTreeRecords()

        ### plt
        self.canvas_frame = tk.Frame(self.combined_frame, borderwidth=0)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.X, expand=1)
        canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)  # A tk.DrawingArea.
        
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        if self.footer_frame is not None:
            self.footer_frame.destroy()

        ### Footer buttons frame
        self.footer_frame = tk.Frame(
            self.root,
            highlightbackground="blue", 
            highlightthickness=0
        )
        self.footer_frame.pack(side=tk.TOP, expand=1, fill=tk.BOTH)
        tk.Label(self.footer_frame, 
            text="Total: "+str(self.dataframe.iloc[:,1].sum()), 
            font=self.app.config['fonts']['f10']
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        frame1 = tk.Frame(
            self.footer_frame,
            highlightbackground="blue", 
            highlightthickness=0
        )
        frame1.place(x=430, y=-5, height=100)
        tk.Label(frame1, text="Group by: ", font=self.app.config['fonts']['f10']).grid(row=0, column=1, pady=5, sticky="e")
        self.category_button = ttk.Button(frame1, text='Category', command=lambda: self.app.update_groupby_win('Category'), style='Accent.TButton')
        self.category_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.note_button = ttk.Button(frame1, text='Note', command=lambda: self.app.update_groupby_win('Note'), style='Accent.TButton')
        self.note_button.grid(row=0, column=3, pady=5, sticky="e")


    def updateTreeRecords(self, columns: List[str] = []):
        self.tree.delete(*self.tree.get_children()) # delete data for next rendering)

        if columns == []:
            columns = list(self.dataframe.columns)
        
        for row in self.dataframe[columns].to_numpy():
            self.tree.insert("", 0, values=row.tolist())




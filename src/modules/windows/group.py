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

    def __init__(self, app, icon=None, purpose=None):
        super().__init__(app, icon, purpose)
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

    def update(self, fig, dataframe: pd.DataFrame, title:str=None, position:list=None, headings=True):
        super().update(dataframe, title, position, headings)
        self.tree_records = 15
        super().update_tk()
        self.fig = fig
        self.updateTk()

    def updateTk(self):

        # if the frame exists, detroy it
        if self.combined_frame is not None:
            self.combined_frame.destroy()

        # combined frame
        self.combined_frame = tk.Frame(self.root, borderwidth=0, width=self.width+500, height=self.height)
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

        if self.scrollbar_bool:
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




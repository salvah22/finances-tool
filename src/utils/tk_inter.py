import pandas as pd
import tkinter as tk
from tkinter import ttk
from typing import List


def popup_tree_window(dataframe: pd.DataFrame, title: str, position: list = None, icon = None):

    # init
    win = tk.Toplevel()
    win.wm_title(title)

    if icon:
        win.tk.call('wm', 'iconphoto', win._w, icon)

    # look
    width = 130 * dataframe.shape[1]
    
    if dataframe.shape[0] > 15:
        scrollbar_bool=True
        width += 15
        height = 450 + 25
    else:
        scrollbar_bool=False
        height = 30 * dataframe.shape[0] + 25

    if position:
        win.geometry(f'{width}x{height}+{position[0]}+{position[1]}') # (width, height, x, y)
    else:
        win.geometry(f'{width}x{height}')

    # treeview
    tree = ttk.Treeview(win, style="mystyle.Treeview", columns=list(dataframe.columns), height=dataframe.shape[0], show='headings')
    tree.pack(side=tk.LEFT, expand=True)

    if scrollbar_bool:
        scrollbar = ttk.Scrollbar(win, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)

    for colname in (dataframe.columns):
        tree.column(colname, anchor='center', width=130, stretch=tk.NO)
        tree.heading(colname, text=colname, anchor='center', command=lambda _col=colname: treeview_sort_column(tree, _col, False))

    update_tree_records(dataframe, tree)


def update_tree_structure(tree: ttk.Treeview, columns: List[str] = []):

    # clear it 

    tree.delete(*tree.get_children()) # delete data for next rendering)

    tree["columns"] = ()

    for col in tree['columns']:
        tree.heading(col, text='')

    # populate it

    tree['columns'] = columns

    for colname in columns:
        if colname == 'ID':
            width = 60
        else:
            width = 130
        tree.column(colname, anchor='center', width=width, stretch=tk.NO)
        tree.heading(colname, text=colname, anchor='center', command=lambda _col=colname: treeview_sort_column(tree, _col, False))


def update_tree_records(dataframe: pd.DataFrame, tree: ttk.Treeview, columns: List[str] = []):
    tree.delete(*tree.get_children()) # delete data for next rendering)

    if columns == []:
        columns = list(dataframe.columns)
    
    for row in dataframe[columns].to_numpy():
        tree.insert("", 0, values=row.tolist())


def treeview_sort_column(tv, col, reverse):
    l = [(tv.set(k, col), k) for k in tv.get_children()]
    if col in ['ID', 'EUR', 'USD',' GBP', 'AccountBalance']:
        l.sort(reverse=reverse, key=lambda tup: float(tup[0]))
    else:
        l.sort(reverse=reverse)
    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)

    # reverse sort next time
    tv.heading(col, command=lambda _col=col: treeview_sort_column(tv, _col, not reverse))

import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import List


def popup_tree_window(dataframe: pd.DataFrame, title: str, geom: list = None, treeview_height: int = 10, icon = None):
    win = tk.Toplevel()
    win.wm_title(title)
    if geom:
        win.geometry(f'{geom[0]}x{geom[1]}+{geom[2]}+{geom[3]}') # (width, height, x, y)
    if icon:
        win.tk.call('wm', 'iconphoto', win._w, icon)
    tree = ttk.Treeview(win, style="mystyle.Treeview", height=treeview_height)
    tree.pack(expand=True)
    update_tree(dataframe, tree)


def update_tree(dataframe: pd.DataFrame, tree: ttk.Treeview, columns: List[str] = []):
    tree.delete(*tree.get_children()) # delete data for next rendering
    if columns == []:
        columns = list(dataframe.columns)
    tree['columns'] = columns
    tree.column('#0', anchor='center', width=60, stretch=tk.NO)
    tree.heading('#0', text='', anchor='center', command=lambda: treeview_sort_column(tree, '#0', False))
    for i in columns:
        tree.column(i, anchor='center', width=130, stretch=tk.NO)
        tree.heading(i, text=i, anchor='center', command=lambda: treeview_sort_column(tree, i, False))
    for _, row in dataframe[columns].iterrows():
        tree.insert("", 0, text=row.name, values=list(row))


def treeview_sort_column(tv, col, reverse):
    l = [(tv.item(k)["text"], k) for k in tv.get_children()] #Display column #0 cannot be set
    l.sort(key=lambda t: t[0], reverse=reverse)

    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)

    tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))

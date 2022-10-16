import tkinter as tk
from tkinter import ttk


def popup_tree_window(dataframe):
    win = tk.Toplevel()
    win.wm_title("Data grouped by categories")

    tree = ttk.Treeview(win, style="mystyle.Treeview")
    tree.pack(expand=True)
    update_tree(dataframe, tree)


def update_tree(df, tree, columns=[]):
    tree.delete(*tree.get_children()) # delete data for next rendering
    if columns == []:
        columns = list(df.columns)
    tree['columns'] = columns
    tree.column('#0', anchor='center', width=60, stretch=tk.NO)
    tree.heading('#0', text='', anchor='center', command=lambda: treeview_sort_column(tree, '#0', False))
    for i in columns:
        tree.column(i, anchor='center', width=130, stretch=tk.NO)
        tree.heading(i, text=i, anchor='center', command=lambda: treeview_sort_column(tree, i, False))
    for _, row in df[columns].iterrows():
        tree.insert("", 0, text=row.name, values=list(row))


def treeview_sort_column(tv, col, reverse):
    l = [(tv.item(k)["text"], k) for k in tv.get_children()] #Display column #0 cannot be set
    l.sort(key=lambda t: t[0], reverse=reverse)

    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)

    tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))

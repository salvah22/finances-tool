'''
Main frontend window
'''
from tkinter import ttk
import tkinter as tk
import pandas as pd
import numpy as np

from typing import List

from .window import Window

from utils.tk_inter import treeview_sort_column, update_tree_structure

class Mainwindow(Window):
    '''
    Main frontend window
    '''

    def __init__(self, parent, config, icon_path, theme=None):
        
        ### main definitions
        self.app = parent
        self.config = config
        self.tree_main_records = 15
        self.frame_tree_height = int(30 * self.tree_main_records)
        self.frame_tree_width = int(60 + (len(self.config['display_columns']) - 1) * 130) # 60 idx + 130 p/column
        self.root = self.app.root
        self.root.title('Money Mgr.')
        self.root.bind('<Escape>', lambda e: self._quit())
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.main_width = self.frame_tree_width + 10 # + 10 for margins ~ 1000
        self.main_height = self.frame_tree_height + 110 # 450 treeview + 110 other elements ~ 650
        self.main_x = int((self.screen_width)/2 - (self.main_width)/2) # screen_width - app_width
        self.main_y = int((self.screen_height)/2 - (self.main_height)/2)
        self.root.geometry(f'{self.main_width}x{self.main_height}+{self.main_x}+{self.main_y}')
        self.root.resizable(False, False)
        self.icon = tk.PhotoImage(file=icon_path)
        self.root.tk.call('wm', 'iconphoto', self.root._w, self.icon)
        ### menu bar
        self.main_menubar = tk.Menu(self.root)
        # file cascade menu
        self.main_filemenu = tk.Menu(self.main_menubar, tearoff=0)
        self.main_filemenu.add_command(label='Exit', command=self._quit)
        self.main_menubar.add_cascade(label='File', menu=self.main_filemenu)
        # view cascade menu
        self.main_viewmenu = tk.Menu(self.main_menubar, tearoff=0)
        self.main_viewmenu.add_command(label='Balances', command=lambda: self.showWindow('Balances'))
        self.main_viewmenu.add_command(label='Group By', command=lambda: self.showWindow('Group By'))
        self.main_viewmenu.add_command(label='Filters', command=lambda: self.showWindow('Filters'))
        self.main_viewmenu.add_command(label='Configuration', command=lambda: self.showWindow('Filters'))
        self.main_menubar.add_cascade(label='View', menu=self.main_viewmenu)
        # set menubar when ready
        self.root.config(menu=self.main_menubar)
        ### style
        self.style = ttk.Style()
        if theme:
            self.root.tk.call('source', 'src/configs/'+theme+'.tcl')
            self.style.theme_use(theme) # for all ttk elems
        self.style_bg_col = str(self.style.lookup('TFrame', 'background'))
        
        self.style.configure('mystyle.Treeview', rowheight=30) # default: 20
        self.style.configure('mystyle.Treeview', font=self.config['fonts']['f08'])
        self.style.configure('mystyle.Treeview.Heading', font=self.config['fonts']['f10'])
        self.style.layout('mystyle.Treeview', [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])
        self.frame_header = tk.Frame(self.root, borderwidth=0)
        self.frame_header.pack(expand=True)
        ### Period frames
        self.button_last = ttk.Button(self.frame_header, text='Today', style='Accent.TButton', command=lambda: self.app.move_time_window('today'))
        self.button_last.grid(row=0, column=0, padx=(5,5), pady=5, sticky='nsew') #.pack(side=tk.LEFT, fill=tk.Y)
        self.button_today = ttk.Button(self.frame_header, text='First', command=lambda: self.app.move_time_window('last') )
        self.button_today.grid(row=0, column=1, padx=(0,5), pady=5, sticky='nsew')
        self.frame_period = tk.Frame(self.frame_header, borderwidth=0)
        self.frame_period.grid(row=0, column=2, padx=(0,5), pady=5, sticky='nsew', columnspan=1) # .pack(expand=True, side=tk.LEFT, fill=tk.Y)

        self.frame_period_alter = tk.Frame(self.frame_period, borderwidth=0)
        self.frame_period_alter.pack( side=tk.BOTTOM, fill=tk.Y)
        self.start_date = tk.StringVar()
        self.end_date = tk.StringVar()
        c = 0
        self.button_backwards = ttk.Button(self.frame_period_alter, text='◄', command=lambda: self.app.move_time_window('backwards'))
        self.button_backwards.grid(row=0, column=c, sticky='w', padx=5) 
        c += 1
        self.entry_date_start = ttk.Entry(self.frame_period_alter, textvariable=self.start_date,justify='center', width=10)
        self.entry_date_start.grid(row=0, column=1, sticky='nsew', padx=5)
        self.entry_date_start.bind('<Return>', lambda event: self.app.on_entry_change('start'))
        c += 1
        self.entry_date_end = ttk.Entry(self.frame_period_alter, textvariable=self.end_date, justify='center', width=10)
        self.entry_date_end.grid(row=0, column=2, sticky='nsew', padx=5) 
        self.entry_date_end.bind('<Return>', lambda event: self.app.on_entry_change('end'))
        c += 1
        self.button_onwards = ttk.Button(self.frame_period_alter, text='►', command=lambda: self.app.move_time_window('onwards'))
        self.button_onwards.grid(row=0, column=3, sticky='w', padx=5) 

        self.frame_DMY = tk.Frame(self.frame_period, borderwidth=0)
        self.frame_DMY.pack(expand=True, side=tk.BOTTOM, fill=tk.Y)

        self.period_days = tk.StringVar()
        self.period_days.set('0')
        self.period_months = tk.StringVar()
        self.period_months.set('1')
        self.period_years = tk.StringVar()
        self.period_years.set('0')

        c = 0
        tk.Label(self.frame_DMY, text='Days', font=self.config['fonts']['f10']).grid(row=0, column=c, sticky='nsew', padx=5)
        c += 1
        self.spinbox_period_days = ttk.Spinbox(self.frame_DMY, textvariable=self.period_days, from_=0, to=31, increment=1, width=3)
        self.spinbox_period_days.grid(row=0, column=c, sticky='nsew', padx=(0,10))
        c += 1
        tk.Label(self.frame_DMY, text='Months', font=self.config['fonts']['f10']).grid(row=0, column=c, sticky='nsew', padx=5)
        c += 1
        self.spinbox_period_months = ttk.Spinbox(self.frame_DMY, textvariable=self.period_months, from_=0, to=11, increment=1, width=3)
        self.spinbox_period_months.grid(row=0, column=c, sticky='nsew', padx=(0,10))
        c += 1
        tk.Label(self.frame_DMY, text='Years', font=self.config['fonts']['f10']).grid(row=0, column=c, sticky='nsew', padx=5)
        c += 1
        self.spinbox_period_years = ttk.Spinbox(self.frame_DMY, textvariable=self.period_years, from_=0, to=99, increment=1, width=3)
        self.spinbox_period_years.grid(row=0, column=c, sticky='nsew')

        ### Button Group In/Out (EXPENSE/INCOME/TRANSFER/ALL)
        self.frame_in_out = tk.Frame(self.frame_header, borderwidth=0)
        self.frame_in_out.grid(row=0, column=3, padx=(0,5), pady=5, sticky='nsew', columnspan=2)#.pack(expand=True, side=tk.LEFT, fill=tk.BOTH)
        self.frame_in_out.columnconfigure(tuple(range(2)), weight=1)
        self.frame_in_out.rowconfigure(tuple(range(2)), weight=1)
        self.button_income = ttk.Button(self.frame_in_out, text='Income',
                                                  command=lambda: self.app.update_subset('inout_Income'))
        self.button_income.grid(row=0, column=0, sticky='nswe', padx=(0,2.5), pady=(0,2.5))
        self.button_expenses = ttk.Button(self.frame_in_out, text='Expenses',
                                                  command=lambda: self.app.update_subset('inout_Expenses'))
        self.button_expenses.grid(row=1, column=0, sticky='nswe', padx=(0,2.5), pady=(2.5,0))
        self.button_transfers = ttk.Button(self.frame_in_out, text='Transfer',
                                                  command=lambda: self.app.update_subset('inout_Transfer'))
        self.button_transfers.grid(row=0, column=1, sticky='nswe', padx=(2.5,0), pady=(0,2.5))
        self.button_all = ttk.Button(self.frame_in_out, text='All',
                                                  command=lambda: self.app.update_subset('inout_All'))
        self.button_all.grid(row=1, column=1, sticky='nswe', padx=(2.5,0), pady=(2.5,0))
        ### GROUPING
        self.frame_groups = tk.Frame(self.frame_header, padx=5, pady=5) # , highlightbackground='black', highlightthickness=2
        self.frame_groups.grid(row=0, column=5, padx=(0,5), pady=5, sticky='nsew')#.pack(expand=True)
        ttk.Label(self.frame_groups, text='Grouping').grid(row=0, column=0, sticky='nsew') 
        self.group = tk.StringVar()
        self.group_opt_menu = ttk.OptionMenu(self.frame_groups, self.group,'None', 'None', 'Day', 'Month', 'Year', command=self.app.group_change)
        self.group_opt_menu.grid(row=1, column=0, sticky='nsew')
        self.group_category = tk.BooleanVar(value=False)
        self.checkbox_category = ttk.Checkbutton(self.frame_groups, text='category', variable=self.group_category, onvalue=True, offvalue=False, command=self.app.group_opts_change)
        self.checkbox_category.grid(row=2, column=0, sticky='nsew')  #.pack(side=tk.TOP, expand=True, padx=(0, 5))
        ### MAIN BIG TREE
        self.frame_tree_container = tk.Frame(self.root)
        self.frame_tree_container.pack(expand=True, side=tk.TOP)
        self.frame_tree = tk.Frame(self.frame_tree_container, width=self.frame_tree_width, height=self.frame_tree_height) # -20 for the scrollbar
        self.frame_tree.grid(row=0, column=0)
        # By default, Tkinter Frame fits to its children and thus its width and height depends on its children.
        # You can override this behavior and force a specific width and height to the frame.
        self.frame_tree.pack_propagate(0)
        self.tree_main = ttk.Treeview(self.frame_tree, style='mystyle.Treeview', height=self.tree_main_records, columns=self.config['display_columns'], show='headings') # originally height=10
        self.tree_main.bind('<Double-1>', self.app.on_double_click)
        self.tree_main.pack(side=tk.LEFT) # .pack(side=tk.LEFT)
        update_tree_structure(self.tree_main, self.config['display_columns'])
        self.tree_main_scrollbar = ttk.Scrollbar(self.frame_tree_container, orient=tk.VERTICAL, command=self.tree_main.yview)
        self.tree_main.configure(yscroll=self.tree_main_scrollbar.set)
        self.tree_main_scrollbar.grid(row=0, column=1, sticky='ns') # .pack(side=tk.LEFT, fill=tk.Y)

        # the period spinbox variables need to be defined after tree_main exists
        self.period_days.trace('w', lambda *_: self.app.on_entry_change('period'))
        self.period_months.trace('w', lambda *_: self.app.on_entry_change('period'))
        self.period_years.trace('w', lambda *_: self.app.on_entry_change('period'))

    def open_filters_win(self):
        self.app.filters_win.show(self.app.filters_list)


    def showWindow(self, which_one):
        if which_one == "Balances":
            if self.app.balances_win.root is None or not self.app.balances_win.root.winfo_exists():
                self.app.show_balances()
            self.raise_above_all(self.app.balances_win.root)
        elif which_one == "Group By":
            if self.app.groupby_win.root is None or not self.app.groupby_win.root.winfo_exists():
                self.app.update_groupby_win('Category')
            self.raise_above_all(self.app.groupby_win.root)
        elif which_one == "Filters":
            if self.app.filters_win.root is None or not self.app.filters_win.root.winfo_exists():
                self.open_filters_win()
            self.raise_above_all(self.app.filters_win.root)
        elif which_one == "Configuration":
            pass
    
    def raise_above_all(self, window):
        window.lift()
        window.attributes('-topmost', True)
        window.attributes('-topmost', False)
        window.attributes('-topmost', 1)
        window.attributes('-topmost', 0)
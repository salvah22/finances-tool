"""
Money Manager software developed by Salvador Hernández, September 2022

"""

import re
import pandas as pd

import datetime
from dateutil.relativedelta import relativedelta

from utils.time import parse_period
from utils.data import data_loader, data_prepare
from utils.tk_inter import update_tree, popup_tree_window

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.messagebox import showinfo

class App:
    """
    https://stackoverflow.com/questions/3794268/command-for-clicking-on-the-items-of-a-tkinter-treeview-widget
    """
    today = datetime.datetime.today()
    todays_month = datetime.datetime(today.year, today.month, 1)

    @property
    def period(self):
        return self._period

    @period.setter
    def period(self, value):
        self._period = value
        self.period_update_callback()

    def period_update_callback(self):
        self.tk_elems['period_days'].set(str(self.period.days) + " days")
        self.tk_elems['period_months'].set(str(self.period.months) + " months")
        self.tk_elems['period_years'].set(str(self.period.years) + " years")

    def __init__(self, data_path='', tk=True):
        ### parameters ###
        self.params = {'fonts': {'f08': 'sans-serif, 8', 'f10': 'sans-serif, 10', 'f12': 'sans-serif, 12'}, 'colors': {'green':'#91BF2C', 'blue':'#00ABFF', 'red':'#FF614F'}}
        # dates in ISO format: '2022-06-01T00:00:00'
        self._period = relativedelta(months=1)
        self.in_out = 'Expenses' # 'Income', 'Expenses', 'Transfer in', 'Transfer out', 'All'
        self.dates = {'initial': self.todays_month - self._period, 'final': self.todays_month}
        ### data ###
        self.data_path = data_path
        self.df = pd.DataFrame()
        self.df_subset = pd.DataFrame()
        self.load_df()
        print('--- df loaded and prepared ---')
        ### tk inter gui related stuff ###
        self.tk_elems = {}
        if tk:
            self.init_tk()
            self.period_update_callback()
            self.move_time_window('onwards') # wraps update_subset
            self.tk_elems['main_app'].mainloop()

    def load_df(self):
        if self.data_path != '':
            self.df = data_loader(self.data_path) # checks for the extensions and employs the proper load function
        else:
            self.df = pd.read_excel('/home/salva/personal/budgeting/Mny.Mgr.2022-08-31.xlsx').iloc[::-1]  # inverse order for show
        # prepare/preprocess the dataframe:
        self.df = data_prepare(self.df)
        # write the dates of the first and last record
        self.dates['first_record'] = datetime.datetime.fromisoformat(self.df['Day'].iloc[0])
        ld = self.df['Day'].iloc[-1].split('-')
        self.dates['last_record'] = datetime.datetime.fromisoformat('-'.join([ld[0], ld[1], str(int(ld[2]) + 1)]))
        # we don't want transfer out transactions
        self.df = self.df[self.df['Income/Expenses'] != 'Transfer out']
        self.df_subset = pd.DataFrame()

    def init_tk(self):
        self.tk_elems['main_app'] = tk.Tk()
        self.tk_elems['main_app'].title('Money Mgr.')
        self.tk_elems['main_app'].geometry('850x500') # 130 per column (6 cols) + 60 idx + 10 margins
        self.tk_elems['style'] = ttk.Style()
        self.tk_elems['style'].configure("mystyle.Treeview", font=self.params['fonts']['f08'])
        self.tk_elems['style'].configure("mystyle.Treeview.Heading", font=self.params['fonts']['f10'])
        self.tk_elems['style'].layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])
        self.tk_elems['frame_header'] = tk.Frame(self.tk_elems['main_app'])
        self.tk_elems['frame_header'].pack(expand=True)
        self.tk_elems['frame_tree'] = tk.Frame(self.tk_elems['main_app'], padx=5, pady=5)
        self.tk_elems['frame_tree'].pack(expand=True)
        self.tk_elems['date_initial'] = tk.StringVar()
        self.tk_elems['date_final'] = tk.StringVar()
        self.tk_elems['period_years'] = tk.StringVar()
        self.tk_elems['period_months'] = tk.StringVar()
        self.tk_elems['period_days'] = tk.StringVar()
        self.tk_elems['button_today'] = tk.Button(self.tk_elems['frame_header'], text='Today', width=2, command=lambda: self.move_time_window('today'), font=self.params['fonts']['f12'], bg=self.params['colors']['green'])
        self.tk_elems['button_today'].pack(side=tk.LEFT)
        self.tk_elems['button_backwards'] = tk.Button(self.tk_elems['frame_header'], text='<', width=2, command=lambda: self.move_time_window('backwards'), font=self.params['fonts']['f12'])
        self.tk_elems['button_backwards'].pack(side=tk.LEFT)
        ### DROPDOWN: DAILY/WEEKLY/MONTHLY/YEARLY
        self.tk_elems['entry_date_initial'] = tk.Entry(self.tk_elems['frame_header'], textvariable=self.tk_elems['date_initial'], font=self.params['fonts']['f12'], width=10)
        self.tk_elems['entry_date_initial'].pack(side=tk.LEFT)
        self.tk_elems['entry_date_initial'].bind('<Return>', lambda event: self.on_entry_change('initial'))
        #tk.Label(self.tk_elems['frame_header'], text=" | ", font=self.params['fonts']['f12']).pack(side=tk.LEFT)
        self.tk_elems['entry_date_final'] = tk.Entry(self.tk_elems['frame_header'], textvariable=self.tk_elems['date_final'], font=self.params['fonts']['f12'], width=10)
        self.tk_elems['entry_date_final'].pack(side=tk.LEFT)
        self.tk_elems['entry_date_final'].bind('<Return>', lambda event: self.on_entry_change('final'))
        self.tk_elems['button_onwards'] = tk.Button(self.tk_elems['frame_header'], text='>', width=2, command=lambda: self.move_time_window('onwards'), font=self.params['fonts']['f12'])
        self.tk_elems['button_onwards'].pack(side=tk.LEFT)
        self.tk_elems['frame_period'] = tk.Frame(self.tk_elems['frame_header'])
        self.tk_elems['frame_period'].pack(expand=True, side=tk.LEFT)
        self.tk_elems['entry_period_years'] = tk.Entry(self.tk_elems['frame_period'], textvariable=self.tk_elems['period_years'], font=self.params['fonts']['f10'], width=8)
        self.tk_elems['entry_period_years'].pack(side=tk.BOTTOM)
        self.tk_elems['entry_period_years'].bind('<Return>', lambda event: self.on_entry_change('period'))
        self.tk_elems['entry_period_months'] = tk.Entry(self.tk_elems['frame_period'], textvariable=self.tk_elems['period_months'], font=self.params['fonts']['f10'], width=8)
        self.tk_elems['entry_period_months'].pack(side=tk.BOTTOM)
        self.tk_elems['entry_period_months'].bind('<Return>', lambda event: self.on_entry_change('period'))
        self.tk_elems['entry_period_days'] = tk.Entry(self.tk_elems['frame_period'], textvariable=self.tk_elems['period_days'], font=self.params['fonts']['f10'], width=8)
        self.tk_elems['entry_period_days'].pack(side=tk.BOTTOM)
        self.tk_elems['entry_period_days'].bind('<Return>', lambda event: self.on_entry_change('period'))
        self.tk_elems['frame_in_out'] = tk.Frame(self.tk_elems['frame_header'])
        self.tk_elems['frame_in_out'].pack(expand=True, side=tk.LEFT)
        self.tk_elems['button_income'] = tk.Button(self.tk_elems['frame_in_out'], text='Income', width=4, height=1,
                                                  command=lambda: self.update_subset('Income'),
                                                  font=self.params['fonts']['f10'], bg=self.params['colors']['blue'])
        self.tk_elems['button_income'].grid(row=0, column=0)
        self.tk_elems['button_expenses'] = tk.Button(self.tk_elems['frame_in_out'], text='Expenses', width=4, height=1,
                                                  command=lambda: self.update_subset('Expenses'),
                                                  font=self.params['fonts']['f10'], bg=self.params['colors']['red'])
        self.tk_elems['button_expenses'].grid(row=1, column=0)
        self.tk_elems['button_transfers'] = tk.Button(self.tk_elems['frame_in_out'], text='Transfer', width=4, height=1,
                                                  command=lambda: self.update_subset('Transfer'),
                                                  font=self.params['fonts']['f10'])
        self.tk_elems['button_transfers'].grid(row=0, column=1)
        self.tk_elems['button_all'] = tk.Button(self.tk_elems['frame_in_out'], text='All', width=4, height=1,
                                                  command=lambda: self.update_subset('All'),
                                                  font=self.params['fonts']['f10'])
        self.tk_elems['button_all'].grid(row=1, column=1)
        ### DROPDOWN: EXPENSE/INCOME/TRANSFER
        self.tk_elems['main_tree'] = ttk.Treeview(self.tk_elems['frame_tree'], style="mystyle.Treeview")
        self.tk_elems['main_tree'].pack(expand=True)
        self.tk_elems['main_tree'].bind('<Double-1>', self.on_double_click)
        self.tk_elems['frame_footer'] = tk.Frame(self.tk_elems['main_app'])
        self.tk_elems['frame_footer'].pack(expand=True)
        self.tk_elems['button_groupby_categories'] = tk.Button(self.tk_elems['frame_footer'], text='Groupby categories', width=12, command=self.groupby_categories, font=self.params['fonts']['f10'], bg=self.params['colors']['green'])
        self.tk_elems['button_groupby_categories'].pack(side=tk.LEFT)

    def move_time_window(self, direction=''):
        if direction == 'today':
            self.period = relativedelta(months=1)
            self.dates['initial'] = self.todays_month - self.period
            self.dates['final'] = self.todays_month
            if self.dates['final'] + self.period <= self.dates['last_record']:
                self.dates['initial'] = self.dates['initial'] + self.period
                self.dates['final'] = self.dates['final'] + self.period
            else:
                self.dates['final'] = self.dates['last_record']
                self.dates['initial'] = self.dates['last_record'] - self.period
        elif direction == 'backwards':
            # assert we don't go outside timely boundaries
            if self.dates['initial'] - self.period >= self.dates['first_record']:
                self.dates['initial'] = self.dates['initial'] - self.period
                self.dates['final'] = self.dates['final'] - self.period
            else:
                self.dates['initial'] = self.dates['first_record']
                self.dates['final'] = self.dates['first_record'] + self.period
        elif direction == 'onwards':
            # assert we don't go outside timely boundaries
            if self.dates['final'] + self.period <= self.dates['last_record']:
                self.dates['initial'] = self.dates['initial'] + self.period
                self.dates['final'] = self.dates['final'] + self.period
            else:
                self.dates['final'] = self.dates['last_record']
                self.dates['initial'] = self.dates['last_record'] - self.period
        self.tk_elems['date_initial'].set(self.dates['initial'].strftime("%Y-%m-%d"))
        self.tk_elems['date_final'].set(self.dates['final'].strftime("%Y-%m-%d"))
        self.update_subset()

    def update_subset(self, instruction=''):
        if instruction != '':
            self.in_out = instruction
        # timely
        if self.dates['initial'] and self.dates['final']:
            self.df_subset = self.df[(self.dates['initial'] <= self.df['datetime']) & (self.df['datetime'] <= self.dates['final'])]
        self.tk_elems['date_initial'].set(self.dates['initial'].strftime("%Y-%m-%d"))
        self.tk_elems['date_final'].set(self.dates['final'].strftime("%Y-%m-%d"))
        # in/out
        if self.in_out == 'All':
            pass
        elif self.in_out in ['Income', 'Expenses']:
            self.df_subset = self.df_subset[self.df_subset['Income/Expenses'] == self.in_out]
        elif self.in_out == 'Transfer':
            self.df_subset = self.df_subset[self.df_subset['Income/Expenses'] == 'Transfer in']
        update_tree(self.df_subset, self.tk_elems['main_tree'])

    def on_double_click(self, event):
        #idx = self.tk_elems['main_tree'].selection()[0]
        tree_idx = self.tk_elems['main_tree'].identify('item', event.x, event.y)
        df_idx = self.tk_elems['main_tree'].item(tree_idx,'text')
        #print('you clicked on dataframes idx=', df_idx)
        showinfo("Transaction Details", str(self.df_subset.loc[df_idx]))

    def on_entry_change(self, instruction):
        if instruction == 'initial':
            self.dates['initial'] = datetime.datetime.fromisoformat(self.tk_elems['date_initial'].get())
        elif instruction == 'final':
            self.dates['final'] = datetime.datetime.fromisoformat(self.tk_elems['date_final'].get())
        elif instruction == 'period':
            years = int(self.tk_elems['period_years'].get().split(" ")[0])
            months = int(self.tk_elems['period_months'].get().split(" ")[0])
            days = int(self.tk_elems['period_days'].get().split(" ")[0])
            self.period = relativedelta(years=years, months=months, days=days)
            self.dates['final'] = self.dates['initial'] + self.period

        if instruction in ['final', 'initial']:
            self.period = parse_period(self.dates['initial'], self.dates['final'])
            # TODO: WRITE THIS PERIOD NOW THAT IS WORKING REALLY COOL TO A DROPDOWN / ENTRY

        self.update_subset()

    def groupby_categories(self):
        grouped = self.df_subset.groupby(["Category"])['EUR'].sum().reset_index()
        groupedsorted = grouped.sort_values(by='EUR', ascending=True)
        groupedsortedrounded = groupedsorted.round(0)
        popup_tree_window(groupedsortedrounded)

if __name__ == '__main__':
    app = App()
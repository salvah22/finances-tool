"""
Money Manager software developed by Salvador Hernández
Created: September 2022
Changed: April 2023
"""

# standard python libraries

from tkinter.messagebox import showinfo

import sys
import yaml
from os import path
import datetime
from dateutil.relativedelta import relativedelta

from tkinter import ttk, PhotoImage, Tk

# extra libraries
import pandas as pd
import matplotlib.pyplot as plt

# own modules
from modules.mainwindow import Mainwindow
from modules.groupwindow import Groupwindow
from modules.treewindow import Treewindow
from modules.filterswin import Filterswindow

# own utils
from utils.time import parse_period
from utils.data import data_loader, data_prepare, get_last_balance_per_account, year_month_from_iso, year_from_iso
from utils.graph import pie_chart
from utils.tk_inter import update_tree_records, update_tree_structure

class App:
    """
    https://stackoverflow.com/questions/3794268/command-for-clicking-on-the-items-of-a-tkinter-treeview-widget
    """
    today = datetime.datetime.today()
    todays_month = datetime.datetime(today.year, today.month, 1)

    # constructor, loads configs, data, and bootstrap the tk inter
    def __init__(self, data_path:str=None, config_path:str=None, tk:bool=True):
        self.initiated = False
        ### parameters ###
        # load config file
        if config_path and path.exists(config_path):
            pass
        elif path.exists('src'):
            config_path = 'src/configs/app.yml'
        else:
            print('cannot locate app.yml config file')
        with open(config_path, 'r') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
        # initiate important variables
        self.period = relativedelta(months=1)
        self.group = 'None'
        self.group_opts = []
        self.in_out = self.config['default_subset']
        self.dates = {'start': self.todays_month - self.period, 'end': self.todays_month} # dates in ISO format: '2022-06-01T00:00:00'
        ### load data ###
        # locate input data to load as dataframe
        if data_path:
            if path.exists(data_path):
                self.data_path = data_path
            else:
                print('file path supplied via data_path arg is not valid')
        elif len(sys.argv) > 1:
            if path.exists(sys.argv[1]):
                self.data_path = sys.argv[1]
            else:
                print('file path supplied via sys.argv is not valid')
        else:
            self.data_path = 'src/resources/dummy_data_with_balances.xlsx'
        self.df = pd.DataFrame()
        self.df_subset = pd.DataFrame()
        self.load_df()
        print('data loaded and prepared successfully')
        # df must have Row and AccountBalance columns
        self.config['columns'].insert(0, 'Row')
        self.config['columns'].append('AccountBalance')
        self.config['display_columns'] = self.config['columns']
        self.filters_list = []

        ### tk inter gui ###
        if tk:
            # self.init_tk()
            self.root = Tk()

            self.icon_transparent = PhotoImage(file='src/resources/favicon_transparent.png')
            self.filters_win = Filterswindow(app=self, icon=self.icon_transparent)
            self.main = Mainwindow(self, self.config, 'src/resources/favicon.png', 'forest-dark')
            plt.rcParams['figure.facecolor'] = self.main.style_bg_col
            self.balances_win = Treewindow(app=self, icon=self.icon_transparent)
            self.groupby_win = Groupwindow(app=self, icon=self.icon_transparent)
            self.details = Treewindow(app=self, icon=self.icon_transparent)

            # show popup window with balances
            self.move_time_window('onwards') # wraps update_subset
            self.show_balances()
            self.update_groupby_win('Category')
            self.initiated = True
            self.main.root.mainloop()


    def load_df(self):
        # for employing the proper load function based on extension
        self.df = data_loader(self.data_path)
        # analyze the df for main_currency
        self.determine_main_currency()
        # ensure a datatime type column exists, fills NA's, adds Row and AccountBalance columns, sort by Day:
        self.df = data_prepare(self.df, self.config['main_currency'])
        # write the dates of the first and last record
        self.dates['first_record'] = datetime.datetime.fromisoformat(self.df['Day'].iloc[0])
        self.dates['last_record'] = datetime.datetime.fromisoformat(self.df['Day'].iloc[-1]) + relativedelta(days=1)


    def determine_main_currency(self):
        c = self.config['currencies'] 
        for currency in c:
            if currency in self.df.columns:
                self.config['main_currency'] = currency
                self.config['columns'].append(currency)
                return
        print('no valid currency found in dataframe. the header of one column has to match one of the following: ' + str(c))     


    def group_opts_change(self):
        if self.main.group_category.get():
            self.group_opts.append('Category')
        elif 'Category' in self.group_opts:
            self.group_opts.remove('Category')
        # if group options change but we not showing groups leave it
        if self.group != "None":
            self.group_change(self.group)

    def group_change(self, group):
        self.details.close()
        self.group = group

        if group == 'None':
            self.config['display_columns'] = self.config['columns']
            # -1 since original columns got the Row column
            self.main.frame_tree_width = int(60 + (len(self.config['display_columns']) - 1) * 130)
        else:
            self.config['display_columns'] = ['group'] + self.group_opts + [self.config['main_currency']]
            # groups aint got Row col
            self.main.frame_tree_width = int(len(self.config['display_columns']) * 130)
            
        self.main.frame_tree['width'] = self.main.frame_tree_width
        update_tree_structure(self.main.tree_main, self.config['display_columns'])
        self.update_subset()

    def move_time_window(self, direction=''):
        self.details.close()
        if direction == 'today':
            self.main.period_days.set('0')
            self.main.period_months.set('1')
            self.main.period_years.set('0')
            self.period = relativedelta(months=1)
            self.dates['start'] = self.todays_month - self.period
            self.dates['end'] = self.todays_month
        elif direction == 'last':
            self.main.period_days.set('0')
            self.main.period_months.set('1')
            self.main.period_years.set('0')
            self.period = relativedelta(months=1)
            self.dates['start'] = self.dates['first_record']
            self.dates['end'] = self.dates['first_record'] + self.period
        elif direction == 'backwards':
            self.dates['start'] = self.dates['start'] - self.period
            self.dates['end'] = self.dates['end'] - self.period
            if self.dates['end'] < self.dates['first_record']:
                showinfo('Information', 'Period set before the first record ('+str(self.dates['first_record'])+')')
        elif direction == 'onwards':
            self.dates['start'] = self.dates['start'] + self.period
            self.dates['end'] = self.dates['end'] + self.period
            if self.dates['start'] > self.dates['last_record']:
                if self.initiated:
                    showinfo('Information', 'Period set past the last record ('+str(self.dates['last_record'])+')')
                else:
                    self.move_time_window('backwards')
        self.main.start_date.set(self.dates['start'].strftime("%Y-%m-%d"))
        self.main.end_date.set(self.dates['end'].strftime("%Y-%m-%d"))
        self.update_subset()
        self.main.tree_main.yview_moveto(0)


    def add_quick_filter(self, column, value):
        self.filters_list.append((column,value))
        
        self.df_subset = self.df_subset[self.filters_cond()]
        
        self.filters_win.show(self.filters_list)

        self.update_tree_records()


    def update_tree_records(self):
        update_tree_records(self.df_subset, self.main.tree_main, self.config['display_columns'])

    # parses filters_list to be used 
    def filters_cond(self):

        if len(self.filters_list) > 0:
            _ = self.filters_list[0]
            filters_cond = (self.df_subset[_[0]] == _[1])

            for _ in self.filters_list[:-1]:
                filters_cond = filters_cond & (self.df_subset[_[0]] == _[1])

            return filters_cond
        
        return list(self.df.columns)

    def update_subset(self, instruction=''):
        self.details.close()

        # timely
        if self.dates['start'] and self.dates['end']:
            self.df_subset = self.df[(self.dates['start'] <= self.df['datetime']) & (self.df['datetime'] <= self.dates['end'])]
        self.main.start_date.set(self.dates['start'].strftime("%Y-%m-%d"))
        self.main.end_date.set(self.dates['end'].strftime("%Y-%m-%d"))

        # in/out
        if instruction[:5] == 'inout':
            self.in_out = instruction[6:]
        if self.in_out == 'All':
            pass
        elif self.in_out in ['Income', 'Expenses']:
            self.df_subset = self.df_subset[self.df_subset['Income/Expenses'] == self.in_out]
        elif self.in_out == 'Transfer':
            self.df_subset = self.df_subset[(self.df_subset['Income/Expenses'] == 'Transfer in') | (self.df_subset['Income/Expenses'] == 'Transfer out')]

        # groups
        if self.group != 'None':
            if self.group == 'Day':
                self.df_subset['group'] = self.df_subset['Day']
            elif self.group == 'Month':
                self.df_subset['group'] = [year_month_from_iso(_) for _ in self.df_subset['Day'].to_list()]
            elif self.group == 'Year':
                self.df_subset['group'] = [year_from_iso(_) for _ in self.df_subset['Day'].to_list()]
            self.df_subset = self.df_subset.groupby(['group'] + self.group_opts).sum()[self.config['main_currency']].reset_index()
            # group has the bad habit of having infinite decimal places
            self.df_subset[self.config['main_currency']] = self.df_subset[self.config['main_currency']].round(2)

        self.df_subset = self.df_subset[self.filters_cond()]

        self.update_tree_records()

        # update groupby_win if it was initiated
        if self.groupby_win.initiated:
            self.update_groupby_win(self.group_by)


    def on_double_click(self, event):
        tree_idx = self.main.tree_main.identify_row(event.y) # self.main.tree_main.identify('item', event.x, event.y)
        df_idx = int(self.main.tree_main.item(tree_idx, 'values')[0]) # formerly (tree_idx, 'text') when Row was supplied
        
        self.details.update(
            dataframe = pd.DataFrame([self.df_subset.columns,self.df_subset.loc[df_idx].to_list()]).T.rename(columns={0: "Column", 1: "Cell"}),
            title = "Details",
            position = [
                self.main.main_width + self.main.main_x + 2, 
                self.main.main_y + self.balances_win.dataframe.shape[0] * 30 + 60 # 30 * 11 ~ 340
            ]
        )


    def on_entry_change(self, instruction):
        if instruction == 'start':
            self.dates['start'] = datetime.datetime.fromisoformat(self.main.start_date.get())
        elif instruction == 'end':
            self.dates['end'] = datetime.datetime.fromisoformat(self.main.end_date.get())
        elif instruction == 'period':
            yearsStr = self.main.period_years.get()
            years = int(yearsStr) if yearsStr != '' else 0
            monthsStr = self.main.period_months.get()
            months = int(monthsStr) if monthsStr != '' else 0
            daysStr = self.main.period_days.get()
            days = int(daysStr) if daysStr != '' else 0
            self.period = relativedelta(years=years, months=months, days=days)
            if self.dates['start'] + self.period <= self.dates['last_record']:
                self.dates['end'] = self.dates['start'] + self.period
            else:
                self.dates['start'] = self.dates['end'] - self.period

        if instruction in ['end', 'start']:
            self.period = parse_period(self.dates['start'], self.dates['end'])
            # TODO: WRITE THIS PERIOD NOW THAT IS WORKING REALLY COOL TO A DROPDOWN / ENTRY

        self.update_subset()


    def update_groupby_win(self, by):
        self.group_by = by
        grouped = self.df_subset.groupby([by])[self.config['main_currency']]
        groupedsum = grouped.sum().reset_index()
        groupedsorted = groupedsum.sort_values(by=self.config['main_currency'], ascending=True)
        groupedsortedrounded = groupedsorted.round(0)

        self.groupby_win.update(
            dataframe = groupedsortedrounded,
            fig = pie_chart(df_grouped=grouped, color=self.main.style_bg_col),
            title = f"{self.in_out} grouped by {by}",
            position = [10, -10] # [x,y]
        )


    def show_balances(self):
        balances = pd.DataFrame(get_last_balance_per_account(self.df), columns=["Account",self.config['main_currency']])

        self.balances_win.update(
            dataframe=balances[-balances["Account"].isin(self.config['hidden_balances'])], 
            title="Balances", 
            position=[ # [x,y]
                self.main.main_width + self.main.main_x + 2, 
                self.main.main_y
            ]
        )
        

if __name__ == '__main__':
    app = App()
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
from modules.windows.main import Mainwindow
from modules.windows.group import Groupwindow
from modules.windows.tree import Treewindow
from modules.windows.filters import Filterswindow

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
        self.group_by = None
        self.group_opts = []
        self.in_out = self.config['default_subset']
        self.dates = {} # dates in ISO format: '2022-06-01T00:00:00'
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

        initial = self.dates['last_record'] # self.todays_month
        self.dates['start'] = initial - self.period # dates in ISO format: '2022-06-01T00:00:00'
        self.dates['end'] = initial

        self.CURRENCY = self.config['main_currency']
        print('data loaded and prepared successfully')
        # df must have Row and AccountBalance columns
        self.config['columns'].insert(0, 'Row')
        self.config['columns'].append('AccountBalance')
        self.config['display_columns'] = self.config['columns']
        self.filters_list = []

        ### tk inter gui ###
        self.root = Tk()

        self.icon_azul = PhotoImage(file='src/resources/favicon_dark.png')
        self.filters_win = Filterswindow(app=self, icon=self.icon_azul)
        self.main = Mainwindow(self, self.config, 'src/resources/favicon_verde.png', 'forest-dark')
        plt.rcParams['figure.facecolor'] = self.main.style_bg_col
        self.balances_win = Treewindow(app=self, icon=self.icon_azul, purpose="balances")
        self.groupby_win = Groupwindow(app=self, icon=self.icon_azul, purpose="group")
        self.details = Treewindow(app=self, icon=self.icon_azul)

        # show popup window with balances
        self.move_time_window('onwards') # wraps update_subset
        self.show_balances()
        self.update_groupby_win('Category')
        self.initiated = True
        if tk:
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
        _one_day = relativedelta(days=1)
        _last_record = datetime.datetime.fromisoformat(self.df['Day'].iloc[-1])
        _last = _last_record if ((_last_record + _one_day).month > _last_record.month) else _last_record + _one_day
        self.dates['last_record'] = datetime.datetime(_last.year, _last.month, 1)


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
            self.config['display_columns'] = ['group'] + self.group_opts + [self.CURRENCY]
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
        self.filters_win.show(self.filters_list)

        self.update_subset()

        if column == "Note":
            self.update_groupby_win("Category1")
        elif column == "Category1":
            self.update_groupby_win("Note")


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
        
        return list(self.df_subset.columns)

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
            self.df_subset = self.df_subset[self.df_subset['Direction'] == self.in_out]
        elif self.in_out == 'Transfer':
            self.df_subset = self.df_subset[(self.df_subset['Direction'] == 'Transfer in') | (self.df_subset['Direction'] == 'Transfer out')]

        # groups
        if self.group != 'None':
            # the columns have been carefuly selected to not break anything, don't change crazily
            self.df_subset = self.df_subset[[_ for _ in self.df_subset.columns if _ != "datetime"]]
            if self.group == 'Day':
                self.df_subset['group'] = self.df_subset['Day']
            elif self.group == 'Month':
                self.df_subset['group'] = [year_month_from_iso(_) for _ in self.df_subset['Day'].to_list()]
            elif self.group == 'Year':
                self.df_subset['group'] = [year_from_iso(_) for _ in self.df_subset['Day'].to_list()]
            self.df_subset = self.df_subset.groupby(['group'] + self.group_opts).sum().reset_index()
            # group has the bad habit of having infinite decimal places
            self.df_subset[self.CURRENCY] = self.df_subset[self.CURRENCY].round(2)
            # self.update_groupby_win("Day")

        self.df_subset = self.df_subset[self.filters_cond()]
        
        self.update_tree_records()

        # update groupby_win if it was initiated
        if self.groupby_win.initiated:
            self.update_groupby_win(self.group_by)


    def on_double_click(self, event):
        tree_idx = self.main.tree_main.identify_row(event.y) # self.main.tree_main.identify('item', event.x, event.y)
        df_idx = int(self.main.tree_main.item(tree_idx, 'values')[0]) # formerly (tree_idx, 'text') when Row was supplied
        
        self.details.update_plus_tk(
            dataframe = pd.DataFrame([self.df_subset.columns,self.df_subset.loc[df_idx].to_list()]).T.rename(columns={0: "Column", 1: "Cell"}),
            title = "Details",
            position = [
                0,
                0,
                self.main.main_width + self.main.main_x + 2, 
                self.main.main_y + self.balances_win.dataframe.shape[0] * 30 + 60 # 30 * 11 ~ 340
            ]
        )


    def on_entry_change(self, instruction, date=None):
        print(instruction)
        print(self.main.start_date.get())
        if instruction == 'start':
            self.dates['start'] = datetime.datetime.fromisoformat(date)
        elif instruction == 'end':
            self.dates['end'] = datetime.datetime.fromisoformat(date)
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
        grouped = self.df_subset.groupby([by])[self.CURRENCY]
        groupedsum = grouped.sum().reset_index()
        groupedsorted = groupedsum.sort_values(by=self.CURRENCY, ascending=True)
        groupedsortedrounded = groupedsorted.round(0)

        self.groupby_win.update(
            dataframe = groupedsortedrounded,
            fig = pie_chart(df_grouped=grouped, color=self.main.style_bg_col),
            title = f"{self.in_out} grouped by {by}",
            position = [500, 60, 10, -10] # [x,y]
        )


    def show_balances(self):
        balances = pd.DataFrame(get_last_balance_per_account(self.df), columns=["Account",self.CURRENCY])

        self.balances_win.update_plus_tk(
            dataframe=balances[-balances["Account"].isin(self.config['hidden_balances'])], 
            title="Balances", 
            position=[ # [x,y]
                0,0,
                self.main.main_width + self.main.main_x + 2, 
                self.main.main_y
            ]
        )
        

if __name__ == '__main__':
    app = App()
    pass
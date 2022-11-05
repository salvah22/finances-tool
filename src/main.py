"""
Money Manager software developed by Salvador Hernández
Created: September 2022
Last Edit: October 2022
"""

# standard python libraries

import sys, yaml, os
import datetime
from dateutil.relativedelta import relativedelta
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.messagebox import showinfo

# extra libraries
import pandas as pd

# own utils
from utils.time import parse_period
from utils.data import *
from utils.tk_inter import update_tree, popup_tree_window


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

    def __init__(self, tk=True):
        ### parameters ###
        with open('src/configs/app.yml', 'r') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

        self._period = relativedelta(months=1)
        self.group = "None"
        self.group_opts = []
        self.in_out = self.config['default_subset']
        self.dates = {'initial': self.todays_month - self._period, 'final': self.todays_month} # dates in ISO format: '2022-06-01T00:00:00'
        ### data ###
        if len(sys.argv) > 1:
            if os.path.exists(sys.argv[1]):
                self.data_path = sys.argv[1]
            else:
                print("supplied file path not valid, file does not exist?")
        else:
            self.data_path = 'src/resources/dummy_data_with_balances.xlsx'

        self.df = pd.DataFrame()
        self.df_subset = pd.DataFrame()
        self.load_df()
        print('data loaded and prepared successfully')

        for currency in self.config['currencies']:
            if currency in self.df.columns:
                self.config['main_currency'] = currency
                self.config['display_columns'].insert(-1, currency)
                break

        if 'AccountBalance' in self.df.columns:
            self.config['display_columns'] += ['AccountBalance']

        ### tk inter gui related stuff ###
        self.tk_elems = {}
        if tk:
            self.init_tk()
            self.period_update_callback()
            self.move_time_window('onwards') # wraps update_subset
            self.tk_elems['main_app'].mainloop()

    def load_df(self):
        self.df = data_loader(self.data_path) # checks for the extensions and employs the proper load function
        # prepare/preprocess the dataframe:
        self.df = data_prepare(self.df)
        # write the dates of the first and last record
        self.dates['first_record'] = datetime.datetime.fromisoformat(self.df['Day'].iloc[0])
        self.dates['last_record'] = datetime.datetime.fromisoformat(self.df['Day'].iloc[-1]) + relativedelta(days=1)
        self.df_subset = pd.DataFrame()

    def init_tk(self):
        ### main definitions
        self.windows = ['main_app']
        self.tk_elems['main_app'] = tk.Tk()
        self.tk_elems['main_app'].title('Money Mgr.')
        self.tk_elems['main_app'].bind('<Escape>', lambda e: self.tk_elems['main_app'].destroy())
        self.tk_elems['screen_width'] = self.tk_elems['main_app'].winfo_screenwidth()
        self.tk_elems['screen_height'] = self.tk_elems['main_app'].winfo_screenheight()
        self.tk_elems['main_app_width'] = int(len(self.config['display_columns']) * 130 + 60 + 10) # 130 p/column + 60 idx + 10 margins ~ 980
        self.tk_elems['main_app_height'] = 650
        self.tk_elems['main_app'].geometry(f'{self.tk_elems["main_app_width"]}x{self.tk_elems["main_app_height"]}')
        self.tk_elems['main_app_x'] = int((self.tk_elems['screen_width'])/2 - (self.tk_elems['main_app_width'])/2) # screen_width - app_width
        self.tk_elems['main_app_y'] = int((self.tk_elems['screen_height'])/2 - (self.tk_elems['main_app_height'])/2)
        self.tk_elems['icon'] = tk.PhotoImage(file="src/resources/favicon.png")
        self.tk_elems['main_app'].tk.call('wm', 'iconphoto', self.tk_elems['main_app']._w, self.tk_elems['icon'])
        ### menu bar
        self.tk_elems['main_app_menubar'] = tk.Menu(self.tk_elems['main_app'])
        self.tk_elems['main_app_filemenu'] = tk.Menu(self.tk_elems['main_app_menubar'], tearoff=0)
        self.tk_elems['main_app_filemenu'].add_command(label="Exit", command=self.tk_elems['main_app'].destroy)
        self.tk_elems['main_app_menubar'].add_cascade(label="File", menu=self.tk_elems['main_app_filemenu'])
        self.tk_elems['main_app'].config(menu=self.tk_elems['main_app_menubar'])
        
        ### style
        self.tk_elems['style'] = ttk.Style()
        self.tk_elems['style'].configure("mystyle.Treeview", rowheight=30) # default: 20
        self.tk_elems['style'].configure("mystyle.Treeview", font=self.config['fonts']['f08'])
        self.tk_elems['style'].configure("mystyle.Treeview.Heading", font=self.config['fonts']['f10'])
        self.tk_elems['style'].layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])
        self.tk_elems['frame_header'] = tk.Frame(self.tk_elems['main_app'])
        self.tk_elems['frame_header'].pack(expand=True)
        ### Period frame
        self.tk_elems['frame_period'] = tk.Frame(self.tk_elems['frame_header'])
        self.tk_elems['frame_period'].pack(expand=True, side=tk.LEFT)
        self.tk_elems['date_initial'] = tk.StringVar()
        self.tk_elems['date_final'] = tk.StringVar()
        self.tk_elems['period_years'] = tk.StringVar()
        self.tk_elems['period_months'] = tk.StringVar()
        self.tk_elems['period_days'] = tk.StringVar()
        self.tk_elems['button_today'] = tk.Button(self.tk_elems['frame_period'], text='Today', width=2, command=lambda: self.move_time_window('today'), font=self.config['fonts']['f12'], bg=self.config['colors']['green'])
        self.tk_elems['button_today'].pack(side=tk.LEFT)
        self.tk_elems['button_backwards'] = tk.Button(self.tk_elems['frame_period'], text='<', width=2, command=lambda: self.move_time_window('backwards'), font=self.config['fonts']['f12'])
        self.tk_elems['button_backwards'].pack(side=tk.LEFT)
        self.tk_elems['entry_date_initial'] = tk.Entry(self.tk_elems['frame_period'], textvariable=self.tk_elems['date_initial'], font=self.config['fonts']['f12'], width=10)
        self.tk_elems['entry_date_initial'].pack(side=tk.LEFT)
        self.tk_elems['entry_date_initial'].bind('<Return>', lambda event: self.on_entry_change('initial'))
        self.tk_elems['entry_date_final'] = tk.Entry(self.tk_elems['frame_period'], textvariable=self.tk_elems['date_final'], font=self.config['fonts']['f12'], width=10)
        self.tk_elems['entry_date_final'].pack(side=tk.LEFT)
        self.tk_elems['entry_date_final'].bind('<Return>', lambda event: self.on_entry_change('final'))
        self.tk_elems['button_onwards'] = tk.Button(self.tk_elems['frame_header'], text='>', width=2, command=lambda: self.move_time_window('onwards'), font=self.config['fonts']['f12'])
        self.tk_elems['button_onwards'].pack(side=tk.LEFT)
        self.tk_elems['frame_period'] = tk.Frame(self.tk_elems['frame_header'])
        self.tk_elems['frame_period'].pack(expand=True, side=tk.LEFT)
        self.tk_elems['entry_period_years'] = tk.Entry(self.tk_elems['frame_period'], textvariable=self.tk_elems['period_years'], font=self.config['fonts']['f10'], width=8)
        self.tk_elems['entry_period_years'].pack(side=tk.BOTTOM)
        self.tk_elems['entry_period_years'].bind('<Return>', lambda event: self.on_entry_change('period'))
        self.tk_elems['entry_period_months'] = tk.Entry(self.tk_elems['frame_period'], textvariable=self.tk_elems['period_months'], font=self.config['fonts']['f10'], width=8)
        self.tk_elems['entry_period_months'].pack(side=tk.BOTTOM)
        self.tk_elems['entry_period_months'].bind('<Return>', lambda event: self.on_entry_change('period'))
        self.tk_elems['entry_period_days'] = tk.Entry(self.tk_elems['frame_period'], textvariable=self.tk_elems['period_days'], font=self.config['fonts']['f10'], width=8)
        self.tk_elems['entry_period_days'].pack(side=tk.BOTTOM)
        self.tk_elems['entry_period_days'].bind('<Return>', lambda event: self.on_entry_change('period'))
        ### Button Group In/Out (EXPENSE/INCOME/TRANSFER/ALL)
        self.tk_elems['frame_in_out'] = tk.Frame(self.tk_elems['frame_header'])
        self.tk_elems['frame_in_out'].pack(expand=True, side=tk.LEFT)
        self.tk_elems['button_income'] = tk.Button(self.tk_elems['frame_in_out'], text='Income', width=4, height=1,
                                                  command=lambda: self.update_subset('Income'),
                                                  font=self.config['fonts']['f10'], bg=self.config['colors']['blue'])
        self.tk_elems['button_income'].grid(row=0, column=0)
        self.tk_elems['button_expenses'] = tk.Button(self.tk_elems['frame_in_out'], text='Expenses', width=4, height=1,
                                                  command=lambda: self.update_subset('Expenses'),
                                                  font=self.config['fonts']['f10'], bg=self.config['colors']['red'])
        self.tk_elems['button_expenses'].grid(row=1, column=0)
        self.tk_elems['button_transfers'] = tk.Button(self.tk_elems['frame_in_out'], text='Transfer', width=4, height=1,
                                                  command=lambda: self.update_subset('Transfer'),
                                                  font=self.config['fonts']['f10'])
        self.tk_elems['button_transfers'].grid(row=0, column=1)
        self.tk_elems['button_all'] = tk.Button(self.tk_elems['frame_in_out'], text='All', width=4, height=1,
                                                  command=lambda: self.update_subset('All'),
                                                  font=self.config['fonts']['f10'])
        self.tk_elems['button_all'].grid(row=1, column=1)

        ### GROUPING
        self.tk_elems['frame_groups'] = tk.Frame(self.tk_elems['frame_header'], padx=5, pady=5) # , highlightbackground="black", highlightthickness=2
        self.tk_elems['frame_groups'].pack(expand=True)
        tk.Label(self.tk_elems['frame_groups'], text="Grouping", font=self.config['fonts']['f10']).pack(side=tk.TOP)
        self.tk_elems['group'] = tk.StringVar()
        self.tk_elems['group'].set("None") # default value
        self.tk_elems['group_opt_menu'] = tk.OptionMenu(self.tk_elems['frame_groups'], self.tk_elems['group'], "None", "Day", "Month", "Year", command=self.group_change)
        self.tk_elems['group_opt_menu'].pack(side=tk.TOP)
        self.tk_elems['group_category'] = tk.BooleanVar(value=False)
        self.tk_elems['checkbox_category'] = ttk.Checkbutton(self.tk_elems['frame_groups'], text='category', variable=self.tk_elems['group_category'], onvalue=True, offvalue=False, command=self.group_opts_change)
        self.tk_elems['checkbox_category'].pack(side=tk.TOP, expand=True, padx=(0, 5))
        ### MAIN BIG TREE
        self.tk_elems['frame_tree'] = tk.Frame(self.tk_elems['main_app'], padx=5, pady=5)
        self.tk_elems['frame_tree'].pack(expand=True)
        self.tk_elems['main_tree'] = ttk.Treeview(self.tk_elems['frame_tree'], style="mystyle.Treeview", height=15) # originally height=10
        self.tk_elems['main_tree'].pack(expand=True)
        self.tk_elems['main_tree'].bind('<Double-1>', self.on_double_click)
        self.tk_elems['frame_footer'] = tk.Frame(self.tk_elems['main_app'])
        self.tk_elems['frame_footer'].pack(expand=True)

        self.tk_elems['button_groupby_category'] = tk.Button(self.tk_elems['frame_footer'], text='Groupby category', width=12, command=self.groupby_category, font=self.config['fonts']['f10'], bg=self.config['colors']['green'])
        self.tk_elems['button_groupby_category'].pack(side=tk.LEFT)
        if 'AccountBalance' in self.config['display_columns']:
            # show AccountBalance window
            self.show_balances()
    
    def group_opts_change(self):
        if self.tk_elems['group_category'].get():
            self.group_opts.append('Category')
        elif 'Category' in self.group_opts:
            self.group_opts.remove('Category')
        if self.group != "None":
            self.update_subset()

    def group_change(self, group):
        self.group = group
        self.update_subset()


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
            self.df_subset = self.df_subset[(self.df_subset['Income/Expenses'] == 'Transfer in') | (self.df_subset['Income/Expenses'] == 'Transfer out')]
        if self.group == 'None':
            cols = self.config['display_columns']
        else:
            cols = ["group"] + self.group_opts
            if self.group == 'Day':
                self.df_subset['group'] = self.df_subset['Day']
            elif self.group == 'Month':
                self.df_subset['group'] = self.df_subset.apply(lambda row: year_month_from_iso(row['Day']), axis=1)
            elif self.group == 'Year':
                self.df_subset['group'] = self.df_subset.apply(lambda row: year_from_iso(row['Day']), axis=1)
            self.df_subset = self.df_subset.groupby(cols).sum()[self.config['main_currency']].reset_index()
            # for display:
            cols += [self.config['main_currency']]
        update_tree(self.df_subset, self.tk_elems['main_tree'], cols)


    def on_double_click(self, event):
        tree_idx = self.tk_elems['main_tree'].identify('item', event.x, event.y)
        df_idx = self.tk_elems['main_tree'].item(tree_idx,'text')
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

    def groupby_category(self):
        grouped = self.df_subset.groupby(["Category"])['EUR'].sum().reset_index()
        groupedsorted = grouped.sort_values(by='EUR', ascending=True)
        groupedsortedrounded = groupedsorted.round(0)
        popup_tree_window(
            dataframe=groupedsortedrounded,
            title="Data grouped by category",
            icon=self.tk_elems['icon']
        )

    def show_balances(self):
        balances = pd.DataFrame(get_last_balance_per_account(self.df), columns=["Account",self.config['main_currency']])
        position_x = self.tk_elems['main_app_width'] + self.tk_elems['main_app_x'] # width + x (center)
        width = 130 * balances.shape[1] + 60 # 130 p/column + 60 idx + 10 margins ~ 980
        height = 30 * balances.shape[0] + 25
        geom = [width,height,position_x,self.tk_elems['main_app_y']]
        popup_tree_window(
            dataframe=balances, 
            title="Balances", 
            geom=geom, 
            treeview_height=balances.shape[0],
            icon=self.tk_elems['icon']
        )

if __name__ == '__main__':
    app = App()
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
from utils.tk_inter import *


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
        self.dates = {'start': self.todays_month - self._period, 'end': self.todays_month} # dates in ISO format: '2022-06-01T00:00:00'
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
                self.config['columns'].insert(-1, currency)
                break

        if 'AccountBalance' in self.df.columns:
            self.config['columns'] += ['AccountBalance']
        
        self.config['display_columns'] = self.config['columns']

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
        self.tk_elems['tree_main_records'] = 15
        self.tk_elems['frame_tree_height'] = int(30 * self.tk_elems['tree_main_records'])
        self.tk_elems['frame_tree_width'] = int(60 + (len(self.config['display_columns']) - 1) * 130) # 60 idx + 130 p/column 
        self.tk_elems['main_app'] = tk.Tk()
        self.tk_elems['main_app'].title('Money Mgr.')
        self.tk_elems['main_app'].bind('<Escape>', lambda e: self.tk_elems['main_app'].destroy())
        self.tk_elems['screen_width'] = self.tk_elems['main_app'].winfo_screenwidth()
        self.tk_elems['screen_height'] = self.tk_elems['main_app'].winfo_screenheight()
        self.tk_elems['main_app_width'] = self.tk_elems['frame_tree_width'] + 20 # + 10 for margins ~ 1000
        self.tk_elems['main_app_height'] = self.tk_elems['frame_tree_height'] + 200 # 450 treeview + 200 other elements ~ 650
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
        self.tk_elems['start_date'] = tk.StringVar()
        self.tk_elems['end_date'] = tk.StringVar()
        self.tk_elems['period_years'] = tk.StringVar()
        self.tk_elems['period_months'] = tk.StringVar()
        self.tk_elems['period_days'] = tk.StringVar()
        self.tk_elems['button_today'] = tk.Button(self.tk_elems['frame_period'], text='Today', width=2, command=lambda: self.move_time_window('today'), font=self.config['fonts']['f12'], bg=self.config['colors']['green'])
        self.tk_elems['button_today'].pack(side=tk.LEFT)
        self.tk_elems['button_backwards'] = tk.Button(self.tk_elems['frame_period'], text='<', width=2, command=lambda: self.move_time_window('backwards'), font=self.config['fonts']['f12'])
        self.tk_elems['button_backwards'].pack(side=tk.LEFT)
        self.tk_elems['entry_date_start'] = tk.Entry(self.tk_elems['frame_period'], textvariable=self.tk_elems['start_date'], font=self.config['fonts']['f12'], width=10)
        self.tk_elems['entry_date_start'].pack(side=tk.LEFT)
        self.tk_elems['entry_date_start'].bind('<Return>', lambda event: self.on_entry_change('start'))
        self.tk_elems['entry_date_end'] = tk.Entry(self.tk_elems['frame_period'], textvariable=self.tk_elems['end_date'], font=self.config['fonts']['f12'], width=10)
        self.tk_elems['entry_date_end'].pack(side=tk.LEFT)
        self.tk_elems['entry_date_end'].bind('<Return>', lambda event: self.on_entry_change('end'))
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
                                                  command=lambda: self.update_subset('inout_Income'),
                                                  font=self.config['fonts']['f10'], bg=self.config['colors']['blue'])
        self.tk_elems['button_income'].grid(row=0, column=0)
        self.tk_elems['button_expenses'] = tk.Button(self.tk_elems['frame_in_out'], text='Expenses', width=4, height=1,
                                                  command=lambda: self.update_subset('inout_Expenses'),
                                                  font=self.config['fonts']['f10'], bg=self.config['colors']['red'])
        self.tk_elems['button_expenses'].grid(row=1, column=0)
        self.tk_elems['button_transfers'] = tk.Button(self.tk_elems['frame_in_out'], text='Transfer', width=4, height=1,
                                                  command=lambda: self.update_subset('inout_Transfer'),
                                                  font=self.config['fonts']['f10'])
        self.tk_elems['button_transfers'].grid(row=0, column=1)
        self.tk_elems['button_all'] = tk.Button(self.tk_elems['frame_in_out'], text='All', width=4, height=1,
                                                  command=lambda: self.update_subset('inout_All'),
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
        self.tk_elems['frame_tree_container'] = tk.Frame(self.tk_elems['main_app'])
        self.tk_elems['frame_tree_container'].pack(expand=True, side=tk.TOP)
        self.tk_elems['frame_tree'] = tk.Frame(self.tk_elems['frame_tree_container'], width=self.tk_elems["frame_tree_width"], height=self.tk_elems['frame_tree_height']) # -20 for the scrollbar
        self.tk_elems['frame_tree'].grid(row=0, column=0)
        # By default, Tkinter Frame fits to its children and thus its width and height depends on its children. 
        # You can override this behavior and force a specific width and height to the frame.
        self.tk_elems['frame_tree'].pack_propagate(0)
        self.tk_elems['tree_main'] = ttk.Treeview(self.tk_elems['frame_tree'], style="mystyle.Treeview", height=self.tk_elems['tree_main_records'], columns=self.config['display_columns'], show='headings') # originally height=10
        self.tk_elems['tree_main'].bind('<Double-1>', self.on_double_click)
        self.tk_elems['tree_main'].pack(side=tk.LEFT) # .pack(side=tk.LEFT)
        update_tree_structure(self.tk_elems['tree_main'], self.config['display_columns'])
        self.tk_elems['tree_main_scrollbar'] = ttk.Scrollbar(self.tk_elems['frame_tree_container'], orient=tk.VERTICAL, command=self.tk_elems['tree_main'].yview)
        self.tk_elems['tree_main'].configure(yscroll=self.tk_elems['tree_main_scrollbar'].set)
        self.tk_elems['tree_main_scrollbar'].grid(row=0, column=1, sticky='ns') # .pack(side=tk.LEFT, fill=tk.Y)
        ### Footer buttons
        self.tk_elems['frame_footer'] = tk.Frame(self.tk_elems['main_app'])
        self.tk_elems['frame_footer'].pack(expand=True)
        tk.Label(self.tk_elems['frame_footer'], text="View grouped by: ", font=self.config['fonts']['f10']).pack(side=tk.LEFT)
        self.tk_elems['button_groupby_category'] = tk.Button(self.tk_elems['frame_footer'], text='Category', width=12, command=lambda: self.popup_groupby('Category'), font=self.config['fonts']['f10'], bg=self.config['colors']['green'])
        self.tk_elems['button_groupby_category'].pack(side=tk.LEFT)
        self.tk_elems['button_groupby_note'] = tk.Button(self.tk_elems['frame_footer'], text='Note', width=12, command=lambda: self.popup_groupby('Note'), font=self.config['fonts']['f10'], bg=self.config['colors']['green'])
        self.tk_elems['button_groupby_note'].pack(side=tk.LEFT)
        if 'AccountBalance' in self.config['display_columns']:
            # show AccountBalance window
            self.show_balances()
    
    def group_opts_change(self):
        if self.tk_elems['group_category'].get():
            self.group_opts.append('Category')
        elif 'Category' in self.group_opts:
            self.group_opts.remove('Category')
        # if group options change but we not showing groups leave it
        if self.group != "None":
            self.group_change(self.group)

    def group_change(self, group):
        self.group = group

        if group == 'None':
            self.config['display_columns'] = self.config['columns']
            # -1 since original columns got ID
            self.tk_elems['frame_tree_width'] = int(60 + (len(self.config['display_columns']) - 1) * 130)
        else:
            self.config['display_columns'] = ['group'] + self.group_opts + [self.config['main_currency']]
            # groups aint got ID
            self.tk_elems['frame_tree_width'] = int(len(self.config['display_columns']) * 130)
            
        self.tk_elems['frame_tree']['width'] = self.tk_elems['frame_tree_width']
        update_tree_structure(self.tk_elems['tree_main'], self.config['display_columns'])
        self.update_subset()

    def move_time_window(self, direction=''):
        if direction == 'today':
            self.period = relativedelta(months=1)
            self.dates['start'] = self.todays_month - self.period
            self.dates['end'] = self.todays_month
            if self.dates['end'] + self.period <= self.dates['last_record']:
                self.dates['start'] = self.dates['start'] + self.period
                self.dates['end'] = self.dates['end'] + self.period
            else:
                self.dates['end'] = self.dates['last_record']
                self.dates['start'] = self.dates['last_record'] - self.period
        elif direction == 'backwards':
            # assert we don't go outside timely boundaries
            if self.dates['start'] - self.period >= self.dates['first_record']:
                self.dates['start'] = self.dates['start'] - self.period
                self.dates['end'] = self.dates['end'] - self.period
            else:
                self.dates['start'] = self.dates['first_record']
                self.dates['end'] = self.dates['first_record'] + self.period
        elif direction == 'onwards':
            # assert we don't go outside timely boundaries
            if self.dates['end'] + self.period <= self.dates['last_record']:
                self.dates['start'] = self.dates['start'] + self.period
                self.dates['end'] = self.dates['end'] + self.period
            else:
                self.dates['end'] = self.dates['last_record']
                self.dates['start'] = self.dates['last_record'] - self.period
        self.tk_elems['start_date'].set(self.dates['start'].strftime("%Y-%m-%d"))
        self.tk_elems['end_date'].set(self.dates['end'].strftime("%Y-%m-%d"))
        self.update_subset()


    def update_subset(self, instruction=''):
        
        # timely
        if self.dates['start'] and self.dates['end']:
            self.df_subset = self.df[(self.dates['start'] <= self.df['datetime']) & (self.df['datetime'] <= self.dates['end'])]
        self.tk_elems['start_date'].set(self.dates['start'].strftime("%Y-%m-%d"))
        self.tk_elems['end_date'].set(self.dates['end'].strftime("%Y-%m-%d"))

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

        update_tree_records(self.df_subset, self.tk_elems['tree_main'], self.config['display_columns'])


    def on_double_click(self, event):
        tree_idx = self.tk_elems['tree_main'].identify('item', event.x, event.y)
        df_idx = self.tk_elems['tree_main'].item(tree_idx,'text')
        showinfo("Transaction Details", str(self.df_subset.loc[df_idx]))


    def on_entry_change(self, instruction):
        if instruction == 'start':
            self.dates['start'] = datetime.datetime.fromisoformat(self.tk_elems['start_date'].get())
        elif instruction == 'end':
            self.dates['end'] = datetime.datetime.fromisoformat(self.tk_elems['end_date'].get())
        elif instruction == 'period':
            years = int(self.tk_elems['period_years'].get().split(" ")[0])
            months = int(self.tk_elems['period_months'].get().split(" ")[0])
            days = int(self.tk_elems['period_days'].get().split(" ")[0])
            self.period = relativedelta(years=years, months=months, days=days)
            self.dates['end'] = self.dates['start'] + self.period

        if instruction in ['end', 'start']:
            self.period = parse_period(self.dates['start'], self.dates['end'])
            # TODO: WRITE THIS PERIOD NOW THAT IS WORKING REALLY COOL TO A DROPDOWN / ENTRY

        self.update_subset()


    def popup_groupby(self, by):
        grouped = self.df_subset.groupby([by])['EUR'].sum().reset_index()
        groupedsorted = grouped.sort_values(by='EUR', ascending=True)
        groupedsortedrounded = groupedsorted.round(0)
        popup_tree_window(
            dataframe=groupedsortedrounded,
            title="Data grouped by " + by,
            icon=self.tk_elems['icon']
        )


    def show_balances(self):
        balances = pd.DataFrame(get_last_balance_per_account(self.df), columns=["Account",self.config['main_currency']])
        position = [self.tk_elems['main_app_width'] + self.tk_elems['main_app_x'] + 10, self.tk_elems['main_app_y']] # [x,y]
        popup_tree_window(
            dataframe=balances, 
            title="Balances", 
            position=position, 
            icon=self.tk_elems['icon'],
        )


if __name__ == '__main__':
    app = App()
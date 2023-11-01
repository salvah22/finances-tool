import sys
import pandas as pd
import numpy as np
from os import path

def data_loader(fp: str):
    """
    Function for loading inputs with a variety of extensions with the proper pandas read function
    """

    _, f = path.split(fp)
    _, file_ext = path.splitext(f)
    if file_ext == '.xlsx':
        df = pd.read_excel(fp)
    elif file_ext == '.csv':
        df = pd.read_csv(fp)
    else:
        sys.exit('data_path extension not supported')
        
    return df


def data_prepare(df: pd.DataFrame, main_currency: str):
    """
    Function for pre-processing the dataframe
    """
    # lets check day is recognized as datetime:
    if df.select_dtypes(include=[np.datetime64]).shape[1] == 0:
        try:
            df['Day'] = pd.to_datetime(df['Day'])
        except Exception as e:
            sys.exit(f'Day column in unrecognizable format, exception:\n{e}')

    # nans look ugly
    df.fillna("", inplace=True)

    # we want inverse order for the treeview, .iloc[0] will point to the oldest date
    df.sort_values(by='Day', ascending=True, inplace=True)

    # generate AccountBalance column if not in dataframe, it needs to be sorted by day
    if 'AccountBalance' not in df.columns:
        df = compute_balance(df, main_currency)

    # period is a very vague word for date, use it as datetime
    df['datetime'] = df['Day']

    # convert period to strf (YYYY-MM-DD)
    df['Day'] = [_.strftime("%Y-%m-%d") for _ in df['datetime'].to_list()] 

    # add the Row column
    df['Row'] = df.index

    return df

def get_last_balance_per_account(df: pd.DataFrame) -> list[list]:
    """
    get the last known value of 'AccountBalance' for each account
    """
    accounts = df["Account"].unique()
    balances = []
    for acc in accounts:
        balances.append([acc, round(df[df["Account"] == acc].iloc[-1]["AccountBalance"], 2)])
    return balances

def year_month_from_iso(datestring: str):
    yyyy, mm, _ = datestring.split('-')
    return yyyy + "-" + mm

def year_from_iso(datestring: str):
    yyyy, _, _ = datestring.split('-')
    return yyyy

# function for computing a balances column in the dataframe
def compute_balance(df: pd.DataFrame, main_currency: str):

    # function for assigning a +/- sign to expenses/income movements
    def amounts_with_sign(row):
        if row["Direction"] == "Expenses" or row["Direction"] == "Transfer out":
            return - row[main_currency]
        elif row["Direction"] == "Income" or row["Direction"] == "Transfer in":
            return row[main_currency]
        else:
            return 0
    
    accounts = df["Account"].unique()
    
    df["AccountBalance"] = 0
    
    df["_amountswsigns"] = df.apply(lambda row: amounts_with_sign(row), axis=1)

    for acc in accounts:
        cumsum = df[df["Account"] == acc]["_amountswsigns"].cumsum().round(2)
        for i in cumsum.index:
            df.loc[i, "AccountBalance"] = cumsum.loc[i]

    # drop the temporal columns
    df.drop("_amountswsigns", axis=1, inplace=True)
    
    return df

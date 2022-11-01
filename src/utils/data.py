import os, sys
import pandas as pd
import numpy as np

def data_loader(path):
    """
    Function for loading inputs with a variety of extensions with the proper pandas read function
    """

    parent, file = os.path.split(path)
    file_name, file_ext = os.path.splitext(file)
    if file_ext == '.xlsx':
        df = pd.read_excel(path)
    elif file_ext == '.csv':
        df = pd.read_csv(path)
    else:
        sys.exit('data_path extension not supported')

    # lets check day is recognized as datetime:
    if df.select_dtypes(include=[np.datetime64]).shape[1] == 0:
        try:
            df['Day'] = pd.to_datetime(df['Day'])
        except Exception as e:
            sys.exit(f'Day column in unrecognizable format, exception:\n{e}')

    # we want inverse order for the treeview, .iloc[0] is the oldest date
    return df.sort_values(by='Day', ascending=True) 


def data_prepare(df):
    """
    Function for pre-processing the dataframe
    """
    df['datetime'] = df['Day'] # period is a very bad word for date, use it as datetime
    df['Day'] = df.apply(lambda row: row['Day'].strftime("%Y-%m-%d"), axis=1) # convert period to strf (YYYY-MM-DD)

    return df


def compute_balances(df):
    """
    get the last known value of 'AccountBalance' for each account
    """
    accounts = df["Accounts"].unique()
    balances = {}
    for acc in accounts:
        balances[acc] = df[df["Accounts"] == acc].iloc[0]
    return balances
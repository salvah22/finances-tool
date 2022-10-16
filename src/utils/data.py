import os, sys
import pandas as pd

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

    return df.iloc[::-1] # inverse order for the treeview


def data_prepare(df):
    """
    Function for pre-processing the dataframe
    """
    df['datetime'] = df['Day'] # period is a very bad word for date, use it as datetime
    df['Day'] = df.apply(lambda row: row['Day'].strftime("%Y-%m-%d"), axis=1) # convert period to strf (YYYY-MM-DD)

    return df

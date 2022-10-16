import os, sys
import pandas as pd

def data_loader(path):
    """
    Function for loading inputs with a variety of extensions with the proper pandas read function
    """

    parent, file = os.path.split(data_path)
    file_name, file_ext = os.path.splitext(file)
    if file_ext == '.xlsx':
        df = pd.read_excel(data_path).iloc[::-1]
    elif file_ext == '.csv':
        df = pd.read_csv(data_path).iloc[::-1]
    else:
        sys.exit('data_path extension not supported')

    return df


def data_prepare(df):
    """
    Function for pre-processing the dataframe
    """
    df['datetime'] = df['Period'] # period is a very bad word for date, use it as datetime
    df['Period'] = df.apply(lambda row: row['Period'].strftime("%Y-%m-%d"), axis=1) # convert period to strf (YYYY-MM-DD)
    df.rename(columns={'Period': 'Day'}, inplace=True) # change it to Day

    return df

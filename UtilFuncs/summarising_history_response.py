import pandas as pd
from pandas.io.json import json_normalize

from .get_balance import *

def get_active_rewards_balance(df, file):

    df_history_points = df.loc[df['PointType'].str.contains("Points")].copy()
    df_history_credits = df.loc[df['PointType'].str.contains("Credits")].copy()

    file.write(f"\nTotal points = {df_history_points['BalancePoints'].sum()}")
    file.write(f"\nTotal $ value of points = {df_history_points['JsonExternalData.DOLLAR_VALUE'].sum()}")
    file.write(f"\nTotal credits = {df_history_credits['JsonExternalData.DOLLAR_VALUE'].sum()}")

    total_dollar_val = df['JsonExternalData.DOLLAR_VALUE'].sum()
    file.write(f"\nTotal $ value of rewards available = {total_dollar_val}")

    return {"points_dollar_value": df_history_points['JsonExternalData.DOLLAR_VALUE'].sum(), 
            "credits_dollar_value": df_history_credits['JsonExternalData.DOLLAR_VALUE'].sum(),
            "total_dollar_value": total_dollar_val}


def get_total_dollars_in_account(df):
    total_dollar_val = df['JsonExternalData.DOLLAR_VALUE'].sum()
    return total_dollar_val

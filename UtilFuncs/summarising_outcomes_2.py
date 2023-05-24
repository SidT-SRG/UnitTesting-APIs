import pandas as pd
import numpy as np 
import os
from datetime import datetime

def summarise_outcomes(outcomes, test_id):

    # Prepare the Summary Dataframe
    col_names = ['ActPointId', 'Subtype_code', 'Expiration_date', 'ActivityType', 'CreateDate']

    dyn_col_names = ['PointsAmount', 'BalancePoints',  'Dollar_values']
    for item in outcomes: 
        col_names += [item['Operation']+": "+col_name for col_name in dyn_col_names]

    df_summary = pd.DataFrame(columns=col_names)

    # print(f"The following Data frame will be created {df_summary.columns}")

    # Now take the biggest DF, and use it to create the summary dataframe
    lengths = [len(item['History']) for item in outcomes]
    index_max = lengths.index(max(lengths))

    df_summary[['ActPointId', 'Subtype_code', 'Expiration_date', 'ActivityType', 'CreateDate']] = \
        outcomes[index_max]['History'][['ActPointId', 'JsonExternalData.SubTypeCode', 'JsonExternalData.EXPIRATION_DATE', 'ActivityType', 'CreateDate']]
    
    # Adding all of the info from the other dataframes
    for outcome in outcomes:

        # the dynamic col name = outcome['Operation'] + ": " + col from dyn_col_names
        for col in dyn_col_names:
            column_name = outcome['Operation'] + ": " + col

            if col == 'PointsAmount': source_col = 'PointsAmount'
            elif col == 'BalancePoints': source_col = 'BalancePoints'
            elif col == 'Dollar_values': source_col = 'JsonExternalData.DOLLAR_VALUE'
            else: source_col = col
            
            df_summary[column_name] = pd.merge(df_summary, outcome['History'], on="ActPointId", how="left")[source_col]

    # Adding notes to the summary DF
    # If PointsAmount cols values have changed during the transaction, mark it
    def add_notes(row):
        # Find all elements with "BalancePoints" in the name. 
        # Get the values of those elements into a list
        # compare the list if all elements are equal
        # print (row.index)
        col_names = [name for name in row.index.to_list() if name.endswith('BalancePoints')]
        values_list = row[col_names].to_list()

        if len(values_list) == values_list.count(values_list[0]): return "Equal"
        else: return "Changed"

    df_summary['Notes'] = df_summary.apply(add_notes, axis=1 )

    # Now for the df grouped by Expiration Dates
    # Take all cols from df_summary for 'BalancePoints'
    expiration_cols = ['Expiration_date', 'ActivityType', 'Subtype_code'] + [col for col in df_summary.columns if col.endswith('BalancePoints') ]
    df_expiration = df_summary[expiration_cols].groupby("Expiration_date").first()

    df_expiration.index = pd.to_datetime(df_expiration.index, format='%m/%d/%Y %H:%M:%S %p')
    df_expiration = df_expiration.sort_index()

    return [df_summary, df_expiration]

def create_outcome_directory(customer_name):

    now_timestamp = datetime.now().strftime("%m-%d-%Y-%H-%M-%S")

    # If this is the first iteration, create a new sub-directory in the Outcomes Directory
    dir_path = f'Outcomes/{customer_name}_{now_timestamp}'

    os.makedirs(dir_path)

    print(f"New directory created for test outcomes: {dir_path}")

    return dir_path

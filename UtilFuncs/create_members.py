import requests 
import pandas as pd
import json
from .get_token import *
import datetime as dt 

def create_member_and_assign_rewards():

    # 1. Read the MembersCreate CSV.
    # 2. Create the customer 
    # 3. If adjustments are to be created as points or credits, call add_adjustments

    url_create = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v2/profiles"

    headers = { 'Accept-Language': 'en-US', 
    'Authorization': 'OAuth ' + get_token(),
    'Content-Type': 'application/json',
    'Program-Code': 'REBEL' }

    # Get the member details to be created 
    members_data = pd.read_csv("Resources/MembersCreate.csv")

    # Call the create API

    # Refer to the sample json file 
    dict_json = json.load(open("Resources/member_create.json"))

    print(f"Creating member: {members_data.iloc[0]['FirstName']} {members_data.iloc[0]['LastName']}\n")
    
    dict_json['FirstName'] = members_data.iloc[0]['FirstName']
    dict_json['LastName'] = members_data.iloc[0]['LastName']
    dict_json['EMAILS'][0]['EMAILADDRESS'] = members_data.iloc[0]['FirstName'] + members_data.iloc[0]['LastName'] + "@email.com"
    dict_json['PHONES'][0]['PHONENUMBER'] = ("4" + str(dt.datetime.now().day).zfill(2) + str(dt.datetime.now().month).zfill(2)  
                                            + str(dt.datetime.now().hour).zfill(2) + str(dt.datetime.now().minute).zfill(2) )
    payload = json.dumps(dict_json)

    response = requests.request("POST", url_create, headers=headers, data=payload)

    print({"request":payload, "response": response.text})

    if response.status_code == 200:
        profile_id = response.json()['ProfileId']
        print(f"Member created: {profile_id}")
    else:
        print(response.text)
        return []
    
    url_adjustments = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v1/profiles/" + profile_id + "/adjustments"
    # Refer to the sample json file 
    dict_json_points = json.load(open("Resources/add_adjustments_points.json"))
    dict_json_credits = json.load(open("Resources/add_adjustments_credits.json"))

    
    if members_data.iloc[0]['PT_ADJ'] > 0:
        dict_json_points["NUMPOINTS"] = members_data.iloc[0]['PT_ADJ']
        payload = json.dumps(dict_json_points, default=str)
        requests.request("POST", url_adjustments, headers=headers, data=payload)

    if members_data.iloc[0]['RBAPPCR'] > 0:
        dict_json_credits["ADJUSTMENTREASONCODE"] = 'RBAPPCR'
        dict_json_credits["JSONEXTERNALDATA"]['DOLLAR_VALUE'] = members_data.iloc[0]['RBAPPCR']
        payload = json.dumps(dict_json_credits, default=str)
        requests.request("POST", url_adjustments, headers=headers, data=payload)

    if members_data.iloc[0]['RBMMKTCR'] > 0:
        dict_json_credits["ADJUSTMENTREASONCODE"] = 'RBMMKTCR'
        dict_json_credits["JSONEXTERNALDATA"]['DOLLAR_VALUE'] = members_data.iloc[0]['RBMMKTCR']
        payload = json.dumps(dict_json_credits, default=str)
        requests.request("POST", url_adjustments, headers=headers, data=payload)

    if members_data.iloc[0]['RBMKTCR'] > 0:
        dict_json_credits["ADJUSTMENTREASONCODE"] = 'RBMKTCR'
        dict_json_credits["JSONEXTERNALDATA"]['DOLLAR_VALUE'] = members_data.iloc[0]['RBMKTCR']
        payload = json.dumps(dict_json_credits, default=str)
        requests.request("POST", url_adjustments, headers=headers, data=payload)

    # if members_data.iloc[0]['CRED_10D'] > 0:
    #     dict_json_credits["ADJUSTMENTREASONCODE"] = 'CRED_10D'
    #     dict_json_credits["JSONEXTERNALDATA"]['DOLLAR_VALUE'] = members_data.iloc[0]['CRED_10D']
    #     payload = json.dumps(dict_json_credits, default=str)
    #     requests.request("POST", url_adjustments, headers=headers, data=payload)

    return [profile_id, dict_json['FirstName'] + "_" + dict_json['LastName']]
 

def create_member():

    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v2/profiles"

    headers = { 'Accept-Language': 'en-US', 
    'Authorization': 'OAuth ' + get_token(),
    'Content-Type': 'application/json',
    'Program-Code': 'REBEL' }

    # Refer to the sample json file 
    dict_json = json.load(open("Resources/member_create.json"))

    # Get the member details to be created 
    df_members = pd.read_csv("Resources/MembersCreate.csv")

    outcomes = []

    # Loop at the dataframe and send to EPCL 
    for index in df_members.index:
        print(f"Creating member: {df_members.iloc[index]['FirstName']} {df_members.iloc[index]['LastName']}")
        dict_json['FirstName'] = df_members.iloc[index]['FirstName']
        dict_json['LastName'] = df_members.iloc[index]['LastName']
        dict_json['EMAILS'][0]['EMAILADDRESS'] = df_members.iloc[index]['FirstName'] + df_members.iloc[index]['LastName'] + "@email.com"
        dict_json['PHONES'][0]['PHONENUMBER'] =  str(df_members.iloc[index]['PhoneNumber'])

        payload = json.dumps(dict_json)

        response = requests.request("POST", url, headers=headers, data=payload)

        # outcomes.append{}

        # print(response['ProfileId'])

        print(response.status_code)

        if response.status_code == 200:
            response_dict = response.json()
            outcome = {}
            outcome['CustName'] = response_dict['FirstName'] + " " + response_dict['LastName']
            outcome['ProfileId'] = response_dict['ProfileId']
            outcomes.append(outcome)
        else: 
            print(f"Line 50: {response}")

    if len(outcomes) > 0:
        df = pd.read_csv("Resources/MembersRecords.csv")
        df = df.append(pd.DataFrame(outcomes), ignore_index = True)
        df.to_csv("Resources/MembersRecords.csv", index=False)

    #     df.to_csv("Resources/MembersRecords.csv", index=False)



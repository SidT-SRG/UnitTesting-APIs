import requests
# from get_token import *
from .get_token import *


def get_balance(profile_id):

    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v1/profiles/"+ profile_id + "/points/balance?status=A"

    try: 

        payload={}
        headers = {
        'Accept-Language': 'en-US',
        'Authorization': 'OAuth ' + get_token(),
        'Content-Type': 'application/json',
        'Program-Code': 'REBEL'
        }


        balance_response = requests.request("GET", url, headers=headers, data=payload).json()

        balance = balance_response["PointsBalance"]
        balance_points = list(filter(lambda bal: bal['PointTypeCode'] == 'RBL_POINT', balance))[0]
        balance_credits = list(filter(lambda bal: bal['PointTypeCode'] == 'RBL_CREDIT', balance))[0]
        total_dollar_value = balance_points['JsonExternalData']['DOLLAR_VALUE'] + balance_credits['JsonExternalData']['DOLLAR_VALUE']

        return {"points_dollar_value": balance_points['JsonExternalData']['DOLLAR_VALUE'], 
                "credits_dollar_value": balance_credits['JsonExternalData']['DOLLAR_VALUE'],
                "total_dollar_value": total_dollar_value}

    except ConnectionError as err:

        return []
    
def get_history(profile_id):

    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v1/profiles/"+profile_id+"/points/summary"

    payload={}

    headers = {
    'Accept-Language': 'en-US',
    'Authorization': 'OAuth ' + get_token(),
    'Content-Type': 'application/json',
    'Program-Code': 'REBEL'
    }

    response = requests.request("GET", url, headers=headers, data=payload).json()

    return response

import requests
import json
from .get_token import *
from .services_logs import *

def redeem_rewards(test_id, profile_id, dollarAmount, transaction_id, file):
    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v1/profiles/" + profile_id + "/rewards/catalogs/orders/profilerewards"

    headers = {
    'Accept-Language': 'en-US',
    'Authorization': 'OAuth ' + get_token(),
    'Content-Type': 'application/json',
    'Program-Code': 'REBEL'
    }

    # Refer to the sample json file 
    dict_json = json.load(open("Resources/redeem_rewards.json"))

    dict_json['OrderDetails'][0]['JsonExternalData']['Temp_Ref_No'] = transaction_id
    dict_json['OrderDetails'][0]['JsonExternalData']['TotalDollarValueForBurn'] = dollarAmount

    # Only call redeem rewards if the dollar amount > 0
    if dict_json['OrderDetails'][0]['JsonExternalData']['TotalDollarValueForBurn'] > 0: 

        payload = json.dumps(dict_json, default=str)

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 201:
            redeem_response = response.json()['JsonExternalData']
            file.write("\nRedeem API called successfully")
            file.write("\nBreakup of Rewards being used for the transaction")
            file.write(f"\nPoints burned = ${redeem_response['PointsDollarValue']}")
            for credit_type in redeem_response['CreditsDollarValue']: 
                file.write(f"\n{credit_type['CreditType']} burned = ${credit_type['CreditValue']}")

            # Store the request and response to the services log file  
            store_api_payloads("Redeem", 
                               {
                                "status": "Success",
                                "request": dict_json, 
                                "response": response.json()
                               })

            return redeem_response
        else: 
            print(f'Error in calling Redeem API for TestId: {test_id}\n')
            print(response.status_code)
            print(response.text)

            # Store the request and response to the services log file  
            store_api_payloads("Redeem", 
                               {
                                "status": "Fail",
                                "request": dict_json, 
                                "response": response.text
                               })

            return dict_json['OrderDetails'][0]['JsonExternalData']
        
    else: 

        print(f'Redeem API was not called for TestId: {test_id}\n')

        # Store the request and response to the services log file  
        store_api_payloads("Redeem", 
                            {
                            "status": "Null",
                            "request": {}, 
                            "response": {}
                            })

        return dict_json['OrderDetails'][0]['JsonExternalData']

@dec_store_payloads(api_name="Redeem")
def redeem_rewards_dec(**kwargs):
    # Following parameters will be passed to the Function 
    # test_id, profile_id, dollarAmount, transaction_id, file

    test_id = kwargs.get('test_id')
    profile_id = kwargs.get('profile_id')
    dollarAmount = kwargs.get('dollarAmount')
    transaction_id = kwargs.get('transaction_id')
    file = kwargs.get('file')

    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v1/profiles/" + profile_id + "/rewards/catalogs/orders/profilerewards"

    headers = {
    'Accept-Language': 'en-US',
    'Authorization': 'OAuth ' + get_token(),
    'Content-Type': 'application/json',
    'Program-Code': 'REBEL'
    }

    # Refer to the sample json file 
    dict_json = json.load(open("Resources/redeem_rewards.json"))

    dict_json['OrderDetails'][0]['JsonExternalData']['Temp_Ref_No'] = transaction_id
    dict_json['OrderDetails'][0]['JsonExternalData']['TotalDollarValueForBurn'] = dollarAmount

    # Only call redeem rewards if the dollar amount > 0
    if dict_json['OrderDetails'][0]['JsonExternalData']['TotalDollarValueForBurn'] > 0: 

        payload = json.dumps(dict_json, default=str)

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 201:
            redeem_response = response.json()['JsonExternalData']
            file.write("\nRedeem API called successfully")
            file.write("\nBreakup of Rewards being used for the transaction")
            file.write(f"\nPoints burned = ${redeem_response['PointsDollarValue']}")
            for credit_type in redeem_response['CreditsDollarValue']: 
                file.write(f"\n{credit_type['CreditType']} burned = ${credit_type['CreditValue']}")

            return {"status": "Success", "request": dict_json, "response": response.json()}
        else: 
            print(f'Error in calling Redeem API for TestId: {test_id}\n')
            print(response.status_code)
            print(response.text)

            return {"status": "Fail", "request": dict_json, "response": response.text}

        
    else: 

        print(f'Redeem API was not called for TestId: {test_id}\n')

        return {"status": "Null", "request":{}, "response": {}}


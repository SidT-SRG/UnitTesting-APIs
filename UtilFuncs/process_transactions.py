import requests
import json
import time
from .get_token import *
from .services_logs import *
from datetime import datetime, timedelta

def purchase_transactions(test_id, profile_id, temp_ref_no, redeem_response, order_total, file):

    file.write(f"\n\n---------------------------Submitting the above temporary transaction ID {temp_ref_no}\n")


    transaction_num = int(datetime.now().timestamp())
    # Call the map certs API first
    if map_transaction(profile_id, temp_ref_no, transaction_num):
        file.write(f"\nMap Certs API called. The {temp_ref_no} has been swapped with {transaction_num}\n")

    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v2/transaction"

    headers = {
    'Accept-Language': 'en-US',
    'Authorization': 'OAuth ' + get_token(),
    'Content-Type': 'application/json',
    'Program-Code': 'REBEL'
    }

    # Refer to the sample json file 
    dict_json = json.load(open("Resources/process_transactions.json"))

    # Setting header data 

    dict_json['ProfileId'] = profile_id
    dict_json['TransactionNumber'] = transaction_num
    dict_json['TransactionDateTime'] = datetime.now()
    dict_json['TransactionNetTotal'] = order_total


    # setting value of items based on the order total sent by calling function 
    item_values = split_order_total(order_total)
    for i in range(len(dict_json['TransactionDetails'])):
        dict_json['TransactionDetails'][i]['DollarValueGross'] = item_values[i]
        dict_json['TransactionDetails'][i]['DollarValueNet'] = item_values[i]

    # rewards_dollar_value will be passed from the calling function
    if order_total >  float(redeem_response['TotalDollarValueForBurn']):
        cash_paid = order_total - float(redeem_response['TotalDollarValueForBurn'])
    else:
        cash_paid = 0

    if float(redeem_response['TotalDollarValueForBurn']) > 0:
        points_burnt = redeem_response['PointsDollarValue']
    else: points_burnt = 0

    # TODO For the current version of the API, we are aggregating the credit types 
    if float(redeem_response['TotalDollarValueForBurn']) > 0:
        credits_burnt = sum(item['CreditValue'] for item in redeem_response['CreditsDollarValue'])
    else: credits_burnt = 0


    # dict_json['JsonExternalData']['Temp_Ref_No'] = temp_ref_no
    
    if cash_paid > 0:
        dict_json['Tenders'][0]['TenderAmount'] = cash_paid
    else: 
        dict_json['Tenders'].clear()

    if points_burnt > 0:
        dict_json['Tenders'].append({"TenderCode": "POINTS", "TenderAmount": points_burnt})

    # TODO For the current version of the API, we are aggregating the credit types 
    # if credits_burnt > 0:
    #     dict_json['Tenders'].append({"TenderCode": "CREDITS", "TenderAmount": credits_burnt})

    # New version of the API: pass the individual credit types as payment tenders
    if credits_burnt > 0:
        for credit_record in redeem_response['CreditsDollarValue']:
            dict_json['Tenders'].append({
                'TenderCode': credit_record['CreditType'],
                'TenderAmount': credit_record['CreditValue']
            })

    payload = json.dumps(dict_json, default= str)

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        file.write(f"\n\nTransaction {dict_json['TransactionNumber']} Successfully submitted with the following payment tenders")
        file.write(f"\nFollowing tenders were paid for this transaction")
        for tender_type in dict_json['Tenders']:
            file.write(f"\n{tender_type['TenderCode']} : {tender_type['TenderAmount']}")

        # Store the request and response to the services log file  
        store_api_payloads("SubmitPurchase", 
                            {
                            "status": "Success",
                            "request": dict_json, 
                            "response": response.json()
                            })
        
        # Wait for 2 secs 
        time.sleep(2)

        # Return the json response
        return [dict_json, response.json()]

    else: 
        print(f'Error in calling Submit API for Purchase for TestId: {test_id}\n')
        print()
        print(response.status_code, response.text)

        # Store the request and response to the services log file  
        store_api_payloads("SubmitPurchase", 
                            {
                            "status": "Fail",
                            "request": dict_json, 
                            "response": response.text
                            })
        
        return [dict_json, {}]

# Function to split the order total among items 
def split_order_total(order_total):

    item_val_1 = order_total / 2
    item_val_2 = (order_total - item_val_1) // 2
    item_val_3 = order_total - item_val_1 - item_val_2
    return [round(item_val_1, 2), round(item_val_2, 2), round(item_val_3, 2)]

def map_transaction(profile_id, temp_ref_no, transaction_id):


    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v1/infrastructure/scripts/Swap_SFCC_OrderNo_TempRefNo_StandAlone/invoke"

    payload = json.dumps({
        "ProfileId": profile_id,
        "Temp_Ref_No": temp_ref_no,
        "OrderNumber": transaction_id
    })
    headers = {
        'Accept-Language': 'en-US',
        'Authorization': 'OAuth ' + get_token(),
        'Content-Type': 'application/json',
        'Program-Code': 'REBEL'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        return True
    else: return False

def return_transactions_full(test_id, profile_id, file):

    # Read the service logs for the Submit transaction details 
    service_logs = read_api_payloads()

    # Search Service logs for key Api_name = "SubmitPurchase"
    calls = [item for item in service_logs['service_calls'] if item.get('Api_name') == 'SubmitPurchase' ]
    if len(calls) > 0: submit_call = calls[0]

    original_txn_num = submit_call['payload']['request']['TransactionNumber']
    original_txn_date = submit_call['payload']['request']['TransactionDateTime']
    original_store_code = submit_call['payload']['request']['StoreCode']

    file.write(f"\n\n---------------------------Returning the above transaction ID {original_txn_num} \n")

    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v2/transaction"

    headers = {
        'Accept-Language': 'en-US',
        'Authorization': 'OAuth ' + get_token(),
        'Content-Type': 'application/json',
        'Program-Code': 'REBEL'
    }

    # Refer to the sample json file 
    dict_json = json.load(open("Resources/return_transactions.json"))

    # Setting header data 

    dict_json['ProfileId'] = profile_id
    dict_json['TransactionNumber'] = int(datetime.now().timestamp())
    dict_json['TransactionDateTime'] = datetime.now()
    dict_json['TransactionNetTotal'] = submit_call['payload']['request']['TransactionNetTotal'] * -1
    dict_json['TransactionTypeCode'] = 'RT'

    # Adding the line items
    return_transaction_details = []
    for item in submit_call['payload']['request']['TransactionDetails']:
        return_item = item
        return_item['ItemTransactionTypeCode'] = 'RT'
        return_item['DollarValueGross'] *= -1 
        return_item['DollarValueNet'] *= -1 
        return_item['originalTransactionDateTime'] = original_txn_date
        return_item['originalStoreCode']  = original_store_code
        return_item['originalTransactionNumber'] = original_txn_num
        return_transaction_details.append(return_item)

    dict_json['TransactionDetails'] = return_transaction_details

    dict_json['Tenders'] = []
    for tender in submit_call['payload']['request']['Tenders']:
        tender['TenderAmount'] *= -1
        dict_json['Tenders'].append(tender)

    # Converting to json 
    payload = json.dumps(dict_json, default= str)

    # Posting the request 
    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        file.write(f"\n\nTransaction {original_txn_num} Successfully Returned ")

        file.write(f"\nFollowing tenders were reinstated for this transaction")
        for tender_type in dict_json['Tenders']:
            file.write(f"\n{tender_type['TenderCode']} : {tender_type['TenderAmount']}")

        # Store the request and response to the services log file  
        store_api_payloads("SubmitReturn", 
                            {
                            "status": "Success",
                            "request": dict_json, 
                            "response": response.json()
                            })

        # Return the json response
        return [dict_json, response.json()]

    else: 
        print(f'Error in calling Submit API for Return for TestId: {test_id}\n')
        print()
        print(response.status_code, response.text)

        # Store the request and response to the services log file  
        store_api_payloads("SubmitReturn", 
                            {
                            "status": "Fail",
                            "request": dict_json, 
                            "response": response.text
                            })
        
        return [dict_json, {}]
    
@dec_store_payloads(api_name="SubmitPurchase")
def purchase_transactions_dec(**kwargs):
    # The foll parameters will be passed through the kwargs 
    # test_id, profile_id, temp_ref_no, order_total, file
    
    test_id = kwargs.get('test_id')
    profile_id = kwargs.get('profile_id')
    order_total = float(kwargs.get('order_total')) # type: ignore
    temp_ref_no = kwargs.get('temp_ref_no')
    file = kwargs.get('file')

    # Read the service logs for the rewards redeem details 
    service_logs = read_api_payloads()
    # Search Service logs for key Api_name = "Redeem" and use the last element
    calls = [item for item in service_logs['service_calls'] if item.get('Api_name') == 'Redeem' ]
    if len(calls) > 0: redeem_call_log = calls[-1]

    # Now get the breakdown of rewards and points which will be redeemed
    if redeem_call_log['payload']['status'] != 'Null':
        redeem_response = redeem_call_log['payload']['response']['JsonExternalData']
    else: 
        redeem_response = redeem_call_log['payload']['request']['OrderDetails'][0]['JsonExternalData']

    file.write(f"\n\n---------------------------Submitting the above temporary transaction ID {temp_ref_no}\n")

    # Generating the transaction number 
    transaction_num = int(datetime.now().timestamp())

    # Call the map certs API first - to swap the temp ref num with the transaction number
    if map_transaction(profile_id, temp_ref_no, transaction_num):
        file.write(f"\nMap Certs API called. The {temp_ref_no} has been swapped with {transaction_num}\n")

    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v2/transaction"

    headers = {
    'Accept-Language': 'en-US',
    'Authorization': 'OAuth ' + get_token(),
    'Content-Type': 'application/json',
    'Program-Code': 'REBEL'
    }

    # Refer to the sample json file 
    dict_json = json.load(open("Resources/process_transactions.json"))

    # Setting header data 

    transaction_time = datetime.today() - timedelta(days=2, hours=12)
    dict_json['ProfileId'] = profile_id
    dict_json['TransactionNumber'] = transaction_num
    # dict_json['TransactionDateTime'] = datetime.now()
    dict_json['TransactionDateTime'] = transaction_time
    dict_json['TransactionNetTotal'] = order_total


    # setting value of items based on the order total sent by calling function 
    item_values = split_order_total(order_total)
    for i in range(len(dict_json['TransactionDetails'])):
        dict_json['TransactionDetails'][i]['DollarValueGross'] = item_values[i]
        dict_json['TransactionDetails'][i]['DollarValueNet'] = item_values[i]

    # rewards_dollar_value will be passed from the calling function
    if order_total >  float(redeem_response['TotalDollarValueForBurn']):
        cash_paid = order_total - float(redeem_response['TotalDollarValueForBurn'])
    else:
        cash_paid = 0

    if float(redeem_response['TotalDollarValueForBurn']) > 0:
        points_burnt = redeem_response['PointsDollarValue']
    else: points_burnt = 0

    # Are credits being used for the purchase?  
    if float(redeem_response['TotalDollarValueForBurn']) > 0:
        credits_burnt = sum(item['CreditValue'] for item in redeem_response['CreditsDollarValue'])
    else: credits_burnt = 0

    if cash_paid > 0:
        dict_json['Tenders'][0]['TenderAmount'] = cash_paid
    else: 
        dict_json['Tenders'].clear()

    if points_burnt > 0:
        dict_json['Tenders'].append({"TenderCode": "POINTS", "TenderAmount": points_burnt})

    # New version of the API: pass the individual credit types as payment tenders
    if credits_burnt > 0:
        for credit_record in redeem_response['CreditsDollarValue']:
            dict_json['Tenders'].append({
                'TenderCode': credit_record['CreditType'],
                'TenderAmount': credit_record['CreditValue']
            })

    payload = json.dumps(dict_json, default= str)

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        file.write(f"\n\nTransaction {dict_json['TransactionNumber']} Successfully submitted with the following payment tenders")
        file.write(f"\nFollowing tenders were paid for this transaction")
        for tender_type in dict_json['Tenders']:
            file.write(f"\n{tender_type['TenderCode']} : {tender_type['TenderAmount']}")

        # Wait for 2 secs - In case we are calling Return after this, it ends up with the same transaction number otherwise!
        time.sleep(2)

        # Return the json response
        return {"status": "Success", "request": dict_json, "response": response.json()}

    else: 
        print(f'Error in calling Submit API for Purchase for TestId: {test_id}\n')
        print()
        print(response.status_code, response.text)

        return {"status": "Fail", "request":dict_json, "response": response.text}

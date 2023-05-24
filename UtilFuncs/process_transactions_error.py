import requests
import json
import time 
from .get_token import *
from .services_logs import *
from datetime import datetime
from .process_transactions import *
from .return_transactions import *

# Function to simulate an error situation where the original purchase wasnt submitted to EPCL 
def purchase_transactions_error(test_id, profile_id, temp_ref_no, redeem_response, order_total, file):

    # file.write(f"\n\n---------------------------Submitting the above temporary transaction ID {temp_ref_no}\n")


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

    # Wait for 2 secs 
    time.sleep(2)

    # we are not calling the actual submitAPI here, so there wont be any response 
    # Store the request and response to the services log file  
    store_api_payloads("SubmitPurchase_Error", 
                        {
                        "status": "Success",
                        "request": dict_json, 
                        "response": {}
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

def submit_transaction_after_return(test_id, profile_id, temp_ref_no, redeem_response, order_total, file):

    file.write(f"\n\n---------------------------Submitting the purchase transaction\n")

    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v2/transaction"

    headers = {
    'Accept-Language': 'en-US',
    'Authorization': 'OAuth ' + get_token(),
    'Content-Type': 'application/json',
    'Program-Code': 'REBEL'
    }

    # Read the service logs for the Submit transaction details 
    service_logs = read_api_payloads()

    # Search Service logs for key Api_name = "SubmitPurchase"
    calls = [item for item in service_logs['service_calls'] if item.get('Api_name') == 'SubmitPurchase_Error' ]
    if len(calls) > 0: submit_call = calls[0]

    dict_json   = submit_call['payload']['request']

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

def return_transactions_partial_error(test_id, profile_id, items_to_return, file):

    # Read the service logs for the Submit transaction details 
    service_logs = read_api_payloads()

    # Search Service logs for key Api_name = "SubmitPurchase_Error"
    calls = [item for item in service_logs['service_calls'] if item.get('Api_name') == 'SubmitPurchase_Error' ]
    if len(calls) > 0: submit_call = calls[0]

    original_txn_num = submit_call['payload']['request']['TransactionNumber']
    original_txn_date = submit_call['payload']['request']['TransactionDateTime']
    original_store_code = submit_call['payload']['request']['StoreCode']

    file.write(f"\n\n---------------------------Returning the above transaction ID {original_txn_num} \n")

    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v2/transaction"
    # url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v2/transaction/validate"

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
    dict_json['TransactionNetTotal'] = 0
    dict_json['TransactionTypeCode'] = 'RT'

    # Adding the line items
    return_transaction_details = []
    item_no = -1
    for item in submit_call['payload']['request']['TransactionDetails']:
        item_no += 1

        if item_no not in items_to_return: 
            continue

        return_item = item
        return_item['ItemTransactionTypeCode'] = 'RT'
        return_item['DollarValueGross'] *= -1 
        return_item['DollarValueNet'] *= -1 
        return_item['originalTransactionDateTime'] = original_txn_date
        return_item['originalStoreCode']  = original_store_code
        return_item['originalTransactionNumber'] = original_txn_num
        return_transaction_details.append(return_item)

        dict_json['TransactionNetTotal'] += return_item['DollarValueNet']

    dict_json['TransactionDetails'] = return_transaction_details

    # Now to get the tenders to be refunded
    dict_json['Tenders'] = []
    
    outstanding_amount = dict_json['TransactionNetTotal'] * -1
    
    cash_paid = get_payment_made_by_tender_type(submit_call['payload']['request']['Tenders'], "CASH")
    points_paid = get_payment_made_by_tender_type(submit_call['payload']['request']['Tenders'], "POINTS")
    mkt_paid = get_payment_made_by_tender_type(submit_call['payload']['request']['Tenders'], "RBMKTCR")
    man_mkt_paid = get_payment_made_by_tender_type(submit_call['payload']['request']['Tenders'], "RBMMKTCR")
    app_paid = get_payment_made_by_tender_type(submit_call['payload']['request']['Tenders'], "RBAPPCR")

    # Calculate the tenders to be refunded
    tenders_list = []

    [tenders_list, outstanding_amount] = calculate_refunds(tenders_list, outstanding_amount, cash_paid, "CASH")
    [tenders_list, outstanding_amount] = calculate_refunds(tenders_list, outstanding_amount, points_paid, "POINTS")
    [tenders_list, outstanding_amount] = calculate_refunds(tenders_list, outstanding_amount, mkt_paid, "RBMKTCR")
    [tenders_list, outstanding_amount] = calculate_refunds(tenders_list, outstanding_amount, man_mkt_paid, "RBMMKTCR")
    [tenders_list, outstanding_amount] = calculate_refunds(tenders_list, outstanding_amount, app_paid, "RBAPPCR")

    dict_json['Tenders'] = tenders_list

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

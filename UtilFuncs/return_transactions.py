import requests
import json
from .get_token import *
from .services_logs import *
from datetime import datetime

def return_transactions_partial(test_id, profile_id, items_to_return, file):

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
    
def get_payment_made_by_tender_type(tenders_list, tender_type):

    payment = [tender['TenderAmount'] for tender in tenders_list if tender['TenderCode'] == tender_type ]
    if (len(payment) > 0): 
        return payment[0]
    else: 
        return 0
    
def calculate_refunds(tenders_list, outstanding_amount, payment_amount, tender_type):

    if outstanding_amount > 0 and payment_amount > 0:
        if payment_amount >= outstanding_amount: 
            tenders_list.append({"TenderCode": tender_type, "TenderAmount": outstanding_amount * -1 })
            outstanding_amount = 0 
        else: 
            tenders_list.append({"TenderCode": tender_type, "TenderAmount": payment_amount * -1 })
            outstanding_amount -= payment_amount

    return [tenders_list, outstanding_amount]
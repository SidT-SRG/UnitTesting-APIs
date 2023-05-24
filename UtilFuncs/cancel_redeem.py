import requests
import json

from .get_token import *

def cancel_redeem(profile_id, transaction_id, file):

    url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v1/infrastructure/scripts/Cancel_TransCertificate_StandAlone/invoke"

    payload = json.dumps({
    "ProfileId": profile_id,
    "Temp_Ref_No": transaction_id
    })

    headers = {
    'Accept-Language': 'en-US',
    'Authorization': 'OAuth ' + get_token(),
    'Content-Type': 'application/json',
    'Program-Code': 'REBEL'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        file.write("\nCancel API Called successfully")
    else:
        file.write("\nCancel API failed")
        print(response.text)

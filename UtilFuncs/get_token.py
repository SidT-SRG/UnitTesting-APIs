import requests

access_token = ''

url = "https://u1srgl-pveapi.epsilonagilityloyalty.com/api/v1/authorization/tokens"

def get_token():

  global access_token
    
  if access_token != '':
    return access_token
  
  payload='grant_type=password&username=SRG_MULESOFT_SERVICE_USER&password=79u_Lfj_KK&response_type=token'
  # payload='grant_type=password&username=SIDDHESH.TUNGARE@SUPERRETAILGROUP.COM&password=AsdfQwer!234&response_type=token'

  headers = {
  'Content-Type': 'application/x-www-form-urlencoded',
  'Accept-Language': 'en-US',
  'Program-Code': 'REBEL',
  'Authorization': 'Basic U1JHX01VTEVTT0ZUX1dFQkFQSUtFWTpTM2N1cmUuMTIz'
  }

  # response = requests.request("POST", url, headers=headers, data=payload).json()
  response = requests.request("POST", url, headers=headers, data=payload)

  if response.status_code >= 400:
    print(f"Error in authentication. Error message:\n{response.json()}")
  else: 
    response_dict = response.json()

  access_token = response_dict['access_token']
  # print(f"Access Token generated: {access_token}")

  return access_token
  

    



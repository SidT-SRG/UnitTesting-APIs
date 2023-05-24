import json

file_name = ""

def create_new_file(path):
    global file_name 

    with open(path, "w") as file:
        json.dump({"service_calls": []}, file, default=str)
        file.close()
        file_name = path

def read_api_payloads():

    global file_name

    return  json.load(open(file_name))


def store_api_payloads(api_name, payload={}):
    global file_name
    dict_json = json.load(open(file_name))

    dict_json['service_calls'].append({"Api_name": api_name, 
                      "payload": payload})

    with open(file_name, "w") as file:
        json.dump(dict_json, file, default=str)
        file.close()

    pass

# Defining the above Function as Function Decorator 
def dec_store_payloads(api_name):
    global file_name
    print(file_name)

    def decorator(func):

        print(api_name)

        def wrapper(**kwargs):

            payload = func(**kwargs)

            # Writing to the service_logs file     
            dict_json = json.load(open(file_name))

            dict_json['service_calls'].append({"Api_name": api_name, 
                            "payload": payload})

            with open(file_name, "w") as file:
                json.dump(dict_json, file, default=str)
                file.close()

            return payload
        
        return wrapper
    
    return decorator

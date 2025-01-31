import os 


def get_devices_from_env_vriables():
    print("checking env variables for device configs")
    count = 1
    running = True
    devices = list()
    while (running):
        
        name= os.environ.get(f"DEV_NAME_{count}", None)
        if name == None:
            break
        url= os.environ.get(f"DEV_URL_{count}", None)
        api_key= os.environ.get(f"DEV_API_KEY_{count}", None)
        # checking if all keys are present is done when devices are added to the mux        

        # got all the vars for this round to lets add them
        devices.append({"name": name, "url": url, "api_key": api_key})

        count += 1

    return devices

from syncthing_multi_server.syncthing import Syncthing

""" class that gathers the info from all the configured syncthing devices """


class Syncthing_mux:
    # type hint
    device_list : [Syncthing]

    def __init__(self):
        self.device_list = []

    def add_syncthing_device_to_mux(self, name, url, api_key):
        # cleanup the url
        if url.startswith("http") == False:
            url = f"http://{url}"
        # if no port is set we add the default syncthing ui port
        # but when a url starts with https, we expect the user to know what they are doing
        # and they will likely not be using the default webui port anymore
        if ':' not in url[-7:] and not url.startswith("https"):
            url = f"{url}:8384"
        if url.endswith("/") == False:
            url= f"{url}/"
        device = Syncthing(name, url, api_key)
        # check if the device is up
        try:
            device.healthcheck()
        except Exception as ex:
            # not perfect that we catch just every type off exception but for now it will do.
            print (f"error while connecting with device: {name}, this indicates that the protocol, ip or port is wrong, this test does not use the api key")
            print(ex)
            #this device errored so we don't add it to the list return to finish the function
            return 
        # ping and also check if we have a working api key
        try:
            device.ping()
        except Exception as ex:
            print (f"error while connecting with device: {name} using its api key this indicates that the api key is wrong. ")
            # print(ex.with_traceback())
            #this device errored so we don't add it to the list return to finish the function
            return 
        self.device_list.append(device)
    
    def add_list_off_devices_dicts(self, list):
        for device in list:
            # check if all params are present
            if "name" not in device:
                print("device added that is missing a name")
                return
            name = device["name"]
            if "url" not in device:
                print(f"device {name} is missing url")
                return
            url =  device["url"]
            if "api_key" not in device:
                print(f"device {name} is missing an api_key")
                return
            api_key = device["api_key"]
            self.add_syncthing_device_to_mux(name= name,
                                            api_key= api_key,
                                            url=url)

    def del_none(self, d):
        # cleanup dict to remove keys that have None values
        for key, value in list(d.items()):
            if value is None:
                del d[key]
            elif isinstance(value, dict):
                self.del_none(value)
        return d  

    def get_full_device_list_status(self):
        all_statuses = list()
        for device in self.device_list:
            status = device.get_syncthing_device_status()
            # remvoing all keys that have null values
            
            all_statuses.append(self.del_none(status.__dict__))
        return all_statuses

    def get_list_off_devices_that_are_not_fully_synced(self) -> []:
        full_status = self.get_full_device_list_status()
        unfinished_syncs = []
        for device in full_status:
            if device["sync_completion"] < 100 :
                unfinished_syncs.append({"name": device["name"], "sync_completion" : device["sync_completion"]})
        return unfinished_syncs


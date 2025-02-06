from syncthing_multi_server.syncthing import Syncthing
import time

""" class that gathers the info from all the configured syncthing devices """


class Syncthing_mux:
    # type hint
    device_list : [Syncthing]

    def __init__(self):
        self.device_list = []
        self.offline_device_list = []
        self.offline_last_checked = time.time()

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
            print(f"{name} connection error : {ex}")
            self.add_device_to_the_offline_list(device=device)
            #this device errored so we don't add it to the list return to finish the function
            return 
        # ping and also check if we have a working api key
        try:
            device.ping()
        except Exception as ex:
            print (f"error while connecting with device: {name} using its api key this indicates that the api key is wrong. ")
            self.add_device_to_the_offline_list(device=device)
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

    def add_device_to_the_offline_list(self, device:Syncthing):
        # sounds stupid to keep a device that is not online.
        # but some clients are not online 24/7 ex. mobile devices, personal computors, unstable connections, ...
        # so we keep these devices so that we can try to reach them in the future 
        
        self.offline_device_list.append(device)
    def move_device_from_online_to_offline(self, device:Syncthing):
        #print(f"moving {device} to the offline list)")
        self.add_device_to_the_offline_list(device)
        self.device_list.remove(device)

    def retest_the_offline_devices(self):
        # remember when we last did this
        self.offline_last_checked = time.time()

        # we try if any of the offline devices is up now
        for device in self.offline_device_list:
            # we pop the device from the list as we are positive and assume that it will be online now.
            # pop 0 to take from the top as we always add to the bottom.
            # otherwise if all these are still offline we could check the last one in this list for the amount off offline devices in the list.
            dev = self.offline_device_list.pop(0)
            self.add_syncthing_device_to_mux(name=dev.name,url=dev.baseurl, api_key=dev.api_key)

    def get_how_long_ago_we_checked_offline_devices_seconds(self) -> int:
        return int(time.time() - self.offline_last_checked)
    def get_how_long_ago_we_checked_offline_devices_in_human(self) -> str:
        sec = self.get_how_long_ago_we_checked_offline_devices_seconds()
        if sec < 60:
            return f"{sec} second{'s' if sec > 1 else ''} ago"
        elif sec < 3600:  # Less than an hour
            min = round(sec / 60)
            return f"{min} minute{'s' if min > 1 else ''} ago"
        elif sec < 86400:  # Less than a day
            hours = round(sec / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = round(sec / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"



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
            try:
                status = device.get_syncthing_device_status()
                # removing all keys that have null values
                all_statuses.append(self.del_none(status.__dict__))
            except Exception as ex: # todo don't just catch all exceptions
                self.move_device_from_online_to_offline(device=device)


        return all_statuses

    def get_list_off_devices_that_are_not_fully_synced(self) -> []:
        full_status = self.get_full_device_list_status()
        unfinished_syncs = []
        for device in full_status:
            if device["sync_completion"] < 100 :
                unfinished_syncs.append({"name": device["name"], "sync_completion" : device["sync_completion"]})
        return unfinished_syncs


    def get_total_device_count(self) -> int:
        return len(self.offline_device_list) + len(self.device_list)

    def get_offline_device_count(self) -> int:
        return len(self.offline_device_list)
    def get_offline_device_names(self) -> [str]:
        name_list =  []
        for device in self.offline_device_list:
            name_list.append(device.name)
        return name_list
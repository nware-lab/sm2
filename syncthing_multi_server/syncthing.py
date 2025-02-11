import requests
import json
import os

'''
Setup call timeout based on environment variable if requested by the user
'''
timeout_default_value = 0.5
timeout = timeout_default_value
timeout_env_var_name="DEVICE_API_TIMEOUT_SEC"

if timeout_env_var_name in os.environ:
    try: 
        input=os.environ.get(timeout_env_var_name, timeout_default_value)
        timeout = float(input)
        print(f"{timeout_env_var_name} set to {timeout} seconds")
    except ValueError: 
        print(f"error casting requested {timeout_env_var_name} value got : {input} \nreverting back to default value 0.5 s")
        # likely an unneeded line but it will one be executed on startup and keeps this readable 
        timeout=timeout_default_value


class Syncthing_device_status:
    """ Class for carrying the status off a syncthing device """
    def __init__(self, instance_name, url):
        self.name = instance_name
        self.url = url
        self.sync_completion= None
        self.errors= None
        self.local_changed_files = None
        self.folder_count = 0
        self.device_count = 0




class Syncthing:
    """ Class representing a Syncthing device """
    folder_list_simplified = None
    folder_list = None

    def __init__(self,name, url, api_key):
        self.name = name
        self.baseurl = url
        self.api_key= api_key
        

    def get_syncthing_device_status(self) -> dict:
        device_status = Syncthing_device_status(instance_name=self.name, url=self.baseurl)
        device_status.errors = self.system_errors()
        device_status.sync_completion = self.system_sync_completion_level()["completion"]
        device_status.local_changed_files = self.list_folders_that_have_local_changes()
        device_status.folder_count = len(self.list_folders_simplified())
        device_status.device_count = len(self.list_devices())
        device_status.pending_folders = self.list_pending_folders_labels_for_device()
        device_status.pending_devices = self.list_pending_devices_labels_for_device()

        
        return device_status

    def _request_builder(self,path:str):
        # helper function to keep the rest of the code cleaner
        # short timeout because if we in 0.5 sec don't have our response something is wrong and we aren't going to wait forever
        # users asked for a configurable timeout, which we get from env variable: default value is 0.5s
        return requests.get(self.baseurl + path, headers = {'Authorization':  f'Bearer {self.api_key}'},timeout=timeout)

    def healthcheck(self):
        # https://docs.syncthing.net/rest/noauth-health-get.html
        r = self._request_builder('rest/noauth/health')
        return r.json()

    def ping(self):
        # https://docs.syncthing.net/rest/system-ping-get.html
        r = self._request_builder('rest/system/ping')
        if r.status_code != 200:
            raise ConnectionError(f"Could not connect to client {self.name}")
        return r.json()

    def list_folders(self):
        # https://docs.syncthing.net/rest/config.html#rest-config-folders-rest-config-devices
        r = self._request_builder('rest/config/folders')
        self.folder_list =r.json()
        return r.json()

    def list_folders_simplified(self):
        js = self.list_folders()
        
        folder_dict = dict()
        # only keep the keys we are interested in
        for item in js:
            folder_dict[item["label"]]= item["id"]
        self.folder_list_simplified = folder_dict
        return folder_dict


    def system_status(self):
        # https://docs.syncthing.net/rest/system-status-get.html
        r = self._request_builder('rest/system/status')
        return r.json()

    def system_errors(self):
        # https://docs.syncthing.net/rest/folder-errors-get.html
        r = self._request_builder('rest/system/error')
        if r.json() == {'errors': None}:
            return None
        return r.json()

    def system_logs(self):
        # https://docs.syncthing.net/rest/system-log-get.html
        r = self._request_builder('rest/system/log')
        return r.json()

    def system_sync_completion_level(self):
        # https://docs.syncthing.net/rest/db-completion-get.html
        r = self._request_builder(f'rest/db/completion')
        return r.json()

    def list_folders_that_are_incomplete(self):
        folders_with_non_complete_status = list()
        for folder in self.folder_list:
            result = self.list_missing_files_for_folder(folder_id=folder["id"])
        return result
            
    def list_devices(self):
        # https://docs.syncthing.net/rest/config.html#rest-config-folders-rest-config-devices
        r = self._request_builder("rest/config/devices")
        return r.json()


    def list_local_changes_for_folder(self, folder_id):
        # https://docs.syncthing.net/rest/db-localchanged-get.html
        
        # only check for non paused folders
        r = self._request_builder(f"rest/db/localchanged?folder={folder_id}")
        # print(f"folderid = {folder_id} \n response\n{r}")
        return r.json()

    def list_folders_that_have_local_changes(self):
        folders_with_local_changes = dict()
        if self.folder_list == None:
            self.list_folders()
        if len(self.folder_list) == 0:
            return None
        for folder in self.folder_list:
            if folder["type"] == "receiveonly" and folder["paused"] == False :
                
                # print(folder["id"] + " " + folder["label"])
                result = self.list_local_changes_for_folder(folder_id=folder["id"])
                # print(result)
                result_count =len(result["files"])
                if result_count > 0:
                    folders_with_local_changes[folder["label"]] = result_count
            else:
                # print(f"skipping {folder['id']} as its either not reeive only or is paused")
                pass
        
        if len(folders_with_local_changes) == 0:
            return None

        return folders_with_local_changes

    def list_pending_folders_for_device(self):
        r = self._request_builder("rest/cluster/pending/folders")

        return r.json()
    def list_pending_devices_for_device(self):
        r = self._request_builder("rest/cluster/pending/devices")
        return r.json()
    
    def list_pending_devices_labels_for_device(self):
        js = self.list_pending_devices_for_device()
        # get jsust the labels from the js
        label_list = []
        for device in js:
            label_list.append(js[device]["name"])
        return label_list


    def list_pending_folders_labels_for_device(self):
        js = self.list_pending_folders_for_device()
         # get jsust the labels from the js
        label_list = []
        for folder in js:
            if folder != "{}":
                # this feels like it could be done more efficient
                # TODO make this less iffy
                inter_folder = js[folder]["offeredBy"]
                device_name = list(inter_folder.keys())[0]
                label_list.append(inter_folder[device_name]["label"])

        return label_list
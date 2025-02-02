
from syncthing_multi_server.syncthing_muxer import Syncthing_mux
import json
from flask import Flask, jsonify, render_template
from env_reader import get_devices_from_env_vriables
import os.path


app = Flask(__name__)

mux = Syncthing_mux()

# check if there is a device list file
device_list_file_path = "device_list.json"
if os.path.exists(device_list_file_path):
    with open (device_list_file_path, "r") as file:
        devices = json.load(file)
    # add the devices from the json to the mux
    mux.add_list_off_devices_dicts(devices)
# add the devices from the env variable to the mux
mux.add_list_off_devices_dicts(get_devices_from_env_vriables())
print("sm² is loaded and ready")



@app.route("/")
def root():
    # basic html page with an overview off all the configured devices
    mux.retest_the_offline_devices()
    res = mux.get_full_device_list_status()
    offline_device_count = mux.get_offline_device_count()
    offine_device_names = mux.get_offline_device_names()
    return render_template('index.html', status = res, offline_count= offline_device_count, offline_names = offine_device_names)

@app.route("/retry_offline_devices")
def retry_offline_devices():
    res = mux.retest_the_offline_devices()
    return jsonify(res)

@app.route("/api/status")
def api_status():
    # return the status off all devices to as a json result
    return mux.get_full_device_list_status()

@app.route("/api/devices_not_fully_synced")
def api_devices_not_fully_synced():
    return mux.get_list_off_devices_that_are_not_fully_synced()

@app.route("/ping")
def ping():
    return jsonify("ello")

if __name__ == '__main__':
	app.run()    





# send "metrics" home on startup
def report_data():
    if os.environ.get("DISABLE_REPORTING", False).lower() != "true":
        import time, socket, requests
        data= {}
        data["ts"]= time.time()
        #aware that this will only give contianer id but thats what i want.
        data["hostname"] = socket.gethostname()
        # amount off devices
        data["dev"]= mux.get_total_device_count()
        # app version
        data["v"]= os.environ.get("SM2_VERSION", "0")
        try:
            requests.post("https://private-sm2monitor.onrender.com/report",json=data)
        except Exception:
            print("stats reporting failed")
        print(f"sent home this data for statistics: {data}")
report_data()
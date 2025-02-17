
from syncthing_multi_server.syncthing_muxer import Syncthing_mux
import json
from flask import Flask, jsonify, render_template, request
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
    # default refresh only the known online devices
    # but if we get a ?load=full we recheck the offline devices
    retest_offline_devices_if_requested()
    if request.args.get("thread") == "no":
        res = mux.get_full_device_list_status()
    else:
        res = mux.get_full_device_list_status_threaded()
    offline_device_count = mux.get_offline_device_count()
    offine_device_names = mux.get_offline_device_names()
    last_checked_offline = mux.get_how_long_ago_we_checked_offline_devices_in_human()
    return render_template('index.html', status = res, offline_count= offline_device_count, offline_names = offine_device_names, last_checked_offline = last_checked_offline)

@app.route("/retry_offline_devices")
def retry_offline_devices():
    res = mux.retest_the_offline_devices()
    return jsonify(res)

@app.route("/api/status")
def api_status():
    retest_offline_devices_if_requested()

    # return the status off all devices to as a json result
    return mux.get_full_device_list_status()

@app.route("/api/devices_not_fully_synced")
def api_devices_not_fully_synced():
    return mux.get_list_off_devices_that_are_not_fully_synced()

@app.route("/ping")
def ping():
    return jsonify("ello")


# send "metrics" home on startup
# no reason to trigger this yourself
# Please don't spam this. :) thanks
@app.route("/report")
def report_data():
    # some cool 'magic' which allows us to run this function before the app is fully loaded
    with app.app_context():
        if os.environ.get("DISABLE_REPORTING", "false").lower() != "true":
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
            return jsonify(data)
        return jsonify("user requested no reporting so we will not")


def retest_offline_devices_if_requested():
    if request.args.get("load") == "full":
        mux.retest_the_offline_devices()

def remove_cron_jobs_if_requested():
    print("cleaning cron jobs if requested")
    if os.environ.get("DISABLE_REPORTING", "false").lower() == "true":
        # the user requested no reporting so we will delete the cron job that would trigger that reporting.
        report_path = "/etc/periodic/daily/report"
        if os.path.exists("/etc/periodic/daily/report"):
            print("deleting daily report cron script")
            os.remove(report_path)
        else:
            print(f"{report_path} not found or already deleted")
    if os.environ.get("DISABLE_OFFLINE_DEVICE_BACKGROUND_RETRY", "false").lower() == "true":
        # user asked for no background retry off the offline devices
        retry_offline_devices_path = "/etc/periodic/hourly/retry_offline_devices"
        if os.path.exists(retry_offline_devices_path):
            print("deleting hourly offline device retry cron")
            os.remove(retry_offline_devices_path)
        else:
            print(f"{retry_offline_devices_path} not found or already deleted")


def start_cron_daemon():
    import subprocess
    subprocess.run("crond")
    print("Background cron started")

if __name__ == '__main__':
    app.run()
    
report_data()
remove_cron_jobs_if_requested()
start_cron_daemon()
print("sm² is loaded and ready")
print("-----------------------------")
print(" ######  ##     ##  #######  ")
print("##    ## ###   ### ##     ## ")
print("##       #### ####        ## ")
print(" ######  ## ### ##  #######  ")
print("      ## ##     ## ##        ")
print("##    ## ##     ## ##        ")
print(" ######  ##     ## ######### ")
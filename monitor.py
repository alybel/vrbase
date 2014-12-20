#! /usr/bin/python -u

import glob
import vr_main
import time

def account_name_from_path(path = ""):
    return path.split("/")[1].split(".")[0]

def run_monitoring():
    fl = glob.glob("stdout/*.out")
    for fn in fl:
        with open(fn, "r") as f:
            for line in f:
                if "error" in line.lower():
                    account_name = account_name_from_path(fn)
                    #Only print something if a process exists. Otherwise produce no printout"
                    result = vr_main.stop_account(account_name, auto_call = True)
                    if result:
                        with open("monitoring_logfile.txt","a") as logfile:
                            logfile.write("%s;%s;%s" % (str(time.ctime(time.time())), "accountkilled", account_name))

if __name__ == "__main__":
    while True:
        run_monitoring()
        time.sleep(10)

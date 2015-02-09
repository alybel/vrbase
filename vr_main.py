import glob
import subprocess
import os
import sys
import psutil

def get_accounts():
    """
    extract all existing account names in the accounts folder
    """
    al = glob.glob("accounts/*/")
    return [x.split("/")[1] for x in al]

def start_account(account = ""):
    if os.path.isfile("accounts/%s/.lock" % account):
        print "Account", account, "is locked. is already running?"
        return False
    os.chdir("bluebird/")
    print "starting account", account
    outfile = "../stdout/%s.out" % account
    with open(outfile, "w") as f:
        subprocess.Popen(["python", "bb_main.py", "-l%s" % account], stdout = f, stderr = f)
    os.chdir("../")
    subprocess.call(["touch","accounts/%s/.lock" % account])
    return True

def stop_account(account = "", auto_call = False):
    procname = "bb_main.py"
    subprocess.call(["rm","accounts/%s/.lock" % account])
    print "lockfile removed"
    for proc in psutil.process_iter():
        try:
            cmdl = proc.cmdline()
            if procname in cmdl and account in cmdl[-1]:
                print "killing", proc.cmdline()
                psutil.Process(proc.pid).kill()
                return True
        except psutil.AccessDenied:
            #these are root processes that cannot be looked into
            pass
    if not auto_call:
        print "no running proccess for account", account, "could be found"
    return False

def run_vr():
    accounts = get_accounts()
    for account in accounts:
        start_account(account)
    return

def remove_all_lockfiles():
    accounts = get_accounts()
    for account in accounts:
        subprocess.call(["rm","accounts/%s/.lock" % account])
    print "all lockfiles removed"


if __name__ == "__main__":
    if not len(sys.argv) == 3:
        print "usage: vr_main.py <action> <selection>"
        print "Example1: vr_main.py start all"
        print "Example2: vr_main.py stop all"
        print "Example3: vr_main.py start BlueBirdBoost"
        print "Example4: vr_main.py restart BlueBirdBoost"
        sys.exit()
    arg1 = sys.argv[1]
    arg2 = sys.argv[2]
    if arg1 == "start":
        if arg2 == "all":
            run_vr()
        else:
            start_account(arg2)
    elif arg1 == "stop":
        if arg2 == "all":
            subprocess.call(["killall", "bb_main.py"])
            subprocess.call(["killall", "bb_main.py"])
            remove_all_lockfiles()
        else:
            stop_account(arg2)
            print "second kill for security -- very bad practice"
            stop_account(arg2)
    elif arg1 == "restart":
        if arg2 == "all":
            subprocess.call(["killall", "bb_main.py"])
            subprocess.call(["killall", "bb_main.py"])
            remove_all_lockfiles()
            run_vr()
        else:
            stop_account(arg2)
            start_account(arg2)


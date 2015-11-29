#!/usr/bin/env python
# this shebang uses the python that is currently activated
import glob
import subprocess
import os
import sys
import psutil
sys.path.append('bluebird')
import load_config as lc



def get_accounts():
    """
    extract all existing account names in the accounts folder
    """
    al = glob.glob("accounts/*/")
    return [x.split("/")[1] for x in al]


def start_account(account=""):
    vr_base = os.getenv('VR_BASE')
    if os.path.isfile("%s/accounts/%s/.lock" % (vr_base, account)):
        print "Account", account, "is locked. is already running?"
        return False
    os.chdir("%s/bluebird/" % vr_base)
    print "starting account", account
    lc.check_if_folder_exists_or_create(account)
    outfile = "%s/stdout/%s.out" % (vr_base, account)
    with open(outfile, "w") as f:
        subprocess.Popen("python bb_main.py -l%s" % account, stdout=f, stderr=f, shell=True)
    os.chdir("../")
    subprocess.call(["touch", "%s/accounts/%s/.lock" % (vr_base, account)])
    return True


def stop_account(account="", auto_call=False, remove_lock=True):
    vr_base = os.getenv('VR_BASE')
    procname = "bb_main.py"
    if remove_lock:
        subprocess.call(["rm", "%s/accounts/%s/.lock" % (vr_base, account)])
        print "lockfile removed"
    for proc in psutil.process_iter():
        try:
            cmdl = proc.cmdline()
            if len(cmdl) < 2:
                continue
            if procname in cmdl[-2] and account in cmdl[-1]:
                print "killing", proc.cmdline()
                psutil.Process(proc.pid).kill()
                return True
        except psutil.AccessDenied:
            # these are root processes that cannot be looked into
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
    vr_base = os.getenv('VR_BASE')
    accounts = get_accounts()
    for account in accounts:
        subprocess.call(["rm", "%s/accounts/%s/.lock" % (vr_base, account)])
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
            raise DeprecationWarning
            subprocess.call(["killall", "bb_main.py"])
            subprocess.call(["killall", "bb_main.py"])
            remove_all_lockfiles()
        else:
            stop_account(arg2)
            print "second kill for security -- very bad practice"
            stop_account(arg2)
    elif arg1 == "restart":
        if arg2 == "all":
            raise DeprecationWarning
            subprocess.call(["killall", "bb_main.py"])
            subprocess.call(["killall", "bb_main.py"])
            remove_all_lockfiles()
            run_vr()
        else:
            stop_account(arg2)
            start_account(arg2)

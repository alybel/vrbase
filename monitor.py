import glob
import vr_main
import time
import smtplib

def account_name_from_path(path = ""):
    return path.split("/")[1].split(".")[0]

def err_exception(line = ""):
    """
    list the exceptions even if there is an error in the line
    """
    if "414" in line:
        return True
    if "ValueError" in line:
        return True
    if "TypeError" in line:
        return True

def run_monitoring():
    fl = glob.glob("stdout/*.out")
    for fn in fl:
        with open(fn, "r") as f:
            for line in f:
                if "error" in line.lower():
                    if err_exception(line):
                        continue
                    account_name = account_name_from_path(fn)
                    #Only print something if a process exists. Otherwise produce no printout"
                    result = vr_main.stop_account(account_name, auto_call = True)
                    if result:
                        send_report(account_name)
                        with open("monitoring_logfile.txt","a") as logfile:
                            logfile.write("%s;%s;%s \n" % (str(time.ctime(time.time())), "accountkilled", account_name))




def send_report(account_name):
    return 
    sender = "a.beck@valureach.com"
    receivers = ["a.beck@valureach.com"]

    message = """From: Valureach Warning System
To: Alexander Beck
Subject: Account killed: %s

empty

""" % account_name

    try:
        smtpObj = smtplib.SMTP('smtp.valureach.com', 25)
        smtpObj.sendmail(sender, receivers, message)
    except SMTPException:
        pass



if __name__ == "__main__":
    while True:
        time.sleep(10)
        run_monitoring()


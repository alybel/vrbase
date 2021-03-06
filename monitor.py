import glob
import vr_main
import time
import smtplib
import datetime
import logging
import os

vr_base = os.getenv('VR_BASE')

logging.basicConfig(filename='%s/../logs/monitor_log.txt' % vr_base, maxBytes=20000000, level=logging.INFO)


def account_name_from_path(path=""):
    return path.split("/")[-1].split(".")[0]


def err_exception(line=""):
    """
    list the exceptions even if there is an error in the line
    """
    if "414" in line:
        return True
    if "ValueError" in line:
        return True
    if "TypeError" in line:
        return True
    if '503' in line:
        # twitter service overloaded, try again later
        return True


def run_monitoring():
    fl = glob.glob("/home/vr/valureach_ops/stdout/*.out")
    for fn in fl:
        with open(fn, "r") as f:
            for line in f:
                if "error" in line.lower():
                    if err_exception(line):
                        continue
                    account_name = account_name_from_path(fn)
                    # Only print something if a process exists. Otherwise produce no printout"
                    result = vr_main.stop_account(account_name, auto_call=True, remove_lock=False)
                    if result:
                        send_report(account_name)
                    logging.info("%s;%s;%s;%s \n" % (str(time.ctime(time.time())), "accountkilled by monitor.py", account_name, line))


def send_report(account_name):
    sender = "support@valureach.com"
    receivers = ["valureach@gmail.com"]

    message = """From: Valureach Warning System
    To: Alexander Beck
    Subject: Account killed: %s

    empty

    """ % account_name

    try:
        smtpObj = smtplib.SMTP('smtp.valureach.com', 25)
        smtpObj.sendmail(sender, receivers, message)
    except smtplib.SMTPException:
        logging.error('email could not be sent')
    except:
        logging.error('email could not be sent')

if __name__ == "__main__":
    while True:
        time.sleep(10)
        run_monitoring()
        logging.info('heartbeat %s' % datetime.datetime.now())

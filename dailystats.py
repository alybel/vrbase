#! /usr/bin/python -u

import glob
import time
import datetime
import sys
sys.path.append("/home/alex/valureach_ops/accounts/valureach")
import config as cfg
sys.path.append("/home/alex/valureach_ops/bluebird")
import bblib as bbl
import os
import smtplib

bbl.set_cfg(cfg)
auth,api= bbl.connect_app_to_twitter()

def get_logfile_list():
    return glob.glob("/home/alex/valureach_ops/accounts/*/*.log")

def get_reports_list():
    return glob.glob("/home/alex/valureach_ops/accounts/*/last_report.txt")

def all_stats():
    account_list = get_logfile_list()
    for account in account_list:
        get_report(account)
    send_report()

def send_report():
    return True
    sender = "a.beck@valureach.com"
    receivers = ["a.beck@valureach.com", "al.d.beck@gmail.com"]

    message = """From: Valureach Reporting System
To: Alexander Beck
Subject: Latest Report 

Here begins the report

"""

    reports = get_reports_list()
    for report in reports:
        with open(report, "r") as f:
            for line in f:
                message += line
            message += "\n \n \n"
    try:
        smtpObj = smtplib.SMTP('smtp.valureach.com', 25)
        smtpObj.sendmail(sender, receivers, message)
    except SMTPException:
        pass

def get_account_path(logfile_path= ""):
    return "/".join(logfile_path.split("/")[:-1])

def get_account_name(logfile_path= ""):
    return logfile_path.split("/")[-2]

def get_report(logfile_path):
    n_follows = 0
    n_status_updates = 0
    n_retweets = 0
    n_favorites = 0
    account_name = get_account_name(logfile_path)
    n_followers, last_status = get_user_information(account_name)
    time_stamp = str(time.ctime(time.time()))
    with open(logfile_path,"r") as f:
        for line in f:
            line = line.lower()
            today = str(datetime.date.today())
            #Only look at reports from today
            if not today in line: 
                continue
            if "$$followinguser" in line:
                n_follows += 1
            if "$$retweet" in line:
                n_retweets += 1
            if "$$statusupdate" in line:
                n_status_updates += 1
            if "$$favorite" in line:
                n_favorites += 1
    with open("%s/last_report.txt" % get_account_path(logfile_path),"w") as report:
        report.write("Account Name: %s \n" % account_name)
        report.write("Time Stamp: %s \n" % time_stamp)
        report.write("N follows: %d \n" % n_follows)
        report.write("N status updates: %d \n" % n_status_updates)
        report.write("N retweets: %d \n" % n_retweets)
        report.write("N favorites: %d \n" % n_favorites)
        report.write("N_followers: %d \n" % n_followers)
        report.write("Last status: %s \n" % bbl.ru(last_status))
    contreportname = "%s/report.csv" %get_account_path(logfile_path)
    if not os.path.isfile(contreportname):
        fh = open(contreportname, "w") 
        hl = ["account_name", "time_stamp", "n_follows_tdy", "n_status_updates_tdy", "n_retweets_tdy", "n_favorites_tdy", "n_followers", "last_update"]
        fh.write(";".join(hl) + "\n")
        fh.close()
    with open(contreportname, "a") as contreport:
        lv = [account_name, time_stamp, n_follows, n_status_updates, n_retweets, n_favorites, n_followers, bbl.ru(last_status)]
        contreport.write(";".join([str(x) for x in lv])+"\n")

def get_user_information(account = "AlexanderD_Beck"):
    usr = api.get_user(account)
    followers = usr.followers_count
    last_status = usr.status.text
    time.sleep(2)
    return followers, last_status
    

if __name__ == "__main__":
    all_stats()

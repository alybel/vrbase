__author__ = 'alex'
import vr_main
import collections
import os.path
import time

def growth_from_report_file(account = ""):
    print account
    d = collections.defaultdict(int)
    fn = "accounts/%s/report.csv"%account
    if not os.path.isfile(fn):return
    headline = True
    with open(fn,'r') as f:
        for line in f:
            if headline:
                headline = False
                continue

            try:
                line = line.split(';')
                if not line[0] == account: continue
                datevec = line[1].split(" ")
                date = " ".join([datevec[1], datevec[2], datevec[-1]])
                d[date] = line[6]
                q = time.strptime(date, '%b %d %y')
                print q
            except Exception, e:
                print line
                print e
    print d

def follower_growth():
    accounts = vr_main.get_accounts()
    for account in accounts:
        growth_from_report_file(account)

def run_stats():
    follower_growth()

if __name__ == '__main__':
    #growth_from_report_file("BlueBirdBoost")
    run_stats()
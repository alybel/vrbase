__author__ = 'alex'
import vr_main
import collections
import os.path

def growth_from_report_file(account = ""):
    print account
    d = collections.defaultdict(int)
    fn = "accounts/%s/report.csv"%account
    if not os.path.isfile(fn):return
    with open(fn,'r') as f:
        for line in f:
            try:
                line = line.split(';')
                date = " ".join(line[1].split(" ")[1:3])
                d[date] = line[6]
            except:
                pass
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
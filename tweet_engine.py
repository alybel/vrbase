#! /usr/bin/python -u

import glob
import sys
import os.path
import time
valureach_ops_path = "/home/alex/valureach_ops"
sys.path.append("%s/bluebird" % valureach_ops_path)
import bblib as bbl


import multiprocessing as mp
from multiprocessing import Pool

def tweet_account(account_name=""):
    print "starting", account_name
    account_path = "%s/accounts/%s/" % (valureach_ops_path, account_name)
    if not os.path.isfile("%s/tweet.py" % account_path):
        return False
    #Check for correct frequency
    freq = 120 * 60
    logfile = "%stweet_engine.log"%account_path
    sys.path.append(account_path)
    import config as cfg
    bbl.set_cfg(cfg)
    auth, api = bbl.connect_app_to_twitter()
    import tweet
    if os.path.isfile(logfile):
        with open(logfile, 'r') as f:
            for line in f:
                if "tweetid" in line:
                    tweet_id  = line.strip("\n").split(":")[1]
                    try:
                        api.destroy_status(tweet_id)
                        print account_name,"tweet destroyed in ramping up", tweet_id
                    except:
                        pass
        f = open(logfile, "w")
        f.close()
    while True:
        res = api.update_status(tweet.tweet)
        with open(logfile, 'a') as f:
            f.write("tweetid:%d\n"%res.id)
        print account_name, "tweeted:", tweet.tweet
        time.sleep(freq/2)
        api.destroy_status(res.id)
        print account_name, "status deleted"
        with open(logfile, 'a') as f:
            f.write("deleted-tweetid:%d\n"%res.id)
        time.sleep(freq/2)

def all_accounts():
    pool = mp.Pool(processes=2)
    try:
        results = [pool.apply(tweet_account, args=(x,)) for x in ["BlueBirdBoost", "sweetorangesoc"]]
    except KeyboardInterrupt:
        sys.exit()
    except Exception,e:
        print e
        
    print(results)

if __name__ == "__main__":
    all_accounts()
    #tweet_account("BlueBirdBoost")

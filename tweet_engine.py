#! /usr/bin/python -u

import glob
import sys
import os.path
import time
valureach_ops_path = "/home/alex/valureach_ops"
sys.path.append("%s/bluebird" % valureach_ops_path)
import bblib as bbl
import random

import multiprocessing as mp
from multiprocessing import Pool

def tweet_account(account_name=""):
    print "starting", account_name
    account_path = "%s/accounts/%s/" % (valureach_ops_path, account_name)
    if not os.path.isfile("%s/tweet.py" % account_path):
        return False
    sys.path.append(account_path)
    import config as cfg
    import tweet
    bbl.set_cfg(cfg)
    auth, api = bbl.connect_app_to_twitter()
    #Check for correct frequency
    freq = tweet.freq * 60
    logfile = "%stweet_engine.log"%account_path
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
        #reset the logfile
        f = open(logfile, "w")
        f.close()
    while True:
        #Tweet own tweets
        sel_tweet = random.choice(tweet.tweets)
        print "selected tweet:", sel_tweet
        res = api.update_status(sel_tweet)
        with open(logfile, 'a') as f:
            f.write("tweetid:%d\n"%res.id)
        print account_name, "tweeted:", sel_tweet
        #time.sleep(freq/3)
        #retweet tweets from friended accounts
        for account in tweet.watch_account:
            print "seeking for tweets to retweet in", account
            apath = "%s/accounts/%s/" % (valureach_ops_path, account)
            lf = "%stweet_engine.log"%apath
            if not os.path.isfile(lf):
                continue
            with open(lf,'r') as f2:
                for line in f2:
                    print line
                    if "tweetid" in line:
                        tweet_id  = line.strip("\n").split(":")[1]
                        print "tweet_id", tweet_id
                        try:
                            api.retweet(tweet_id)
                            print "retweeted", tweet_id
                        except Exception,e:
                            print e
                            print "retweet not carried out", tweet_id
        print "reached sleep point"
        time.sleep(freq/3)
        #remove own tweets
        api.destroy_status(res.id)
        print account_name, "status deleted"
        with open(logfile, 'a') as f:
            f.write("deleted-tweetiid:%d\n"%res.id)
        time.sleep(freq/3)
        f = open(logfile, "w")
        f.close()

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
    #all_accounts()
    args = sys.argv
    if not len(args) == 2:
        print "usage: tweet_engine.py <account_name>"
        sys.exit()
    print "starting for account", args[1]
    tweet_account(args[1])

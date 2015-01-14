#! /usr/bin/python -u

import glob
import sys
import os.path
import time
valureach_ops_path = "/home/alex/PycharmProjects"
sys.path.append("%s/bluebird" % valureach_ops_path)
import bblib as bbl




def tweet_account(account_name=""):
    account_path = "%s/accounts/%s/" % (valureach_ops_path, account_name)
    if not os.path.isfile("%s/tweet.py" % account_path):
        return False
    #Check for correct frequency
    freq = 120 * 60
    if True:
        sys.path.append(account_path)
        import config as cfg
        bbl.set_cfg(cfg)
        auth, api = bbl.connect_app_to_twitter()
        import tweet
        res = api.update_status(tweet.tweet)
        time.sleep(freq/2)
        api.destroy_status(res.id)
        time.sleep(freq/2)




if __name__ == "__main__":
    #all_accounts()
    tweet_account("BlueBirdBoost")
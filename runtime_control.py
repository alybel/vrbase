__author__ = 'alex'

from sqlalchemy import schema, types, create_engine, orm
import datetime
import time
import sys

connection_string = 'mysql+pymysql://alex:1ba12D1Kg84@62.75.156.31:3306/onboarding'
eng = create_engine(connection_string)
states = {}
md = schema.MetaData(bind=eng, reflect=True)
Session = orm.sessionmaker(bind=eng, autoflush=True, autocommit=False,
                           expire_on_commit=True)
s = Session()
gs = md.tables['GeneralSettings']

# Account Control Functions

def pr(str=''):
    print datetime.datetime.now(), str


def start_account(account):
    pr('start account %s' % account['twittername'])
    pass


def stop_account(account):
    pr('stop account %s' % account['twittername'])
    pass


def restart_account(account):
    pr('restart account %s' % account['twittername'])
    pass


def result_to_accounts(result):
    accounts = {}
    for entry in result:
        if entry[0] is None: continue
        accounts[entry[0]] = {
            'onoff': entry[1],
            'restart_needed': entry[2] if entry[2] is not None else 0,
            'paused_until': entry[3] if entry[3] is not None else datetime.datetime(2000, 1, 1),
            'twittername': entry[0],
        }
    return accounts


def pull_data():
    result = s.query(gs.c.own_twittername, gs.c.onoff, gs.c.restart_needed, gs.c.paused_until).all()
    accounts = result_to_accounts(result)
    return accounts


def is_paused(account):
    if datetime.date.today() < account['paused_until'].date():
        return True
    return False


def check_if_off_or_switch_off(account):
    # ToDo check is still needed
    stop_account(account)
    pass


def is_set_on(account):
    if account['onoff'] == 1:
        return True
    return False


def is_set_to_restart(account):
    if account['restart_needed'] == 1:
        return True
    return False


def update_states(account):
    states[account['twittername']] = account['onoff']


def state_changed(account):
    if states[account['twittername']] != account['onoff']:
        return True
    return False


def put_state_in_action(account):
    if account['onoff'] == 1:
        start_account(account)
    else:
        stop_account(account)


while True:
    accounts = pull_data()
    for account_name in accounts:
        account = accounts[account_name]
        # Case 1: Account is put on pause. There are no exceptions to this. Check if account is paused otherwise
        # pause it.
        if is_paused(account):
            check_if_off_or_switch_off(account)
            continue
        # Case 2: fill_states_with_new_accounts and put their state in action
        if account_name not in states:
            put_state_in_action(account)
            update_states(account)
        # Case 3: account is set to ON and restart is needed, then restart account
        if is_set_on(account) and is_set_to_restart(account):
            restart_account(account)
        # Case 4: State has changed, apply change.
        if state_changed(account):
            put_state_in_action(account)
            update_states(account)
        pr('heartbeat')
        sys.stdout.flush()
    time.sleep(10)

from sqlalchemy import schema, types, create_engine, orm
import datetime
import time
import sys
import subprocess

__author__ = 'alex'

connection_string = 'mysql+pymysql://root:valuereachdb@localhost:3306/valuereach'
eng = create_engine(connection_string)
states = {}
md = schema.MetaData(bind=eng, reflect=True)
Session = orm.sessionmaker(bind=eng, autoflush=True, autocommit=False,
                           expire_on_commit=True)

gs = md.tables['GeneralSettings']

# Account Control Functions

def pr(out=None):
    print datetime.datetime.now(), out

def start_or_restart_account(account=None):
    pr('restart account %s' % account['twittername'])
    subprocess.call(['python', '/home/vr/valureach_ops/vr_main.py', 'restart', '%s' % account['twittername']])

def stop_account(account):
    pr('stop account %s' % account['twittername'])
    subprocess.call(['python', '/home/vr/valureach_ops/vr_main.py', 'stop', '%s' % account['twittername']])

def result_to_accounts(result):
    accounts = {}
    for entry in result:
        if entry[0] is None:
            continue
        accounts[entry[0]] = {
            'onoff': entry[1],
            'restart_needed': entry[2] if entry[2] is not None else 0,
            'paused_until': entry[3] if entry[3] is not None else datetime.datetime(2000, 1, 1),
            'twittername': entry[0],
        }
    return accounts

def pull_data():
    s = Session()
    result = s.query(gs.c.own_twittername, gs.c.onoff, gs.c.restart_needed, gs.c.paused_until).all()
    accounts = result_to_accounts(result)
    s.close()
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
        start_or_restart_account()account(account)
    else:
        stop_account(account)


def reset_restart_needed(account):
    """reset the reset_needed information in the database"""
    session = Session()
    session.execute('UPDATE GeneralSettings SET restart_needed = 0 where own_twittername="%s";'
                    % account['twittername'])
    session.commit()
    return True


while True:
    accounts = pull_data()
    for account_name in accounts:
        acc = accounts[account_name]
        # Case 1: Account is put on pause. There are no exceptions to this. Check if account is paused otherwise
        # pause it.
        if is_paused(acc):
            check_if_off_or_switch_off(acc)
            continue
        # Case 2: fill_states_with_new_accounts and put their state in action
        if account_name not in states:
            put_state_in_action(acc)
            update_states(acc)
        # Case 3: account is set to ON and restart is needed, then restart account
        if is_set_on(acc) and is_set_to_restart(acc):
            start_or_restart_account(acc)
            reset_restart_needed(acc)
        # Case 4: State has changed, apply change.
        if state_changed(acc):
            put_state_in_action(acc)
            update_states(acc)
    pr('heartbeat')
    sys.stdout.flush()
    time.sleep(60)

#ToDo Write into LogFile not Stdout
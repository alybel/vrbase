__author__ = 'alex'

from sqlalchemy import schema, types, create_engine, orm

import time

states = {}

def pull_data():
    pass

def is_paused(account):
    pass

def check_if_off_or_switch_off(account):
    pass

def put_state_in_action(account):
    pass

def is_set_on(account):
    pass

def is_set_to_restart(account):
    pass

def update_states(account):
    pass

def restart_account(account):
    pass

def state_changed(account):
    pass

def change_state(account):
    pass

while True:
    time.sleep(10)
    data = pull_data()
    accounts = data.get_accounts()
    for account in accounts:
        # Case 1: Account is put on pause. There are no exceptions to this. Check if account is paused otherwise
        # pause it.
        if is_paused(account):
            check_if_off_or_switch_off(account)
            continue
        # Case 2: fill_states_with_new_accounts and put their state in action
        if account not in states:
            put_state_in_action(account)
            update_states(account)
        # Case 3: account is set to ON and restart is needed, then restart account
        if is_set_on(account) and is_set_to_restart(account):
            restart_account(account)
        # Case 4: State has changed, apply change.
        if state_changed(account):
            change_state(account)

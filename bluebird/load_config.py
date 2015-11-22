from sqlalchemy import schema, types, create_engine, orm
import os.path
import os

def load_config(own_twittername=''):
    connection_string = 'mysql+pymysql://root:valuereachdb@localhost:3306/valuereach'
    eng = create_engine(connection_string)
    md = schema.MetaData(bind=eng, reflect=True)
    Session = orm.sessionmaker(bind=eng, autoflush=True, autocommit=False,
                               expire_on_commit=True)
    s = Session()

    gs = md.tables['GeneralSettings']
    bl = md.tables['BlacklistKeywords']
    wl = md.tables['WhitelistKeywords']
    na = md.tables['NeverUnfollowAccounts']

    class cfg:
        pass

    cfg = cfg()

    row = s.query(gs).filter(gs.c.own_twittername == own_twittername).first()
    row = dict(zip(row.keys(), row))
    for key in row:
        setattr(cfg, key, row[key])

    # Whitelist
    cfg.keywords = dict(s.query(wl.c.keyword, wl.c.weight).filter(wl.c.fk_user_id == cfg.fk_user_id).all())

    # Blacklist
    cfg.blacklist = dict(s.query(bl.c.keyword, bl.c.weight).filter(bl.c.fk_user_id == cfg.fk_user_id).all())

    # Accounts never unfollow
    accounts_never_delete = s.query(na.c.accountname).filter(na.c.fk_user_id == cfg.fk_user_id).all()
    cfg.accounts_never_delete = [x[0] for x in accounts_never_delete]

    cfg.verbose = False
    cfg.languages = ['en', 'de']
    cfg.locations = []
    cfg.preambles = []
    cfg.hashtags = []
    cfg.activity_frequency = 15
    cfg.number_hashtags = 3
    cfg.status_update_prob = 0.5
    print 'loaded config from database'
    return cfg

def check_if_folder_exists_or_create(cfg):
    directory = '../accounts/%s' % cfg.own_twittername
    if not os.path.exists(directory):
        os.makedirs(directory)

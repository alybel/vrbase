from sqlalchemy import schema, types, create_engine, orm


def load_config(own_twittername=''):
    connection_string = 'mysql+mysqldb://valureach:1ba12D1Kg84@62.75.156.31:3306/onboarding'
    eng = create_engine(connection_string)
    md = schema.MetaData(bind=eng, reflect=True)
    Session = orm.sessionmaker(bind=eng, autoflush=True, autocommit=False,
                               expire_on_commit=True)
    s = Session()

    gs = md.tables['GeneralSettings']
    bl = md.tables['BlacklistKeywords']
    wl = md.tables['WhitelistKeywords']

    class cfg:
        pass

    cfg = cfg()

    row = s.query(gs).filter(gs.c.own_twittername == own_twittername).first()
    row = dict(zip(row.keys(), row))
    for key in row:
        setattr(cfg, key, row[key])

    cfg.keywords = dict(s.query(wl.c.keyword, wl.c.weight).filter(wl.c.email == cfg.email).all())
    cfg.blacklist = dict(s.query(bl.c.keyword, bl.c.weight).filter(bl.c.email == cfg.email).all())
    cfg.verbose = False
    cfg.languages = ['en', 'de']
    cfg.locations = []
    cfg.preambles = []
    cfg.hashtags = []
    print 'loaded config from database'
    return cfg

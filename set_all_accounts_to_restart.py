from sqlalchemy import create_engine

connection_string = 'mysql+pymysql://root:valuereachdb@localhost:3306/valuereach?charset=utf8mb4'
eng = create_engine(connection_string, convert_unicode=True)
eng.execute('update GeneralSettings set restart_needed=1;')

# rename stdout files
# remove all lock files

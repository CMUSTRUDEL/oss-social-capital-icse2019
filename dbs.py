from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
import os

num_proc = 30
pswd = os.environ["SQLPW"]
url = "mysql://sophie:"+pswd+"@localhost/ghtorrent-2018-03?charset=utf8mb4"
engine = create_engine(url, pool_size = num_proc, pool_recycle = 3600)
Session = sessionmaker(bind = engine)
metadata = MetaData(engine)
commits = Table("commits", metadata, autoload=True)
projects = Table("projects", metadata, autoload=True)
conns = engine.connect()
session = Session()


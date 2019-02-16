from datetime import datetime
from math import floor
from multiprocessing import *
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from utils import *
import logging
import numpy as np
import os
import pandas as pd
import pickle
import pymysql
import random
import time

# setup
get_fork = False 
logging.basicConfig()
num_proc = 25
pswd = os.environ["SQLPW"]
id_file_name = "data/uid.list"
f = open(id_file_name)
uids = [int(l.strip()) for l in f.readlines()]
f.close()

# load contributors' projects
f = open("dict/contr_projs.dict")
cont_projs_dict = pickle.load(f)
f.close()

f = open("dict/proj_contrs_count.dict")
proj_contrs_count = pickle.load(f)
f.close()

f = open("dict/root_forks.dict")
root_forks = pickle.load(f)
f.close()

f = open("dict/fork_root.dict")
fork_root = pickle.load(f)
f.close()

f = open("dict/alias_map_b.dict")
alias_map = pickle.load(f)
f.close()

f = open("dict/reverse_alias_map_b.dict")
re_alias = pickle.load(f)
f.close()

f = open("data/big_repos.list")
big_repos = [int(l.strip()) for l in f.readlines()]
f.close()

langs = ["JavaScript", "Java", "Python", "CSS", "PHP", "Ruby", "C++", 
  "C", "Shell", "C#", "Objective-C", "R", "VimL", "Go", "Perl", 
  "CoffeeScript", "Tex", "Swift", "Scala", "Emacs Lisp", "Haskell", 
  "Lua", "Clojure", "Matlab", "Arduino", "Groovy", "Puppet", "Rust", 
  "PowerShell", "Erlang", "Visual Basic", "Processing", "Assembly", "Other"]
print "Done setting up"

url = "mysql://sophie:"+pswd+"@localhost/ghtorrent-2018-03?charset=utf8mb4"
engine = create_engine(url, pool_size = num_proc, pool_recycle = 3600)
Session = sessionmaker(bind = engine)
metadata = MetaData(engine)
commits = Table('commits', metadata, autoload=True)
projects = Table('projects', metadata, autoload=True)
followers = Table("followers", metadata, autoload=True)
pull_requests = Table("pull_requests", metadata, autoload=True)
pull_request_history = Table("pull_request_history", metadata, autoload=True)
conns = engine.connect()
session = Session()

url = "mysql://sophie:"+pswd+"@localhost/namsor?charset=utf8mb4"
engine_n = create_engine(url, pool_size = num_proc, pool_recycle = 3600)
Session_n = sessionmaker(bind = engine_n)
metadata_n = MetaData(engine_n)
namsor = Table("ght_namsor_s", metadata_n, autoload=True)
conns_n = engine_n.connect()
session_n = Session_n()

#for p_index, p in enumerate(pids):
def get_info(u_id):
  # if we don't have the user's project list, it means that this author has only
  # contributed to large projects which we do not include in our model.
  if u_id not in cont_projs_dict:
    return []

  proc_id = os.getpid()
  u_p_dicts = []
  if u_id in alias_map:
    aliases = tuple(alias_map[u_id])
  else:
    aliases = tuple([u_id])
  u_projs = cont_projs_dict[u_id]

  act_wins = [win for win in range(36) if len(u_projs[win]) > 0]
  for act_win in act_wins:
    for p_id in u_projs[act_win]:
      if p_id in big_repos or p_id == -1:
        continue
      # no need to get root, we already stored roots
      # get the list of forks
      forks = tuple(root_forks[p_id])

      # count the number of commits made by this contributor to this project
      [begin, end] = windows[act_win].split("_")
      begin = datetime.strptime(begin, "%Y-%m-%d %H:%M:%S")
      end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")

      r = session.query(commits).filter(commits.c.author_id.in_(aliases),
                                    commits.c.project_id.in_(forks),
                                    commits.c.created_at >= begin,
                                    commits.c.created_at <= end)
      user_num_commits_win = len(r.all())

      # count the number of commits made to this project
      r = session.query(commits).filter(commits.c.project_id.in_(forks),
                                    commits.c.created_at >= begin,
                                    commits.c.created_at <= end)

      num_commits_win = len(r.all())
      if num_commits_win == 0:
        continue

      u_p_dict = {}
      u_p_dict["window_num"] = act_win + 1
      u_p_dict["u_id"] = u_id
      u_p_dict["p_id"] = p_id

      # u is owner
      r = session.query(projects.c.owner_id).filter(projects.c.id == p_id)
      owner_id = get_merged_id(re_alias, r.first().owner_id)
      if owner_id == u_id:
        u_p_dict["u_is_owner"] = 1
      else:
        u_p_dict["u_is_owner"] = 0

      # owner's gender
      r = session_n.query(namsor).filter(namsor.c.id == owner_id).first()
      owner_gender = 0
      if r is None:
        owner_gender = 0
      else:
        if r.gender == "Female":
          owner_gender = 1
        elif r.gender == "male":
          owner_gender = -1
        else:
          owner_gender = 0
      u_p_dict["owner_gender"] = owner_gender

      # has owner listed company
      owner_company = 0
      if r is None:
        owner_company = 0
      elif r.company is None:
        owner_company = 0
      else:
        owner_company = 1
      u_p_dict["owner_company"] = owner_company

      # u is major
      if user_num_commits_win * 1.0 / num_commits_win > 0.05:
        u_p_dict["u_is_major"] = 1
      else:
        u_p_dict["u_is_major"] = 0

      # u has merge PR access
      # get the list of PRs
      pr_r = (session.query(pull_requests, pull_request_history)
       .filter(pull_requests.c.base_repo_id == p_id,
                pull_requests.c.id == pull_request_history.c.pull_request_id,
                pull_request_history.c.created_at >= begin,
                pull_request_history.c.created_at <= end,
                pull_request_history.c.action == "merged",
                pull_request_history.c.actor_id == u_id)).all()
      if len(pr_r) == 0:
        u_p_dict["u_pr_merge"] = 0
      else:
        u_p_dict["u_pr_merge"] = 1

      u_p_dicts.append(u_p_dict)
      #print proc_id, u_id, u_p_dict, datetime.now()
  #results = pd.concat([results, pd.DataFrame(p_dicts)]) 
  #session.commit()
  conns.close()
  return u_p_dicts

pool = Pool(num_proc)
results = pool.map(get_info, uids)
result_f = open("result_f_user", "wb")
pickle.dump(results, result_f)
result_f.close()
'''

for u in uids:
  get_info(u)

'''
results = [dict_item for dict_lists in results for dict_item in dict_lists]
results = pd.DataFrame(results)
results.to_csv("data/results_user_proj.csv", index = False, encoding = "utf-8")

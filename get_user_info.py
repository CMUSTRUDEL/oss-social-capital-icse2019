from datetime import datetime
from math import floor
from multiprocessing import *
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
#from utils import *
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

f = open("dict/alias_map_b.dict")
alias_map = pickle.load(f)
f.close()

f = open("dict/reverse_alias_map_b.dict")
re_alias = pickle.load(f)
f.close()

begin = datetime.strptime("2008-01-01", "%Y-%m-%d")
end = datetime.strptime("2016-12-31", "%Y-%m-%d")
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
conns = engine.connect()
session = Session()

url = "mysql://sophie:"+pswd+"@localhost/namsor?charset=utf8mb4"
engine_n = create_engine(url, pool_size = num_proc, pool_recycle = 3600)
Session_n = sessionmaker(bind = engine_n)
metadata_n = MetaData(engine_n)
namsor = Table("ght_namsor_s", metadata_n, autoload=True)
conns_n = engine_n.connect()
session_n = Session_n()

gender_f = open("data/gender.csv")
line = gender_f.readline()
line = gender_f.readline()
user_genders = {}
while len(line):
  parts = line.strip().split(",")
  user_genders[parts[0]] = parts[-1]
  line = gender_f.readline()
gender_f.close()

def get_merged_id(re_alias, aid):
  if aid in re_alias:
    return re_alias[aid]
  return aid

failed = open("u_failed", "w")
out = open("u_out", "w")
#for p_index, p in enumerate(pids):
def get_info(u):
  print u
  # if we don't have the user's project list, it means that this author has only
  # contributed to large projects which we do not include in our model.
  if u not in cont_projs_dict:
    return []

  proc_id = os.getpid()
  u_dicts = []
  # get all aliases:
  try:
    aliases = tuple(alias_map[u])
  except:
    aliases = tuple([u])


  # get user basic info
  r = session_n.query(namsor).filter(namsor.c.id == u)
  u_info = r.first()

  u_email = u_info.email
  u_login = u_info.login
  try:
    u_gender = user_genders[str(u)]
    if u_gender == 1:
      u_gender = "Female"
    elif u_gender == -1:
      u_gender = "Male"
  except:
    u_gender = u_info.gender

  # get user ages and active ages, niche width
  u_projs = cont_projs_dict[u]
  first_win = next((i for i, x in enumerate(u_projs) if x), None)

  # get followers
  follower_win = []
  for i in range(36):
    follower_win.append(set())

  r = session.query(followers).filter(followers.c.user_id.in_(aliases),
                                      followers.c.created_at >= begin,
                                      followers.c.created_at <= end)

  for rr in r.all():
    win = floor((rr.created_at.month-1)/3+1)+ (rr.created_at.year-2008)*4
    win = int(win)
  
    merge_id = get_merged_id(re_alias, rr.follower_id)
    if merge_id == 6059:
      continue # this id is for wrong email settings
    follower_win[int(win)-1].add(merge_id)
  follower_count = [len(fol) for fol in follower_win]

  # number of commits
  commits_win = [0] * 36 
  '''
  for i in range(36):
    commits_win[i] = 0 
  '''
  r = session.query(commits).filter(commits.c.author_id.in_(aliases),
                                commits.c.created_at >= begin,
                                commits.c.created_at <= end)

  for rr in r.all():
    win = floor((rr.created_at.month-1)/3+1)+ (rr.created_at.year-2008)*4
    win = int(win)
    commits_win[int(win)-1] += 1

  u_languages = set()
  act_wins = [win for win in range(36) if len(u_projs[win]) > 0]
  for win_index, act_win in enumerate(act_wins):
    u_dict = {}
    u_dict["window_num"] = act_win + 1
    u_dict["u_id"] = u
    u_dict["u_email"] = u_email
    u_dict["u_gender"] = u_gender
    u_dict["u_login"] = u_login
    u_dict["u_age"] = act_win - first_win
    u_dict["u_windows_active_to_date"] = win_index # 0 indexed
    u_dict["u_followers"] = sum(follower_count[:act_win+1])
    u_projs_so_far = set()
    for u_proj in u_projs[:act_win+1]:
      for u_p in u_proj:
        u_projs_so_far.add(u_p)
    u_dict["u_projects_to_date"] = len(u_projs_so_far)
    u_dict["u_commits_to_date"] = sum(commits_win[:act_win+1])    

    # failure
    if act_win + 1 > 35 or act_win + 2 > 35:
      u_dict["u_temp_failure"] = 0
    elif commits_win[act_win+1] == 0 and commits_win[act_win+2] == 0:
      u_dict["u_temp_failure"] = 1
    else:
      u_dict["u_temp_failure"] = 0
    
    if act_win + 1 > 35 or act_win + 2 > 35 or act_win + 3 > 35 or act_win + 4 > 35:
      u_dict["u_temp_failure_1_year"] = 0
    elif commits_win[act_win+1] == 0 and commits_win[act_win+2] == 0 and \
            commits_win[act_win+3] == 0 and commits_win[act_win+4] == 0:
      u_dict["u_temp_failure_1_year"] = 1
    else:
      u_dict["u_temp_failure_1_year"] = 0

    u_win_projs = u_projs[act_win]
    all_langs = session.query(projects.c.language).filter( \
      projects.c.id.in_(tuple(u_win_projs)),
      projects.c.language.isnot(None)).distinct(projects.c.language)
    all_langs_list = [all_lang[0] for all_lang in all_langs.all()]
    for lang in all_langs_list:
      u_languages.add(lang)
    u_dict["u_nichewidth"] = len(u_languages)
    if len(u_languages) == 0:
      u_dict["u_nichewidth"] = 1

    u_dicts.append(u_dict)
    #print proc_id, p, p_dict, datetime.now()
    out.write(str(u_dict)+",")
    out.write(str(datetime.now())+"\n")
  #out.write("\n".join([str(p_d) for p_d in p_dicts])+"\n")
  #results = pd.concat([results, pd.DataFrame(p_dicts)]) 
  #session.commit()
  conns.close()
  return u_dicts

pool = Pool(num_proc)
results = pool.map(get_info, uids)
pool.close()
pool.join()
result_f = open("result_f_user", "wb")
pickle.dump(results, result_f)
result_f.close()

'''
results = []
for p in uids:
  results.append(get_info(p))
'''

results = [dict_item for dict_lists in results for dict_item in dict_lists]
results = pd.DataFrame(results)
results.to_csv("data/results_user.csv", index = False, encoding = "utf-8")

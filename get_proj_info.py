from datetime import datetime
from math import floor
from multiprocessing import *
from project_lang_div import get_lang_div 
from project_recur_co import get_recur_co
from project_team_famil import get_team_famil
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
num_proc = 30
pswd = os.environ["SQLPW"]
id_file_name = "data/pid.list"
f = open(id_file_name)
pids = [int(l.strip()) for l in f.readlines()]
f.close()

f = open("data/big_repos.list")
big_repos = set([int(p.strip()) for p in f.readlines()])
pids = list(set(pids) - set(big_repos))
pids.sort()
print "Number of projects", len(pids)

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

langs = ["JavaScript", "Java", "Python", "CSS", "PHP", "Ruby", "C++", 
  "C", "Shell", "C#", "Objective-C", "R", "VimL", "Go", "Perl", 
  "CoffeeScript", "Tex", "Swift", "Scala", "Emacs Lisp", "Haskell", 
  "Lua", "Clojure", "Matlab", "Arduino", "Groovy", "Puppet", "Rust", 
  "PowerShell", "Erlang", "Visual Basic", "Processing", "Assembly", "Other"]
watchers = pd.read_csv("data/watchers_monthly_counts_win.csv")
print "Done setting up"

results = pd.DataFrame(columns=("p_id", "p_name", "p_lang", "p_owner",
                        "window", "p_age", "p_windows_active_to_date",
                        "p_num_stars", "p_num_users_to_date",
                        "p_num_commits_to_date", "r_team_size",
                        "p_recurring_co", "p_fam_no_decay", "p_langdiv_denom"))

url = "mysql://sophie:"+pswd+"@localhost/ghtorrent?charset=utf8mb4"
engine = create_engine(url, pool_size = num_proc, pool_recycle = 3600)
Session = sessionmaker(bind = engine)
metadata = MetaData(engine)
commits = Table("commits", metadata, autoload=True)
projects = Table("projects", metadata, autoload=True)
conns = engine.connect()
session = Session()

out = open("out", "w")
#for p_index, p in enumerate(pids):
def get_info(p):
  proc_id = os.getpid()

  # get the list of forks
  forks = root_forks[p]
  out.write(str(proc_id)+","+ str(p) +",forks,"+ str(len(forks))+","+str(datetime.now()))
  forks = tuple(forks)

  # get project basic info
  r = session.query(projects).filter(projects.c.id == p)
  p_name = r.first().name
  p_lang = r.first().language
  p_owner = r.first().owner_id
  p_owner = get_merged_id(re_alias, p_owner)

  # get project commits
  begin = datetime.strptime("2008-01-01", "%Y-%m-%d")
  end = datetime.strptime("2016-12-31", "%Y-%m-%d")
  r = session.query(commits).filter(commits.c.project_id.in_(forks),
        commits.c.created_at <= end, 
        commits.c.created_at >= begin,
        commits.c.author_id != 6059)
        
  # get lists of contributors 
  new_contr_win = {} # newly joined contributors per window
  contr_win = {} # list of contributors in each window
  all_contr = set() #
  num_commits_win = [0] * 36

  for i in range(36):
    new_contr_win[i] = set()
    contr_win[i] = set()

  for rr in r.all():
    win = floor((rr.created_at.month-1)/3+1)+ (rr.created_at.year-2008)*4
    win = int(win)
  
    merge_id = get_merged_id(re_alias, rr.author_id)
    if merge_id == 6059:
      continue # this id is for wrong email settings
    contr_win[int(win)-1].add(merge_id)
    if merge_id not in all_contr:
      new_contr_win[int(win)-1].add(merge_id)  
    all_contr.add(merge_id)

    num_commits_win[win-1] += 1

  # active windows are those with commits
  # 0 indexed 
  act_wins = [win for win in range(36) if num_commits_win[win] > 0]
  #print proc_id, "active windows", p, act_wins

  # count contributors
  contr_lens = []
  new_contr_lens = []
  for i in range(36):
    contr_lens.append(len(contr_win[i]))
    new_contr_lens.append(len(new_contr_win[i]))

  if max(contr_lens) > 1500:
    # otherwise it woule take tooooo long to calculate team familiarity
    return []   
  #print proc_id, "contr", p, contr_lens

  # watchers
  cur_stars = watchers.loc[watchers["project_id"].isin(forks)]
  cur_stars = pd.DataFrame({"sum":cur_stars.groupby(["project_id",
                            "window"])["watchers"].sum()}).reset_index().sort_values(by=["window"])

  stars_count = [0] * 36
  for i in range(cur_stars.shape[0]):
    cur_win = int(cur_stars.iloc[i][["window"]])
    if cur_win > 0 and cur_win < 37:  
      stars_count[cur_win-1] = int(cur_stars.iloc[i][["sum"]])
  #print proc_id, "star", p, stars_count

  # get users' projects per window to calculate team familiarity, lang
  # diversity, and recurring cohesion
  #contr_list_win = get_user_dict(p, helper.session)

  # create dataframe
  p_dicts = []
  for win_index, act_win in enumerate(act_wins):
    p_dict = {}
    p_dict["window_num"] = act_win + 1
    p_dict["window"] = windows[act_win]
    p_dict["p_id"] = np.int64(p)
    p_dict["p_lang"] = p_lang
    p_dict["p_owner"] = int(p_owner)
    p_dict["p_age"] = act_win - min(act_wins) # 0 based
    p_dict["p_windows_active_to_date"] = win_index + 1
    p_dict["p_team_size"] = contr_lens[act_win]
    p_dict["p_num_users_to_date"] = sum(new_contr_lens[:act_win])
    p_dict["p_num_stars"] = sum(stars_count[:act_win])
    p_dict["p_num_commits"] = num_commits_win[act_win]
    p_dict["p_num_commits_to_date"] = sum(num_commits_win[:act_win+1])

    # get contributors' projects in each window 
    #contr_projs_win[act_win] = get_user_projs_all_win(session, commits, contr_win[act_win], act_win)
    #get_user_projs_all_win(contri_projs_win, session, commits, contr_win[act_win], act_win)
    contr_projs_win = get_user_projs_all_win(cont_projs_dict,
                                                      contr_win[act_win], act_win)

    team_famil = get_team_famil(p, session, commits, contr_win[act_win],
                 contr_projs_win, proj_contrs_count, act_win)
    recur_co = get_recur_co(p, contr_win[act_win], contr_projs_win, act_win)
    lang_div = get_lang_div(session, projects, contr_win[act_win],
                contr_projs_win, act_win, langs) 

    # share of new comers
    new_comer = 0
    for contributor in contr_win[act_win]:
      # get the list of projects of this contributor
      this_contr_projs = cont_projs_dict[contributor]
      first_active_win = next((i for i, x in enumerate(this_contr_projs) if x), None)
      if first_active_win == act_win:
        new_comer += 1
    p_dict["p_sharenewcomers"] = new_comer * 1.0 / contr_lens[act_win]
    p_dict["p_sharenewcomers_this"] = new_contr_lens[act_win] * 1.0 / contr_lens[act_win]
    
    p_dict["p_fam_no_decay"] = team_famil
    p_dict["p_recurring_co"] = recur_co 
    p_dict["p_div_langdenom"] = lang_div

    p_dicts.append(p_dict)
    #print proc_id, p, p_dict, datetime.now()
    out.write(str(p_dict)+",")
    out.write(str(datetime.now())+"\n")
  #out.write("\n".join([str(p_d) for p_d in p_dicts])+"\n")
  #results = pd.concat([results, pd.DataFrame(p_dicts)]) 
  #session.commit()

  return p_dicts

'''
for i in range(6):
  print "pid:", i*10000, (i+1)*10000
  p_ids_sub = pids[(i-1)*10000:i*10000]
  pool = Pool(num_proc)
  results = []
  results = pool.map(get_info, p_ids_sub)
  pool.close()
  pool.join()
  result_f = open("result_f"+str(i), "wb")
  pickle.dump(results, result_f)
  result_f.close()


  results = [dict_item for dict_lists in results for dict_item in dict_lists]
  results = pd.DataFrame(results)
  results.to_csv("data/proj_results"+str(i)+".csv", index = False)
'''


results = []
iter_size = 5000
num_iter = len(pids) / iter_size 
print len(pids)
for i in range(num_iter+1):
  pool = Pool(num_proc)
  print datetime.now(), (i+1)*iter_size
  results_i = pool.map(get_info, pids[i*iter_size:(i+1)*iter_size])
  results_i = [dict_item for dict_lists in results_i for dict_item in dict_lists]
  results.extend(results_i)
  pool.close()
  pool.join()
  result_f = open("result_f_"+str(i), "wb")
  pickle.dump(results_i, result_f)
  result_f.close()

'''
results = []
for p in pids:
  results.append(get_info(p))
'''

results = pd.DataFrame(results)
results.to_csv("data/results_proj_big.csv", index = False, encoding = "utf-8")

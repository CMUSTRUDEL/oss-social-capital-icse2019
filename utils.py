from datetime import datetime
from math import floor
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
import os
import pandas as pd
import pickle
import random
f = open("dict/alias_map_b.dict")
alias_map = pickle.load(f)
f.close()

f = open("dict/reverse_alias_map_b.dict")
re_alias = pickle.load(f)
f.close()

time_format = "%Y-%m-%d %H:%M:%S" 
ghbegin = "2008-01-01 0:0:0"
ghend = "2016-12-31 23:59:59"
pswd = os.environ["SQLPW"]
url = "mysql://sophie:"+pswd+"@localhost/ghtorrent?charset=utf8mb4"
engine = create_engine(url, pool_pre_ping = True)
Session = sessionmaker(bind = engine)
metadata = MetaData(engine)
commits = Table('commits', metadata, autoload=True)
projects = Table('projects', metadata, autoload=True)
conn = engine.connect()
session = Session()

big_repo_limit = 500
windows = [\
  "2008-01-01 0:0:0_2008-03-31 23:59:59", "2008-04-01 0:0:0_2008-06-30 23:59:59", \
  "2008-07-01 0:0:0_2008-09-30 23:59:59", "2008-10-01 0:0:0_2008-12-31 23:59:59", \
  "2009-01-01 0:0:0_2009-03-31 23:59:59", "2009-04-01 0:0:0_2009-06-30 23:59:59", \
  "2009-07-01 0:0:0_2009-09-30 23:59:59", "2009-10-01 0:0:0_2009-12-31 23:59:59", \
  "2010-01-01 0:0:0_2010-03-31 23:59:59", "2010-04-01 0:0:0_2010-06-30 23:59:59", \
  "2010-07-01 0:0:0_2010-09-30 23:59:59", "2010-10-01 0:0:0_2010-12-31 23:59:59", \
  "2011-01-01 0:0:0_2011-03-31 23:59:59", "2011-04-01 0:0:0_2011-06-30 23:59:59", \
  "2011-07-01 0:0:0_2011-09-30 23:59:59", "2011-10-01 0:0:0_2011-12-31 23:59:59", \
  "2012-01-01 0:0:0_2012-03-31 23:59:59", "2012-04-01 0:0:0_2012-06-30 23:59:59", \
  "2012-07-01 0:0:0_2012-09-30 23:59:59", "2012-10-01 0:0:0_2012-12-31 23:59:59", \
  "2013-01-01 0:0:0_2013-03-31 23:59:59", "2013-04-01 0:0:0_2013-06-30 23:59:59", \
  "2013-07-01 0:0:0_2013-09-30 23:59:59", "2013-10-01 0:0:0_2013-12-31 23:59:59", \
  "2014-01-01 0:0:0_2014-03-31 23:59:59", "2014-04-01 0:0:0_2014-06-30 23:59:59", \
  "2014-07-01 0:0:0_2014-09-30 23:59:59", "2014-10-01 0:0:0_2014-12-31 23:59:59", \
  "2015-01-01 0:0:0_2015-03-31 23:59:59", "2015-04-01 0:0:0_2015-06-30 23:59:59", \
  "2015-07-01 0:0:0_2015-09-30 23:59:59", "2015-10-01 0:0:0_2015-12-31 23:59:59", \
  "2016-01-01 0:0:0_2016-03-31 23:59:59", "2016-04-01 0:0:0_2016-06-30 23:59:59", \
  "2016-07-01 0:0:0_2016-09-30 23:59:59", "2016-10-01 0:0:0_2016-12-31 23:59:59"]

def get_merged_id(re_alias, aid):
  if aid in re_alias:
    return re_alias[aid]
  return aid

def get_proj_users(re_alias, session, commits, forks, wind):
  [wbegin, wend] = windows[wind-1].split("_")
  begin = datetime.strptime(wbegin, time_format)
  end = datetime.strptime(wend, time_format)
  r = session.query(commits).filter( \
        commits.c.project_id.in_(tuple(forks)), 
        commits.c.created_at <= end, 
        commits.c.created_at >= begin,) 

  # num authors
  contr_win = set()
    
  for rr in r.all():
    merge_id = get_merged_id(re_alias, rr.author_id)
    if merge_id == 6059:
      continue # this id is for wrong email settings
    contr_win.add(merge_id)
  contr_win = list(contr_win)
  return contr_win

# output: a list of dictionaries, each of which corresponds to a window and
# consists of projects for each contributor active in this project in this
# window 
# get contributors' projects in each window 
def get_user_projs_all_win(cont_proj_dict, contributors, end):
  contr_projs_win = []
  for w in range(end + 1):
    contr_projs = {}
    for c in contributors:
      #projs = get_user_projs(session, commits, aliases, w)
      contr_projs[c] = cont_proj_dict[c][w]
    contr_projs_win.append(contr_projs)
  return contr_projs_win

def get_root_map(pids, session, projects):
  fork_root = {}
  r = session.query(projects).filter(projects.c.id.in_(pids))
  for a in r.all():
    if a.forked_from is None:
      fork_root[a.id] = a.id
    else:
      fork_root[a.id] = a.forked_from
  out = open("dict/fork_root.dict", "wb")
  pickle.dump(fork_root, out)
  out.close()
  return fork_root

def get_fork_map(roots, session, projects):
  big_repo = open("data/big_repos.list", "w")
  big_repo_list = []
  root_forks = {}
  for root in roots:
    forks_sql = session.query(projects).filter(projects.c.forked_from == root,
                                              projects.c.id != -1)
    forks_sql_r = forks_sql.all()
    num_forks = len(forks_sql_r)
    if num_forks == 0: 
      forks = [root]
    elif num_forks > big_repo_limit:
      r = session.query(commits.c.author_id).filter(commits.c.project_id.in_(forks),
        commits.c.author_id != 6059).distinct()
      all_contrs = len(r.all())
      if all_contrs * 1.0 / num_forks >= 0.001 and all_contrs <= 1500:
        big_repo.write(str(root) + "\n")
        big_repo_list.append(root)
        forks = [root]
        for fork in forks_sql_r:
          forks.append(fork.id)
      else:
        big_repo.write(str(root) + "\n")
        big_repo_list.append(root)
        continue
    else:
      forks = [root]
      for fork in forks_sql_r:
        forks.append(fork.id)
    root_forks[root] = forks
  out = open("dict/root_forks.dict", "wb")
  pickle.dump(root_forks, out)
  out.close()
  big_repo.close()
  return [root_forks, big_repo_list]

def get_all_contrs(pids, re_alias, root_forks, session, commits):
  begin = datetime.strptime(ghbegin, time_format)
  end = datetime.strptime(ghend, time_format)
  all_users = set()
  for p in pids:
    forks = root_forks[p]
    r = session.query(commits.c.author_id).filter(commits.c.project_id.in_(forks),
        commits.c.created_at <= end, 
        commits.c.created_at >= begin,
        commits.c.author_id != 6059).distinct() 
    users = [rr[0] for rr in r.all()]
    users = [get_merged_id(re_alias, rid) for rid in users]
    all_users = all_users.union(users)
  return list(all_users)

def get_user_projs(session, projects, commits, aliases, wind, big_repos):
  if wind == 37:
    begin = datetime.strptime(ghbegin, time_format)
    end = datetime.strptime(ghend, time_format)
  else:
    [wbegin, wend] = windows[wind].split("_")
    begin = datetime.strptime(wbegin, time_format)
    end = datetime.strptime(wend, time_format)

  user_projs_r = session.query(commits).filter( \
    commits.c.author_id.in_(aliases), 
    commits.c.created_at >= begin,
    commits.c.created_at <= end, 
    commits.c.project_id.isnot(None),
    commits.c.project_id != -1).distinct(commits.c.project_id)

  user_r = user_projs_r.all()
  if len(user_r) == 0:
    return []
  user_projs = [users_proj.project_id for users_proj in user_r]

  # only store the root of projects
  user_projs_roots = set()
  r = session.query(projects).filter(projects.c.id.in_(tuple(user_projs)))
  for a in r.all():
    if a.forked_from is None:
      u_root = a.id
    else:
      u_root = a.forked_from
    if u_root not in big_repos:
      user_projs_roots.add(u_root)

  # return the list of projects for thsi user in this window
  return list(user_projs_roots)

def get_proj_users_count(cs, root_forks, proj_user_count):
  engine = create_engine(url, pool_pre_ping = True)
  Session = sessionmaker(bind = engine)
  metadata = MetaData(engine)
  commits = Table('commits', metadata, autoload=True)
  projects = Table('projects', metadata, autoload=True)
  conn = engine.connect()
  session = Session()

  for c in cs:
    try:
      # only root projects have root_fork mapping
      forks = tuple(root_forks[c])
    except:
      r = session.query(projects).filter(projects.c.forked_from == c)
      forks = tuple([rr.id for rr in r.all()])

    # get project commits
    begin = datetime.strptime(ghbegin, time_format)
    end = datetime.strptime(ghend, time_format)
    r = session.query(commits).filter( \
          commits.c.project_id.in_(forks), 
          commits.c.created_at <= end, 
          commits.c.created_at >= begin,
          commits.c.project_id != -1) 

    # get lists of contributors 
    contr_win = {} # list of contributors in each window

    for i in range(36):
      contr_win[i] = set()
      
    for rr in r.all():
      win = floor((rr.created_at.month-1)/3+1)+ (rr.created_at.year-2008)*4
      win = int(win)
    
      merge_id = get_merged_id(re_alias, rr.author_id)
      if merge_id == 6059:
        continue # this id is for wrong email settings
      contr_win[int(win)-1].add(merge_id)

    # count contributors
    contr_lens = []
    for i in range(36):
      contr_lens.append(len(contr_win[i]))
    
    proj_user_count[c] = contr_lens
  
  try:
    session.commit()
  except:
    session.rollback()
  finally:
    session.close()

# output: a dictionary of lists, each of which is a users' projects in all
# windows
def save_user_projs_all_win(cs, contr_projs, big_repos):#session, projects, commits, c):#ontributors):
  # get contributors' projects in each window 
  '''
  contr_projs_win: a list of dictionaries, each of which is a
  contributor:projects mapping in a window prior to win
  '''

  engine = create_engine(url, pool_pre_ping = True)
  Session = sessionmaker(bind = engine)
  metadata = MetaData(engine)
  commits = Table('commits', metadata, autoload=True)
  projects = Table('projects', metadata, autoload=True)
  conn = engine.connect()
  session = Session()

  for c in cs:  
    # contr_projs_win is a list of 36 lists
    contr_projs_win = []
    if int(c) in alias_map:
      aliases = tuple(alias_map[int(c)])
    else:
      aliases = tuple([c])
    for w in range(36):
      # projs is a list
      projs = get_user_projs(session, projects, commits, aliases, w, big_repos)
      contr_projs_win.append(projs)
    contr_projs[c] = contr_projs_win
  try:
    session.commit()
  except:
    session.rollback()
  finally:
    session.close()

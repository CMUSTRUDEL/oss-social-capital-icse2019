#########
# collects users' projects
# collects the projects' forks
# creates user-project mapping and project-forks mapping
# reads files `dict/alias_map_b.dict`,
# `reverse_alias_map_b.dict`, and `data/uid.list`
# writes files `data/pid.list`, `data/all_contributors.list`, `dict/contr_projs.dict`, 
# `data/all_projs.list`, and `dict/proj_contrs_count.dict`.
#########

from utils import *
from datetime import datetime
from multiprocessing import *
from math import floor
import random
import os
from datetime import datetime
import sys
import pickle
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

#########
# Customized variables:
user_name = ""
port = 3306
host = "127.0.0.1"
pswd = os.environ["SQLPW"]
#########

print datetime.now(),
print "Setting up..."
begin = datetime.strptime("2008-01-01 0:0:0", "%Y-%m-%d %H:%M:%S")
end = datetime.strptime("2016-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")

f = open("dict/alias_map_b.dict")
alias_map = pickle.load(f)
f.close()

f = open("dict/reverse_alias_map_b.dict")
re_alias = pickle.load(f)
f.close()

print datetime.now(),
print "Loading user list..."
uid_file_name = "data/uid.list"
f = open(uid_file_name)
uids = [int(l.strip()) for l in f.readlines()]
f.close()

# get aliases of all users
u_aliases = []
for u in uids:
  if u in alias_map:
    u_aliases.extend(alias_map[u])
  else:
    u_aliases.append(u)
u_aliases = tuple(u_aliases)
print "u aliase", len(u_aliases)

print datetime.now(),
print "Getting their projects..."
r = session.query(commits.c.project_id).filter(commits.c.author_id.in_(u_aliases),
                                  commits.c.created_at <= end,
                                  commits.c.created_at >= begin,
                                  commits.c.project_id.isnot(None),
                                  commits.c.project_id != -1).distinct()
pids = [int(i[0]) for i in r.all()]
print len(pids)

print datetime.now(),
print "Getting the projects' roots and writing them into 'dict/fork_root.dict'..."
fork_root = get_root_map(pids, session, projects)
roots = [fork_root[p] for p in pids]
roots = list(set(roots))
if -1 in roots: 
  roots.remove(-1)

print datetime.now(),
print "Writing the list of projects into 'data/pid.list'..."
id_file_name = "data/pid.list"
f = open(id_file_name, "w")
for p in roots:
  f.write(str(p)+"\n")
f.close()

print datetime.now(),
print "Getting forks of projects... and writing them into",
print "'dict/root_forks.dict', and writing projects with more than 500 forks",
print "into 'data/big_repos.list'..."
[root_forks, big_projs] = get_fork_map(roots, session, projects)  

# we only do calculation for projects with fewer than 500 forks
pids = list(set(roots) - set(big_projs))

print datetime.now(),
print "Getting projects' contributors and writing them into 'data/all_contributors.list'..."
contributors = get_all_contrs(pids, re_alias, root_forks, session, commits)
out = open("data/all_contributors.list", "w")
for a in contributors:
  out.write(str(a) + "\n")
out.close()

try:
  session.commit()
except:
  session.rollback()
finally:
  session.close()

print datetime.now(),
print "Getting all their projects and writing them into 'dict/contr_projs.dict'..."
print "[WARNING] very time consuming"
# save_user_projs_all_win adds projects to all_projs
num_proc = 15
proc = []
seglen = len(contributors) / (num_proc - 2)
print len(contributors)
manager = Manager()
contr_projs = manager.dict()
for num in range(1,num_proc):
  print num, (num-1)*seglen, num*seglen
  pchild = Process(target=save_user_projs_all_win, 
		      args = (contributors[(num-1)*seglen:num*seglen],
                      contr_projs,
                      big_projs))
  proc.append(pchild)
  pchild.start()

for pchild in proc:
  pchild.join()

print "contr num", len(contributors), len(contr_projs.keys())
contr_projs = dict(contr_projs)

out = open("dict/contr_projs.dict", "wb")
pickle.dump(contr_projs, out)
out.flush()
out.close()

print datetime.now(),
print "Construct the list of all projects, more than just roots, and write them"
print " into 'data/all_projs.list'"
all_projs = set()
for c_p in contr_projs.values():
  for w in c_p:
    for w_proj in w:
      all_projs.add(w_proj)
all_projs = list(all_projs)

# save project list
out = open("data/all_projs.list", "w")
for a_p in all_projs:
  out.write(str(a_p)+"\n")
out.close()

a = open("data/all_projs.list")
all_projs = [int(l.strip()) for l in a.readlines()]
print datetime.now(),
print "Getting projects' number of contributors in each window",
print "and writing them into 'dict/proj_contrs_count.dict'..."
print "[WARNING] also very time consuming"
# this is needed for team familiarity
print "all_projs", len(all_projs)
proc = []
seglen = len(all_projs) / (num_proc - 2)
print len(all_projs)
proj_users_count = manager.dict()
for num in range(1,num_proc):
  pchild = Process(target=get_proj_users_count, 
							args = (all_projs[(num-1)*seglen:num*seglen],
                      root_forks, proj_users_count))
  proc.append(pchild)
  pchild.start()

for pchild in proc:
  pchild.join()

proj_users_count = dict(proj_users_count)
out = open("dict/proj_contrs_count.dict", "wb")
pickle.dump(proj_users_count, out)
out.flush()
out.close()


print datetime.now(),
print "Done."

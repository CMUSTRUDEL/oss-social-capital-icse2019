import numpy as np
import itertools
import time

# Gets recurring cohesion for all windows
def get_recur_co(pid, contributors, contr_projs_win, wind):
  team_size = len(contributors)
  # we only calculate for teams of size [3, 20]
  if team_size < 3 or team_size > 20:
    return 0

  cliques = set()
  potential_cliques = []
  # we only consider cliques of sizes [3, 5]
  for i in range(5, 2, -1):
    c = itertools.combinations(contributors, i)
    for cc in c:
      potential_cliques.append(cc)

  for pc in potential_cliques:
    #for prev_w_index, prev_w in enumerate(windows[:window_index+1]):
    if pc in cliques:
      continue
    for w in range(wind):
      contr_projs = contr_projs_win[w]#contributors_sql_windows[prev_w_index]
      #isClique = checkClique(pc, pid, contr_projs)
      inter = contr_projs[pc[0]] 
      for c in pc[1:]:
        inter = np.intersect1d(inter, contr_projs[c])
        if len(inter) == 0:
          # already no overlap projects
          break
        #inter = set(inter).intersection(set(contr_projs[c]))
      if len(inter) > 0:
        cliques.add(pc)
        for subcliquesize in range(len(pc)-1,2,-1):
          # all the subset of the set should all be cliques
          subcliques = itertools.combinations(pc, subcliquesize)
          for subc in subcliques:
            cliques.add(subc)
        #as long as it is a clique in any of the prev windows,
        #we don't need to keep verifying it in other windows 
        break

  cliques = list(cliques)
  q_c = len(cliques) # number of cliques
  S_c = len(contributors) * 1.0 # number of contributors in this window
  if q_c == 1:
    return len(cliques[0]) * 1.0 / S_c
  else:
    denom = 2 * (q_c * 1.0 - 1)
    nom = 0
    for i in range(0, len(cliques)-1):
      for j in range(i+1, len(cliques)):
        inter = set(cliques[i]).intersection(set(cliques[j]))
        S_v = len(cliques[i])
        nom += (S_v + len(inter)) / S_c 
    return nom / denom

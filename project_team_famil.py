from utils import *
import numpy as np
from datetime import datetime

def get_team_famil(p, session, commits, contributors, contr_projs_win,
                    proj_contrs_count, win):
  contributors = list(contributors)
  team_size = len(contributors)
  if team_size <= 1:
    return 0

  famil = np.zeros((len(contributors), len(contributors)))

  cur_fam_no_decay = 0
  for w in range(win):
    for contr_count, i in enumerate(contributors[:-1]):
      contr_count += 1
      for j in contributors[contr_count:]:
        #common_proj = set(contr_projs_win[w][i]).intersection(set(contr_projs_win[w][j]))
        common_proj = np.intersect1d(contr_projs_win[w][i],
        contr_projs_win[w][j])

        person_inter = 0
        # accumulate familiarity of each common project
        for c in common_proj:
          count = proj_contrs_count[c][w]

          if count <= 1:
            person_inter += 0
          else:
            #\sum_{r_s} \frac{1}{|r_s| - 1}
            person_inter += 1.0 / (count - 1) # (0, 1] person_inter may > 1

        # accmulate familiarity over time
        famil[contributors.index(i)][contributors.index(j)] += person_inter 

  return 1.0 * sum(sum(famil)) / (team_size * (team_size - 1) / 2)

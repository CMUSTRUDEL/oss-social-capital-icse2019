from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dbs import *

# calculates language diversity of a project in a window
# input: 
# contributors: a list of contributors to this project in this window
# contr_projs_win: a list of dictionaries, each of which is a
# contributor:projects mapping in a window prior to win
# win: the number of current window, 0 indexed
# output: language diversity [0,1] of this project in this window.
def get_lang_div(pid, contributors, contr_projs_win, win, langs):
  team_size = len(contributors)
  if team_size == 0:
    return 0 

  langs_m = np.zeros((team_size, 34)) # 34 is the number of languages
  for uind, u in enumerate(contributors):
    # get users' all past projects
    projs = []
    for w in range(win+1):
      u_projs_win = contr_projs_win[w][u]
      projs.extend(u_projs_win)
    u_all_projs = list(set(projs))

    # get languages of users' all past projects
    all_langs = session.query(projects.c.language).filter( \
      projects.c.id.in_(tuple(u_all_projs)),
      projects.c.language.isnot(None)).distinct(projects.c.language)
    all_langs_list = [all_lang[0] for all_lang in all_langs.all()]

    langs_num = [1 * (l in all_langs_list) for l in langs]
    for all_lang in all_langs_list:
      if all_lang not in langs:
        langs_num[-1] = 1
        break
    langs_m[uind] = langs_num

  cos_sim = cosine_similarity(langs_m)

  return sum(sum(cos_sim))*1.0 / (team_size)**2

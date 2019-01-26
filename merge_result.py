import pandas as pd

proj = pd.read_csv("data/results_proj.csv")
user = pd.read_csv("data/results_user.csv")
user_proj = pd.read_csv("data/results_user_proj.csv")

total = pd.merge(user, user_proj, left_on = ["u_id", "window_num"], right_on = \
["u_id", "window_num"], how =\
"inner")
total = pd.merge(total, proj, left_on = ["p_id", "window_num"], right_on = ["p_id",
"window_num"], how =\
"inner")
total.to_csv("data/proj_user_proj.csv", index=False)

import random
from insert_to_db import *
from gender.get_feature import *
from gender.determine_gender import *

f = open("data/all_users.list")
filtered_users = [int(l.strip()) for l in f.readlines()]
f.close()

sample_size = 100000
sample_user = random.sample(filtered_users, sample_size)
f = open("data/uid_raw.list", "w")
for s in sample_user:
  f.write(str(s)+"\n")
f.close()

f = open("new_100000/data/uid.list")
sample_user = [int(l.strip()) for l in f.readlines()]
feature_f = "new_100000/data/gender_feature.csv"
gender_f = "new_100000/data/gender.csv"
#insert_to_db(sample_user)
parse_feature(sample_user, feature_f)
determine_gender(feature_f, gender_f)

# balance sample
f = open(gender_f)
lines = [l.strip().split(",") for l in f.readlines()]
female = [l for l in lines if l[-1] == "1"]
male = [l for l in lines if l[-1] == "-1"]

sample_size = len(female)
sampled_male = random.sample(male, sample_size)
f = open("new_100000/data/sampled_user_gender.csv", "w")
fid = open("new_100000/data/uid_new.list", "w")
for fe in female:
  f.write(",".join(fe) + "\n")
  fid.write(fe[0] + "\n")
for ma in sampled_male:
  f.write(",".join(ma) + "\n")
  fid.write(ma[0] + "\n")
f.close()
fid.close()

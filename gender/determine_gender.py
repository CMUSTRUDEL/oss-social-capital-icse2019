import pickle
import os
import pymysql

f = open("gender/gender_classifier.pickel", "rb")
classifier = pickle.load(f)
f.close()
pswd = os.environ["SQLPW"]
conn = pymysql.connect(host="localhost",user="sophie",passwd=pswd,db="namsor")
cursor = conn.cursor()

test_names = []
test_labels = []
test_num_list = []
def load_data(lines):
  names_in = [n.split(",")[0] for n in lines]
 
  test_names.extend([n.title() for n in names_in])
  test_labels.extend([n.split(",")[-1] for n in lines])
  test_num_list.extend([n.split(",")[1:-1] for n in lines])

def gender_features(word, nums):
  features = {}
  features["first_letter"] = word[0]
  features["last_letter"] = word[-1]
  features["bigram_1"] = word[:2]
  features["bigram_2"] = word[1:3]
  features["bigram_3"] = word[2:4]
  features["bigram_last"] = word[-2:]
  features["trigram_1"] = word[:3]
  features["trigram_2"] = word[1:4]
  features["trigram_3"] = word[2:5]
  features["trigram_last"] = word[-3:]
  features["four_last"] = word[-4:]
  features["five_last"] = word[-5:]
  features["namsor"] = nums[2]
  features["genderComputer"] = nums[3]
  return features

def determine_gender(in_f, out_f):
  f = open(in_f)
  lines = [l.strip() for l in f.readlines()]
  f.close()
  load_data(lines)
  test_labeled_names = [(name, num, label) for name, num, label \
                        in zip(test_names, test_num_list, test_labels)]
  test_set = [(gender_features(n, num), gender) for (n, num, gender) in\
                        test_labeled_names]
  pred1 = [classifier.classify(s) for (s, _) in test_set]
  print pred1[:20]
  
  out = open(out_f, "w")
  for i, p in enumerate(pred1):
    out.write(str(lines[i].split(",")[-1]) + "," + lines[i].split(",")[0] + "," + p + "\n")
  out.close()

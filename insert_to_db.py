import pymysql
import random
import os

def insert_to_db(uids, host, port, user_name, pswd):
  # MySQL connection
  conn = pymysql.connect(host=host,
                         port=port, 
                         user=user_name, 
                         passwd=pswd,
                         db='namsor', 
                         charset="utf8")
  cursor = conn.cursor()
  
  print("start")
  count = 0
  for uid in uids:  
    sql = "select login from ght_namsor_s where id = %d" % uid
    if cursor.execute(sql) > 0:
      continue
    count += 1
    if count % 100 == 0:
      print count
  
    sql = "insert into ght_namsor_s (id, login, name, firstName, lastName, email, \
              company, created_at, type, fake, deleted, location, nameParseScore, \
              country, countryAlt, countryScore, script, countryFirstName, countryLastName, \
              countryScoreFirstName, countryScoreLastName, gender, countryGender, \
              countryGenderAlt, genderScale) \
              select distinct u.id, u.login, p.name, np.firstName, np.lastName, p.email,\
                  u.company, u.created_at, u.type, u.fake, u.deleted, u.location,\
                  np.score as nameParseScore, o.country, o.countryAlt, \
                  o.score as countryScore, o.script, o.countryFirstName,\
                  o.countryLastName, o.scoreFirstName as countryScoreFirstName,\
                  o.scoreLastName as countryScoreLastName, g.gender,\
                  g.country as countryGender, g.countryAlt as countryGenderAlt,\
                  g.genderScale\
              from ghtorrent.users u, namsor.ght_private p,\
                  namsor.name_parse np, namsor.origin o, namsor.gender g\
              where u.id = %d\
              and u.login = p.login\
              and u.type = 'USR'\
              and p.name = np.fullName \
              and o.firstName = np.firstName collate utf8mb4_bin\
              and o.lastName = np.lastName collate utf8mb4_bin\
              and g.firstName = np.firstName collate utf8mb4_bin\
              and g.lastName = np.lastName collate utf8mb4_bin;" % uid
  
    cursor.execute(sql)
    conn.commit()

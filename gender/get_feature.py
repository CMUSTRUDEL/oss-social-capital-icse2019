# name
# name length
# country's numerical code
# namsor
# genderComputer
import pycountry
import os
import sys
from genderComputer.genderComputer import GenderComputer
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

def parse_feature(uids, output_f_name):
  # features:
  # name
  # name length
  # country's numerical code
  # namsor
  # genderComputer
  # uid

  pswd = os.environ["SQLPW"]
  url = "mysql://sophie:"+pswd+"@localhost/namsor?charset=utf8mb4"
  engine = create_engine(url)
  Session = sessionmaker(bind = engine)
  metadata = MetaData(engine)
  ght_namsor = Table("ght_namsor_s", metadata, autoload=True)
  conn = engine.connect()
  session = Session()
  dataPath = os.path.dirname(os.path.abspath(__file__))
  gc = GenderComputer(os.path.join(dataPath, 'genderComputer/nameLists'))
  output_f = open(output_f_name, "w")

  for uid in uids:
    r = session.query(ght_namsor).filter(ght_namsor.c.id == uid).first()
    if r is None:
      continue
    firstName = r.firstName
    namsor = r.genderScale
    country_2 = r.country
    if country_2 is not None and country_2 != "null":
      cnty_p = pycountry.countries.get(alpha_2=country_2)
      cnty = cnty_p.name
      cnty_code = cnty_p.numeric
    else:
      cnty = ""

    # name
    output_f.write(firstName.encode("utf-8"))
    features = ","

    # name length
    features += (str(len(firstName)) + ",")

    # country code
    features += (str(cnty_code) + ",")
    # namsor
    features += (str(namsor) + ",")

    # genderComputer
    try:
      genderC = gc.resolveGender(unicode(firstName), cnty)#.decode('utf-8'), cnty)
    except:
      genderC = None
    if genderC is None:
       genderCint = 0
    elif genderC == "mostly male":
      genderCint = -0.8
    elif genderC == "male":
      genderCint = -1
    elif genderC == "mostly female":
      genderCint = 0.8
    elif genderC == "female":
      genderCint = 1
    else:
      genderCint = 0
    features += (str(genderCint) + "," + str(uid))
    output_f.write(features+"\n")

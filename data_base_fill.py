import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_base import *
import pandas as pd 

#Load data for the database
data = pd.read_csv("C:\\Users\\Glenn's pc\\Documents\\Uni\\Disertation\\database_data.csv")
# create a Session
Session = sessionmaker(bind=engine)
session = Session()
for rec in range(len(data)):
	record = (data.iloc[rec])
	#print(record[0])
	Detached = record[0]
	Detached = int(Detached)

	Ageband = record[1]
	Ageband = int(Ageband)

	Cwi = record[2]
	Cwi = int(Cwi)


	Loft = record[3]
	Loft = int(Loft)

	Dg = record[4]
	Dg = int(Dg)

	Cond = record[5]
	Cond = int(Cond)

	Swi = record[6]
	Swi = int(Swi)

	Ashp = record[7]
	Ashp = int(Ashp)

	Gshp = record[8]
	Gshp = int(Gshp)

	Bio = record[9]
	Bio = int(Bio)

	Pv = record[10]
	Pv = int(Pv)

	Shw = record[11]
	Shw = int(Shw)

	Total_Energy_Use = record[12]
	Total_Energy_Use = int(Total_Energy_Use)

	house = housing(Detached, Ageband, Cwi, Loft, Dg, Cond, Swi, Ashp, Gshp, Bio, Pv, Shw, Total_Energy_Use)
	session.add(house)

session.commit()

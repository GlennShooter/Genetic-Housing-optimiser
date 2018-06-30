import os
import sys
import json
import csv
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_base import *

class FileRead():
	""" This Class Reads a users data file into my program, the date can be in any order and the class reorders the data and returns it ready to be modeled"""
	def __init__(self,file):
		self.file = file
		self.data = []

	def process(self):
		f = os.path.basename(self.file) #Saves the file name 
		#Based on if the file is CSV or JSON it will be proccessed a different way 
		if f[-1] == "v":
			with open(self.file) as user_file:
				reader = csv.reader(user_file)
				user_file.seek(0)
				#Discover where in each row the variables are and store their index
				for line in reader:
					try:
						columns = [x.lower() for x in line]
						detach = columns.index("detached")
						ageband = columns.index("ageband")
						cwi = columns.index("cwi")
						loft = columns.index("loft")
						dg = columns.index("dg")
						cond = columns.index("cond")
						swi = columns.index("swi")
						ashp = columns.index("ashp")
						gshp = columns.index("gshp")
						bio = columns.index("bio")
						pv = columns.index("pv")
						shw = columns.index("shw")
						break
					except ValueError:
						print("""ERROR: Please only enter the correct column names, the correct column names are:
							 1.Detached
							 2.AgeBand
							 3.Cwi
							 4.Loft
							 5.Dg
							 6.Cond
							 7.Swi
							 8.Ashp
							 9.Gshp
							 10.Bio
							 11.Pv
							 12.Shw""")
						sys.exit()

				#reodrer input file so the model can predict energy usage of each house 
				to_review = []	
				for line in reader:
					lin = []
					lin.append(line[detach])
					lin.append(line[ageband])
					lin.append(line[cwi])
					lin.append(line[loft])
					lin.append(line[dg])
					lin.append(line[cond])
					lin.append(line[swi])
					lin.append(line[ashp])
					lin.append(line[gshp])
					lin.append(line[bio])
					lin.append(line[pv])
					lin.append(line[shw])
					to_review.append(lin)

				#to_review = np.asarray(to_review)
				#to_review = to_review.astype(int)
			self.data = to_review
			return to_review
			

		#Same process for Json files, read the file and save each record into an array in a set order 
		elif f[-1] == "n":
			with open(self.file) as user_file:
				j_file = json.load(user_file)
				to_review = []
				for row  in j_file:
					try:
						lin = []
						lin.append(row["Detached"])
						lin.append(row["AgeBand"])
						lin.append(row["Cwi"])
						lin.append(row["Loft"])
						lin.append(row["Dg"])
						lin.append(row["Cond"])
						lin.append(row["Swi"])
						lin.append(row["Ashp"])
						lin.append(row["Gshp"])
						lin.append(row["Bio"])
						lin.append(row["Pv"])
						lin.append(row["Shw"])
						to_review.append(lin)
					except KeyError:
						print("""ERROR: Please only enter the correct column names, the correct column names are:
							 1.Detached
							 2.AgeBand
							 3.Cwi
							 4.Loft
							 5.Dg
							 6.Cond
							 7.Swi
							 8.Ashp
							 9.Gshp
							 10.Bio
							 11.Pv
							 12.Shw""")
						sys.exit()


				#to_review = np.asarray(to_review)
				#to_review = to_review.astype(int)
			self.data = to_review
			return to_review
			
		else:
			print("Error invalid file type please only input CSV or JSON files") #PLACEHOLDER WANT A PROPPER ERROR MESSAGE IN FINAL DRAFT
			sys.exit()
	def assesment(self):
		clean_seed = [] #will store self.data cleaned housing data 
		clean_house = [] #will store a cleaned house from self.data this will be added to clean_seed

		#for house in self.data:
		#	clean_house = []
		#	counter = 0
		#	for i in house:
		#		if counter != 1:
		#			if i != "1" and i != "0":
		#				clean_house.append("0")
		#			else:
		#				clean_house.append(i)
		#		if counter == 1:
		#			clean_house.append(i)
		#	clean_seed.append(clean_house)

		#for h in clean_seed:
		#	print(h)

		engine = create_engine('sqlite:///housing.db', echo=False)
 
		# create a Session
		Session = sessionmaker(bind=engine)
		session = Session()
		 
		returned = [] #Will store the values of total energy usage for each query 
		values = [] #Will store average energy usage for each query this will be the value the fitness function assigns to each hous

		to_query = [] #stores the houses which will be used to query the database
		clean_house = [] #stores clean house data that can be used to query the database 

#If a house does not have a cavity wall it cant have cavity wall insulation, to let my system know this the user can input any value other than 1 or 0 into the column
#however my database is made up of presence and absence data so the input file needs to be cleaned before the database is queried, once the database has been 
#queried the energy use value is appended onto the original input data which is what is finally returned 
		for house in self.data:
			for i in house:
				clean_house.append(i)
			to_query.append(clean_house)
			clean_house = []

		counter = 0
		for record in to_query:
			#if any variable other than ageband equals a value other than 1 or 0 for the purposes of quering the database it equals 0
			if record[0] != "1" and record[0] != "0":
				record[0] = "0"
			if record[2] != "1" and record[2] != "0":
				record[2] = "0"
			if record[3] != "1" and record[3] != "0":
				record[3] = "0"
			if record[4] != "1" and record[4] != "0":
				record[4] = "0"
			if record[5] != "1" and record[5] != "0":
				record[5] = "0"
			if record[6] != "1" and record[6] != "0":
				record[6] = "0"
			if record[7] != "1" and record[7] != "0":
				record[7] = "0"
			if record[8] != "1" and record[8] != "0":
				record[8] = "0"
			if record[9] != "1" and record[9] != "0":
				record[9] = "0"
			if record[10] != "1" and record[10] != "0":
				record[10] = "0"
			if record[11] != "1" and record[11] != "0":
				record[11] = "0"
			counter += 1
			#First I query with all provided data, if this fails i remove age band and query again, so far this has been a robust method 
			for record in session.query(housing).filter(housing.Detached == record[0], housing.Ageband == record[1], housing.Cwi == record[2], housing.Loft == record[3], 
				housing.Dg == record[4], housing.Cond == record[5], housing.Swi == record[6], housing.Ashp == record[7], housing.Gshp == record[8], housing.Bio == record[9], 
				housing.Pv == record[10],housing.Shw  == record[11]):
				returned.append(record.Total_Energy_Use)
			l = len(returned)
			if l == 0:
				for record in session.query(housing).filter(housing.Detached == record[0], housing.Cwi == record[2], housing.Loft == record[3], 
				housing.Dg == record[4], housing.Cond == record[5], housing.Swi == record[6], housing.Ashp == record[7], housing.Gshp == record[8], housing.Bio == record[9], 
				housing.Pv == record[10],housing.Shw  == record[11]):
					returned.append(record.Total_Energy_Use)
				values.append(np.mean(returned))
			else:
				values.append(np.mean(returned))
			returned = []

		for i in range(len(self.data)):
			self.data[i].append(values[i])
		return self.data
	
#Test the class
#j = FileRead(r"C:\Users\Glenn's pc\Documents\Uni\Disertation\sample.json")
#c = FileRead(r"C:\Users\Glenn's pc\Documents\Uni\Disertation\test_database.csv")
#c.process()
#j.process()
#init_set = c.assesment()
#j_init_set = j.assesment()
#for i in init_set:
#	print(i)

#print()

#for i in j_init_set:
	#print(i)

#Module works very well
#Takes in a data file 
#Reorders it so that is can be processed by my model, but also makes it easier for me to assign costs to changes
#Turn data into numpy arrays 
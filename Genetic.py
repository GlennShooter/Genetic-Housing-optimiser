from sqlalchemy import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from operator import itemgetter
import os
import sys
import json
import csv
import random
import numpy as np
from data_base import *
from FileRead import *


class Genetic:
	""" A class that provides methods to apply a genetic algorithm to a file of housing data and recomend inprovements """

	def __init__(self, population_size, mutation_rate, crossover_rate, cwi_cost = 500, loft_cost = 250, dg_cost = 5000, cond_cost = 2500, swi_cost = 8000, 
		ashp_cost = 7000, gsph_cost = 10000, bio_cost = 10000, pv_cost = 8000, shw_cost = 2000):
		""" Constructor for the Genetic algorithm takes in a population size, a mutation rate, a crossover rate and the clean input data which will be used
		to create the starting population"""

		self.population_size = population_size #Size of the population in  the gentic algorithm
		self.mutation_rate = mutation_rate #The rate of mutation for the genetic algorithm 
		self.crossover_rate = crossover_rate #crossover rate for the genetic algorithm
		self.seed = [] #stores an initial input population used to assess costs 
		self.pop = [] #stores the population of solutions
		self.pop_scores = [] #stores the scores for each solution in the population 
		self.rank_crowd = [] # stores the solution index its rank and its crowding score 
		self.survivors = [] #Stores surviving solutions for each generation 
		self.total_init_score = 0 #stores the total energy use of the input file (crucial for analysis method)
		self.house_init_scores = [] #stores the energy use of each individual house in the input file (crucial for analysis method)

		self.cwi_cost = cwi_cost #cost of cavity wall insulation
		self.loft_cost = loft_cost #cost of loft insulation
		self.dg_cost = dg_cost #cost of double glazing
		self.cond_cost = cond_cost #cost of a condensing boiler
		self.swi_cost = swi_cost #cost of solid wall insulation
		self.ashp_cost = ashp_cost #cost of air sourced heat pump
		self.gsph_cost = gsph_cost # cost of a ground sourced heat pump
		self.bio_cost = bio_cost # cost of a biomass heater
		self.pv_cost = pv_cost # cost of solar panels
		self.shw_cost = shw_cost # cost of solar heated hot water

		random.seed();

	def populate (self, clean_file):
		"""
		Creats an initial population from the input data file 
		Ensures that there are no errors in the input file if there are errors are generated 
		""" 
		self.seed = clean_file #The seed for the initial population comes from the input data this variable will also be important in making recommendations

		#Before i can assess the energy scores for each house in the input file and the overall portfolio score i need to ensure there are no errors in the input file
		#If there are no erros the total energy use of the portfoli is returned. if there are errors the location of the errors are returned and the user asked to fix them

		counter = 1 #counter starts at 1 so it is easier for the user to see which house in the input file is causing the error
		error_count = 0 #Counts the number of errors in the input file  
		for h in self.seed: #for each house in the input file 
			if h[-1] == h[-1]: #If house has an assigned energy value append it to the initial house scores list 
				self.house_init_scores.append(h[-1])
			else: #If it has no value this is an invalid entry this part of the code will deduce the input error
				#Checks to see if the error was due to the user providing a house with both cwi and swi 
				if h[2] == "1":
					if h[6] == "1":
						print()
						print("InputError: You have indicated your property has both Cavity Wall insulation and Solid Wall insulation")
						print("Please ensure your input file only contains house with Cavity Wall insulation or Solid Wall insulation but not both")
						print("Location of Error: located invalid data entry at house number ", counter, " in input file")
						error_count += 1
				boilers = 0 #stores the number of boilers the solution has
				#if more than 1 boiler is counted an error is returned 
				if h[5] == "1":
					boilers += 1
				if h[7] == "1":
					boilers += 1
				if h[8] == "1":
					boilers += 1 
				if h[9] == "1":
					boilers += 1

				if boilers > 1:
					print()
					print("InputError: You have indicated your property has more than one type of boiler, each property can only have one of the following:")
					print("Condensing boiler, Air sourced heat pumps, Ground sourced heat pumps, Biomass heaters")
					print("Location of Error: located invalid data entry at house number ", counter, " in input file")
					error_count += 1

				#Check to ensure that the user has not entered a house that does not exist in the database 
				if h[2] == "0":
					if h[3] == "0":
						if h[4] == "0":
							if h[5] == "1":
								if h[0] == "1":
									print()
									print("InputError: We are very sorry but the property you entered is not in our database so can't be assesed")
									print("Location of Error: located invalid data entry at house number ", counter, " in input file, please remove the house from the input file to continue")
									error_count += 1

				test = int(h[0]) #Checks to ensure the detached value is a binary value
				if test > 1:
					print()
					print("InputError: You have entered an incorect value")
					print("Location of Error: located invalid data entry at house number ", counter," in column ", i + 1, " in input file. Please use a binary value")
					error_count += 1
				if test <  0:
					print()
					print("InputError: You have entered an incorect value")
					print("Location of Error: located invalid data entry at house number ", counter," in column ", i + 1, " in input file. Please use a binary value")
					error_count += 1
				for i in range(2,len(h) -1): #Checks to ensure the values given for the retrofit variables are binary 
					try:
						test = int(h[i])
					except ValueError: #catches any cases where the user missed a value 
						print()
						print("InputError: There is a missing value in the input file")
						print("Location of Error: located invalid data entry at house number ", counter," in column ", i + 1, " in input file. Please use a binary value")
						error_count += 1
					if test > 1:
						print()
						print("InputError: You have entered an incorect value")
						print("Location of Error: located invalid data entry at house number ", counter," in column ", i + 1, " in input file. Please use a binary value")
						error_count += 1
					if test < 0:
						print()
						print("InputError: You have entered an incorect value")
						print("Location of Error: located invalid data entry at house number ", counter," in column ", i + 1, " in input file. Please use a binary value")
						error_count += 1



			counter += 1 #increase counter by 1
	
		if error_count > 0: #if errors exist the program reports the error and end, although most these errors won't break the program they will corrupt the results 
			sys.exit()

		self.total_init_score = sum(self.house_init_scores) #total inital energy score is just the sum of the energy scores of each house in the portfolio

		seed = self.seed
		transform = []
		for i in seed:
			transform.append(i[0:-1])

		seed = transform

		#The seed needs to be split into immutable and mutable parts, the age band and whether or not the house is detached are immutable 
		retrofit = seed
		transform = []
		for i in seed:
			transform.append(i[2:])

		retrofit = transform

		#Now i have each record split in two the immutable parts are still stored in the initial seed and the mutable parts are in retrofit
		#Solitions have further rules is you have Cavity wall insulation you can't have solid wall insulation 
		#also condensing boilers, air source heat pumps, ground source heat pumps and biomass heaters are mutually exclusive 
		#FOR CODING PURPOSES ONLY DELETE LATER cwi[0], loft[1], dg[2], cond[3], swi[4], ashp[5], gshp[6], bio[7], pv[8], shw[9]
		counter = len(self.pop)
		h_counter = 0 #used to assign detatched status and age band to each new solution,(these need to be the same as in the input file )
		while  counter < self.population_size:
			houses = [] #if user has a portfolio larger than 1 house each house in a solution is stored in houses which will be appended to the population
			for i in retrofit:
				detach = self.seed[h_counter][0]
				if self.seed[h_counter][2] != "0" and self.seed[h_counter][2] != "1": #if cwi equals any non binary value in the input file the house cant have it hence it always equals 0
					cwi = 0
				if self.seed[h_counter][6] == "1": #If the house in the input file has solid wall insulation it can't have cavity wall insulation 
					cwi = 0
					swi = 1
				if self.seed[h_counter][2] == "0" and self.seed[h_counter][6] != "1": #If in the input file cwi is not present then it can take a random value of 1 or 0
					cwi = random.randint(0,1) #Set value for cavity wall insulation
				if self.seed[h_counter][6] != "0" and self.seed[h_counter][6] != "1": #if swi equals any non binary value in the input file the house cant have it hence it always equals 0
					swi = 0
				if self.seed[h_counter][2] == "1": #If the house in the input file has cavity wall insulation it can't have solid wall insulation 
					swi = 0
					cwi = 1
				if self.seed[h_counter][6] == "0" and self.seed[h_counter][2] != "1": #If in the input file swi is not present then it can take a random value of 1 or 0
					swi = random.randint(0,1)
				if self.seed[h_counter][3] == "0":
					loft = random.randint(0,1) #set value for loft insulation
				if self.seed[h_counter][3] == "1":
					loft = 1
				if self.seed[h_counter][3] != "0" and self.seed[h_counter][3] != "1": #if a house can't have loft insulation
					loft = 0
				if self.seed[h_counter][4] == "0":
					dg = random.randint(0,1) #set value for double glazing
				if self.seed[h_counter][4] == "1":
					dg = 1
				if self.seed[h_counter][4] != "1" and self.seed[h_counter][4] != "0":
					dg = 0

				#Boilers need to be mutually exclussive but houses won't neccesarily be able to fit all boilers so this block of code intends to 
				#check the input file and ensure that a house only has boilers it can actually have fitted in the population 

				invalid_boilers = [] #will store values if a house can't have a certain type of boiler fitted
				boiler_list = [5,7,8,9] #Stores the indexs of the different boilers
				#a selection of if statements to check which boilers a house can have 
				if self.seed[h_counter][5] != "1" and self.seed[h_counter][5] != "0":
					invalid_boilers.append(5) 
				if self.seed[h_counter][7] != "1" and self.seed[h_counter][7] != "0":
					invalid_boilers.append(7) 
				if self.seed[h_counter][8] != "1" and self.seed[h_counter][8] != "0":
					invalid_boilers.append(8) 
				if self.seed[h_counter][9] != "1" or self.seed[h_counter][9] != "0":
					invalid_boilers.append(9) 
				if len(invalid_boilers) != 4: #If the house can have at least one boiler
					boiler_index = random.randint(0,3) #select a boiler for each house they are mutually exclusive so only 1 can be selected
					boiler = boiler_list[boiler_index]
					while boiler in invalid_boilers: #if boiler is in the invalid boiler list keep changing the value until a valid boiler is selected 
						boiler_index = random.randint(0,3)
						boiler = boiler_list[boiler_index]
					if boiler == 5:
						cond = 1
						ashp = 0
						gshp = 0
						bio = 0
		
					if boiler == 7:
						cond = 0
						ashp = 1
						gshp = 0
						bio = 0
					if boiler == 8:
						cond = 0
						ashp = 0
						gshp = 1
						bio = 0
					if boiler == 9:
						cond = 0
						ashp = 0
						gshp = 0
						bio = 1	

				if len(invalid_boilers) == 4: #if all boilers can't be fitted
					cond = 0
					ashp = 0
					gshp = 0
					bio = 0

				if cwi == 0 & loft == 0 & dg == 0:
					if cond == 1:
						if detach == "1":
							pv = 0
							shw = 0
						else:
							if self.seed[h_counter][11] == "0": #If the house in the input file does not have solar hot water, randomly select if it has it or not in the population
								shw = random.randint(0,1)
							if self.seed[h_counter][11] == "1": #If the house in the input file already has solar hot water ensure it keeps solar hot water
								shw = 1
							if self.seed[h_counter][11] != "0" and self.seed[h_counter][11] != "1": #if house in the input file can't have solar hot water ensure it does not have solar hot water
								shw = 0
							if self.seed[h_counter][10] == "0": #If the house in the input file does not have solar panels, randomly select if it has it or not in the population
								pv = random.randint(0,1)
							if self.seed[h_counter][10] == "1": #If the house in the input file already has solar panels ensure it keeps solar panels.
								pv = 1
							if self.seed[h_counter][10] != "0" and self.seed[h_counter][10] != "1": #if house in the input file cant have solar panels ensure it does not occur in the population 
								pv = 0
					else:
						if self.seed[h_counter][11] == "0": #If the house in the input file does not have solar hot water, randomly select if it has it or not in the population
							shw = random.randint(0,1)
						if self.seed[h_counter][11] == "1": #If the house in the input file already has solar hot water ensure it keeps solar hot water
							shw = 1
						if self.seed[h_counter][11] != "0" and self.seed[h_counter][11] != "1": #if house in the input file can't have solar hot water ensure it does not have solar hot water
							shw = 0
						if self.seed[h_counter][10] == "0": #If the house in the input file does not have solar panels, randomly select if it has it or not in the population
							pv = random.randint(0,1)
						if self.seed[h_counter][10] == "1": #If the house in the input file already has solar panels ensure it keeps solar panels.
							pv = 1
						if self.seed[h_counter][10] != "0" and self.seed[h_counter][10] != "1": #if house in the input file cant have solar panels ensure it does not occur in the population 
							pv = 0

				else:
					if self.seed[h_counter][11] == "0": #If the house in the input file does not have solar hot water, randomly select if it has it or not in the population
						shw = random.randint(0,1)
					if self.seed[h_counter][11] == "1": #If the house in the input file already has solar hot water ensure it keeps solar hot water
						shw = 1
					if self.seed[h_counter][11] != "0" and self.seed[h_counter][11] != "1": #if house in the input file can't have solar hot water ensure it does not have solar hot water
						shw = 0
					if self.seed[h_counter][10] == "0": #If the house in the input file does not have solar panels, randomly select if it has it or not in the population
						pv = random.randint(0,1)
					if self.seed[h_counter][10] == "1": #If the house in the input file already has solar panels ensure it keeps solar panels.
						pv = 1
					if self.seed[h_counter][10] != "0" and self.seed[h_counter][10] != "1": #if house in the input file cant have solar panels ensure it does not occur in the population 
						pv = 0
					

				house = [] #Create an empty list to store the values of a new house 
				house.append(seed[h_counter][0]) #Set the age and and detached status equal to the house in the input data (we are retrofitting these things can't chang)
				house.append(seed[h_counter][1])
				h_counter += 1
				if h_counter == len(seed):
					h_counter = 0
				#append the retrofit values 
				cwi = str(cwi)
				house.append(cwi)
				loft = str(loft)
				house.append(loft)
				dg = str(dg)
				house.append(dg)
				cond = str(cond)
				house.append(cond)
				swi = str(swi)
				house.append(swi)
				ashp = str(ashp)
				house.append(ashp)
				gshp = str(gshp)
				house.append(gshp)
				bio = str(bio)
				house.append(bio)
				pv = str(pv)
				house.append(pv)
				shw = str(shw)
				house.append(shw)
				
				houses.append(house)
			counter += 1

			self.pop.append(houses)



	def fit(self):
		self.pop_scores = []
		engine = create_engine('sqlite:///housing.db', echo=False)
 
		# create a Session
		Session = sessionmaker(bind=engine)
		session = Session()

		returned = [] #Will store the values of total energy usage for each query 
		pop_scores = [] #stores the sum of the total energy usage for each solution
		values = [] #Will store average energy usage for each query this will be the value the fitness function assigns to each house in a solution
			
		#First I query with all provided data, if this fails i remove age band and query again, so far this has been a robust method 
		counter = 0 #used to count which solution is being assessed
		for sol in self.pop:
			for record in sol: 
				for house in session.query(housing).filter(housing.Detached == record[0], housing.Ageband == record[1], housing.Cwi == record[2], housing.Loft == record[3], 
					housing.Dg == record[4], housing.Cond == record[5], housing.Swi == record[6], housing.Ashp == record[7], housing.Gshp == record[8], housing.Bio == record[9], 
					housing.Pv == record[10],housing.Shw  == record[11]):
					returned.append(house.Total_Energy_Use) #get energy use for each house in a solution

				l = len(returned) # used to check if the database returns any results 

				#If the database returns no result the program removes age band and searches again
				if l == 0:
					for house in session.query(housing).filter(housing.Detached == record[0], housing.Cwi == record[2], housing.Loft == record[3], 
					housing.Dg == record[4], housing.Cond == record[5], housing.Swi == record[6], housing.Ashp == record[7], housing.Gshp == record[8], housing.Bio == record[9], 
					housing.Pv == record[10],housing.Shw  == record[11]):
						returned.append(house.Total_Energy_Use)
					values.append(np.mean(returned))
				else:
					values.append(np.mean(returned))
				#print(returned)
				returned = []

			count = 0	
			for i in values: #Ensures that all houses in a solution have a value (if they don't this corrupts the results)
				if i != i:
					print()
					print(sol)
					print()
					print(values)
					print()
					print(sol[count])
				count += 1

			#i = 0
			#print("BEFORE")
			#for h in self.pop[counter]:
			#	print(h, values[i])
			#	i += 1

			#If new a house in the new solution is not an improvement on the original house the original house is used in the solution not the evolved house
			h_count = 0 #counts through the houses in self.seed 
			for i in values:
				#print()
				#print("EVOLVED ", i)
				#print("ORGINAL ", self.seed[h_count][-1])
				if i > self.seed[h_count][-1]: #if the evolved houses energy usage score is higher than the unchanged house 
					#print("FOUND")
					#print("SOLUTION ", counter)
					#print("HOUSE ", h_count)
					self.pop[counter][h_count] = self.seed[h_count][:-1] #evolved house becomes unchanged house
					for i in range(len(self.pop[counter][h_count])):
						if self.pop[counter][h_count][i] != "0" and self.pop[counter][h_count][i] != "1": #HEY MORON STOP MAKING AGE BAND = 0
							if i != 1:
								self.pop[counter][h_count][i] = "0"
					values[h_count] = self.seed[h_count][-1] #the energy use value of the removed evolved house becomes the value of the unchanged house
				h_count += 1

			#i = 0
			#print("AFTER")
			#for h in self.pop[counter]:
			#	print(h, values[i])
			#	i += 1

			score  = [counter, sum(values)] #solution score is the sum of all houses in the solutions' scores, an index is also assigned so i know what solution the score corrisponds to
			pop_scores.append(score) #list of scores for each solution 
			values = [] #empy values list for next solution 
			counter += 1

		
		self.pop_scores = pop_scores


		counter = 0 #used to count which solution is being assessed
		house_costs = [] #list of costs for each house in a solution
		sol_costs = [] #a list of costs for each solution in the population, takes in the sum of house costs for each house in a solution
		pop_costs = [] #takes in the sum of all the house costs in a soulution, takes in the sum of sol_costs 

		#finds the cost for each house in a solution sums all the costs for the houses in a solution to get the cost of a solution 
		for sol in self.pop:
			index_counter = 0 #used to count through each house in the input file
			for record in sol: 
				if self.seed[index_counter][2] != record[2]:
					if self.seed[index_counter][2] == "1" or self.seed[index_counter][2] == "0":
						house_costs.append(self.cwi_cost) 

				if self.seed[index_counter][3] != record[3]:
					if self.seed[index_counter][3] == "1" or self.seed[index_counter][3] == "0":
						house_costs.append(self.loft_cost)

				if self.seed[index_counter][4] != record[4]:
					if self.seed[index_counter][4] == "1" or self.seed[index_counter][4] == "0":
						house_costs.append(self.dg_cost)

				if self.seed[index_counter][5] != record[5]:
					if self.seed[index_counter][5] == "1" or self.seed[index_counter][5] == "0":
						house_costs.append(self.cond_cost)

				if self.seed[index_counter][6] != record[6]:
					if self.seed[index_counter][6] == "1" or self.seed[index_counter][6] == "0":
						house_costs.append(self.swi_cost)
					
				if self.seed[index_counter][7] != record[7]:
					if self.seed[index_counter][7] == "1" or self.seed[index_counter][7] == "0":
						house_costs.append(self.ashp_cost)

				if self.seed[index_counter][8] != record[8]:
					if self.seed[index_counter][8] == "1" or self.seed[index_counter][8] == "0":
						house_costs.append(self.gsph_cost)

				if self.seed[index_counter][9] != record[9]:
					if self.seed[index_counter][9] == "1" or self.seed[index_counter][9] == "0":
						house_costs.append(self.bio_cost)

				if self.seed[index_counter][10] != record[10]:
					if self.seed[index_counter][10] == "1" or self.seed[index_counter][10] == "0":
						house_costs.append(self.pv_cost)
				
				if self.seed[index_counter][11] != record[11]:
					if self.seed[index_counter][11] == "1" or self.seed[index_counter][11] == "0":
						house_costs.append(self.shw_cost)

				score = sum(house_costs) #sum the total cost of the retrofitting for a house 
				sol_costs.append(score) #append the cost of each house to the solution cost list 
				house_costs = [] #empty housing cost list for the next house
				index_counter += 1

			sol_score = sum(sol_costs) #sum the house costs stored in sol costs to get the cost of a solution 
			sol_costs = [] #empty sol_cost list for the next solution 
			pop_costs.append(sol_score) #population cost list appends the cost of each solution
			sol_score = [] #empty the solution score list for the next solution


		# Add solution costs to the population scores list so this list shows the, index of the solution in the poulation, the total energy use of a solution
		#and the total cost of a solution 
		for sol in range(len(self.pop_scores)):
			self.pop_scores[sol].append(pop_costs[sol])






	# A dominates B if A is strictly better than B in one catagory and worse in none 
	def non_dominated_sort(self):
		S = [[] for i in range(0,len(self.pop_scores))] #A list of lists to store solutions dominated by target solution
		front = [[]] #A list of lists to store fronts 
		n = [0 for i in range(0,len(self.pop_scores))] #A list that shows how many solutions dominate each the target solution
		rank = [0 for i in range(0, len(self.pop_scores))] #A list that shows the rank of each solution

		for p in range(0,len(self.pop_scores)): #p is the target solution
			S[p] = [] 
			n[p] = 0 
			for q in range(0, len(self.pop_scores)): #q is the test solution
	        	#target solution dominates test solution if target solution is strictly better in at least one catagory and worse in none 
				if (self.pop_scores[p][1] < self.pop_scores[q][1] and self.pop_scores[p][2] < self.pop_scores[q][2]) or (self.pop_scores[p][1] <= self.pop_scores[q][1] and self.pop_scores[p][2] < self.pop_scores[q][2]) or (self.pop_scores[p][1] < self.pop_scores[q][1] and self.pop_scores[p][2] <= self.pop_scores[q][2]):
					if q not in S[p]:
						S[p].append(q) #store the index of the dominated solution in the list of dominated solutions 
	            #target solution is dominated by the test solution if the test solution is strictly better in at least one catagory and worse in none
				elif (self.pop_scores[q][1] < self.pop_scores[p][1] and self.pop_scores[q][2] < self.pop_scores[p][2]) or (self.pop_scores[q][1] <= self.pop_scores[p][1] and self.pop_scores[q][2] < self.pop_scores[p][2]) or (self.pop_scores[q][1] < self.pop_scores[p][1] and self.pop_scores[q][2] <= self.pop_scores[p][2]):
					n[p] = n[p] + 1 #Increase counter to show how many times target solution is dominated
			if n[p] == 0:
				rank[p] = 0
				if p not in front[0]:
					front[0].append(p) #If target is not dominated by any solution add to front 

		#This part of the code organises the solutions into fronts 
		i = 0
		while(front[i] != []): 
			Q=[]
			for p in front[i]:
				for q in S[p]:
					n[q] =n[q] - 1
					if( n[q]==0):
						rank[q]=i+1
						if q not in Q:
							Q.append(q) #if solution is only dominated by solutions that are already sorted into their frony add q to Q, Q = the next front
			i = i+1
			front.append(Q)
		del front[len(front)-1] 

		for i in range(len(rank)):
			pair = [i, rank[i]] #create solution index rank pairs 
			self.rank_crowd.append(pair) #append the index and rank score to the rank_crowd list 

		


	def crowding_distance(self):
		#method sets rank crowd to store an index referencing the solution then it is sorted primarily on rank and then by crowding distance

		#before calculating the crowding distance i remove any solutions that have a null value for energy usage scores 
		to_del = [] #stores the indexes for the solution that needs to be deleted 

		#Searches through population and stores the indexes of solutions with null values in the to_del list
		for i in range(len(self.pop_scores)):
			if self.pop_scores[i][1] != self.pop_scores[i][1]:
				to_del.append(self.pop_scores[i][0])

		

		counter = 0 #everytime a solution is deleted the counter will increase the counter will be taken away from the index number to delete this stops IndexErrors
		#removes the null values 
		for i in to_del:
			i = i - counter
			del self.pop_scores[i]
			counter += 1

		#Sort population by energy use and cost
		sorted_energy_use = sorted(self.pop_scores, key=itemgetter(1)) #creats a sorted list of the population sorted by energy use score, ascending order
		sorted_cost = sorted(self.pop_scores, key=itemgetter(2)) #creats a sorted list of the population sorted by cost score, ascending order
		
		#create two blank lists one for each objective to store distance scores
		distance_energy_use = []
		distance_cost = []
		#fill distance energy use list
		for i in sorted_energy_use:
			pair = [i[0],0]
			distance_energy_use.append(pair)

		#assign boundry values infinate values
		distance_energy_use[0][1] = 9999999999999999
		distance_energy_use[-1][1] = 9999999999999999

		#Now calculate the distance between each solution in the sorted energy use list
		for n in range(1, len(distance_energy_use) - 1):
			distance_energy_use[n][1] = distance_energy_use[n][1] + ((sorted_energy_use[n+1][1] + sorted_energy_use[n-1][1]) / (sorted_energy_use[-1][1] - sorted_energy_use[0][1]))

		#repeate the process for the cost objective
		for i in sorted_cost:
			pair = [i[0],0]
			distance_cost.append(pair)

		distance_cost[0][1] = 9999999999999999
		distance_cost[-1][1] = 9999999999999999

		#Now calculate the distance between each solution in the sorted cost list
		for n in range(1, len(distance_energy_use) - 1):
			try:
				distance_cost[n][1] = distance_cost[n][1] + ((sorted_cost[n+1][2] + sorted_cost[n-1][2]) / (sorted_cost[-1][2] - sorted_cost[0][2]))
			except ZeroDivisionError:
				distance_cost[n][1] = 0



		#Now i have the crowding distance for each solution with reguards to each objective combine the results to get the overall crowding distance 
		crowd_dist = [] #Holds the values for overall crowding distance 
		#first sort both distance_cost and distance_energy_use by their index
		distance_energy_use = sorted(distance_energy_use, key=itemgetter(0)) #creats a sorted list of the population sorted by energy use score, ascending order
		distance_cost = sorted(distance_cost, key=itemgetter(0)) #creats a sorted list of the population sorted by cost score, ascending order
		for i in range(len(distance_energy_use)):
			dist = distance_energy_use[i][1] + distance_cost[i][1] #combined crowding distance for each score 
			pair = [i, dist]
			crowd_dist.append(pair)


		for i in range(len(self.rank_crowd)):
			self.rank_crowd[i].append(crowd_dist[i][1])

		self.rank_crowd = sorted(self.rank_crowd,  key = itemgetter(2), reverse = True) #sorts my solutions by crowding distance descending order
		self.rank_crowd = sorted(self.rank_crowd, key =itemgetter(1)) #Then sort by my primary index rank

	def classic_crossover(self):
		"""
		Method to perform a classic crossover creates a random point and takes part of the new child solution from both parents
		also a repair operator is used toensures that the constraints applied to other solutions in the population are applied to the child solutions
		mutation is also applied in this method and the child solution is appended to the population 

		"""
		parent_pool = [] #Only solutions who have rank 0 can be parents 
		for i in self.rank_crowd:
			if i[1] == 0: 
				parent_pool.append(i[0])
		#This if statement ensure i always have at least 2 parents to chose from 
		if len(parent_pool) == 1:
			for i in self.rank_crowd:
				if i[1] == 1:
					parent_pool.append(i[0])
		
		parent1_pool_index = random.randint(0,len(parent_pool) - 1) #selects parent from the parent pool list 
		parent2_pool_index = random.randint(0,len(parent_pool) - 1)
		while parent1_pool_index == parent2_pool_index: #ensures that parent 1 and 2 are different solutions
			parent2_pool_index = random.randint(0,len(parent_pool) - 1)

		parent1_index = parent_pool[parent1_pool_index] #population list index for parent 1 and 2 
		parent2_index = parent_pool[parent2_pool_index]

		parent_pool = []
		parent1 = self.pop[parent1_index] #select the parent solutions from the popuation list 
		parent2 = self.pop[parent2_index]

		crossover_point = random.randint(3,10) #has to start at index 3 because age band and detached status must remain the same, and only to index 10 because index 11 is the final index
		child_house = [] #To store each house in the child solution
		child_solution = [] #To store each solution itself 

		#rules to enforce and coding 
		#cwi[2], loft[3], dg[4], cond[5], swi[6], ashp[7], gshp[8], bio[9], pv[10], shw[11]
		#cwi = 1 xor swi = 1
		# cond, ashp, gshp, bio are mutually exclusive
		#if cwi = 0 and loft = 0 and dg = 0 and cond = 1 , pv and shw == 0

		for i in range(len(parent1)): 
			crossover_point = random.randint(3,10)
			child_house.extend(parent1[i][0:crossover_point]) 
			child_house.extend(parent2[i][crossover_point:])
			#now i have a house for my child solution it needs to fit my restrictions:
			#checks that cwi and swi don't both equal 1
			if self.seed[i][2] == "1": #If cwi is present for the house in the input file ensure it is not removed and ensure swi is not added
				child_house[2] = "1"
				child_house[6] = "0"
			if self.seed[i][6] == "1": #If swi is present for the house in the input file ensure it is not removed and ensure swi is not added
				child_house[6] = "1"
				child_house[2] = "0"

			boilers = [] #this list will store all the boilers that equal 1 in the child house
			#ensures the boilers are mutually exclusive
			#first the boilers list stores the index of any boilers equalling 1 in the child house 
			if child_house[5] == "1":
				boilers.append(5)
			if child_house[7] == "1":
				boilers.append(7)
			if child_house[8] == "1":
				boilers.append(8)
			if child_house[9] == "1":
				boilers.append(9)

			if len(boilers) > 1: #If child house has more than 1 boiler 
				boiler_index = random.randint(0, len(boilers) - 1) #selects a random boiler from the list of boilers 
				boiler = boilers[boiler_index] #boiler is equal to an index in child house 
				#Ensures that only the randomly selected boiler == 1
				if boiler == 5:
					child_house[5] = "1"
					child_house[7] = "0"
					child_house[8] = "0"
					child_house[9] = "0"
					
				elif boiler == 7:
					child_house[5] = "0"
					child_house[7] = "1"
					child_house[8] = "0"
					child_house[9] = "0"
					
				elif boiler == 8:
					child_house[5] = "0"
					child_house[7] = "0"
					child_house[8] = "1"
					child_house[9] = "0"
					
				elif boiler == 9:
					child_house[5] = "0"
					child_house[7] = "0"
					child_house[8] = "0"
					child_house[9] = "1"

			#Ensure that if the house in the input file already has loft insulation,dg or solar panales that they are not removed in crossover
			if self.seed[i][3] == "1":
				child_house[3] = "1"
			if self.seed[i][4] == "1":
				child_house[4] = "1"
			if self.seed[i][11] == "1":
				child_house[11] = "1"
			if self.seed[i][10] == "1":
				child_house[10] = "1"


			#ensures if cwi = 0 and loft = 0 and dg = 0 and cond = 1 , pv and shw == 0
			if child_house[2] == "0":
				if child_house[3] == "0":
					if child_house[4] == "0":
						if child_house[5] == "1":
							if child_house[0] == "1":
								child_house[11] == "0"
								child_house[10] == "0"



			
			child_solution.append(child_house)
			child_house = []

		#mutate the new child solution 
		mutate_house = random.randint(0,len(child_solution) - 1) #can select any house in the child solution to apply the mutation too
		mutate_gene = random.randint(2,len(child_solution[0]) - 1) #can select any retrofit gene 

		#Ensure that the mutation does not breach the cwi and swi restriction
		if mutate_gene == 2: #cwi index
			if self.seed[i][2] == "0" or self.seed[i][2] == "1": #if cwi can be fitted 
				if child_solution[mutate_house][2] == "1": #if cwi is already fitted ensure it is not removed 
					child_solution[mutate_house][2] = "1"
				if child_solution[mutate_house][2] == "0": #if cwi is not fitted and swi is not fitted mutate cwi value 
					if child_solution[mutate_house][6] == "0":
						child_solution[mutate_house][2] = "1"
		

		if mutate_gene == 6: #swi index
			if self.seed[i][6] == "0" or self.seed[i][2] == "1": #if swi can be fitted
				if child_solution[mutate_house][6] == "1": #if swi is already fitted ensure it is not removed
					child_solution[mutate_house][6] = "1"
				if child_solution[mutate_house][6] == "0": #if swi is not fitted and cwi is not fitted mutate swi value 
					if child_solution[mutate_house][2] == "0":
						child_solution[mutate_house][6] = "1"
		

		#ensure mutual exclusivity is maintained amongst the boilers
		if mutate_gene == 5: #condensing boiler index
			if self.seed[i][5] == "0" or self.seed[i][5] == "1": #if a condensing boiler can be fitted
				if child_solution[mutate_house][5] == "0": #if condensing boiler is not already fitted fit it and ensure no other boilers are present 
					child_solution[mutate_house][5] = "1"
					child_solution[mutate_house][7] = "0"
					child_solution[mutate_house][8] = "0"
					child_solution[mutate_house][9] = "0" # if we mutate the value of a boiler from 0 to 1 ensure all other boilers are equal to

		if mutate_gene == 7: #ashp index
			if self.seed[i][7] == "0" or self.seed[i][7] == "1": #if air sourced heat pump can be fitted 
				if child_solution[mutate_house][7] == "0": #if ashp is not already fitted fit it and ensure no other boilers are present 
					child_solution[mutate_house][5] = "0"
					child_solution[mutate_house][7] = "1"
					child_solution[mutate_house][8] = "0"
					child_solution[mutate_house][9] = "0" # if we mutate the value of a boiler from 0 to 1 ensure all other boilers are equal to

		if mutate_gene == 8:
			if self.seed[i][8] == "0" or self.seed[i][8] == "1": #if ground sourced heat pump can be fitted 
				if child_solution[mutate_house][8] == "0": #if  gshp is not already fitted fit it and ensure all other boilers are equal to 0
					child_solution[mutate_house][5] = "0"
					child_solution[mutate_house][7] = "0"
					child_solution[mutate_house][8] = "1"
					child_solution[mutate_house][9] = "0" # if we mutate the value of a boiler from 0 to 1 ensure all other boilers are equal to

		if mutate_gene == 9:
			if self.seed[i][9] == "0" or self.seed[i][9] == "1": #if biomass heater can be fitted
				if child_solution[mutate_house][9] == "0": #if biomass heater is not already fitted  
					child_solution[mutate_house][5] = "0"
					child_solution[mutate_house][7] = "0"
					child_solution[mutate_house][8] = "0"
					child_solution[mutate_house][9] = "1" # if we mutate the value of a boiler from 0 to 1 ensure all other boilers are equal to

		#Ensure that solutions don't mutate loft insulation, dg, or solar panels to 0 if they are present in the input file 
		if mutate_gene == 3: #loft insulation
			if self.seed[i][3] == "1": #If the input file has loft insulation i don't want the mutation to remove this in the child solutions
				child_solution[mutate_house][3] = "1"
			if self.seed[i][3] == "0": #If input file does'nt have loft insulation it can mutate freely 
				if child_solution[mutate_house][3] == "1":
					child_solution[mutate_house][3] = "0"
				if child_solution[mutate_house][3] == "0":
					child_solution[mutate_house][3] = "1"
			if self.seed[i][3] != "1" and self.seed[i][3] != "0": #If it is not possible for the house to have loft insulation ensure the mutation does not cause it to occure
				child_solution[mutate_house][3] = "0"

		if mutate_gene == 4: #double glazing
			if self.seed[i][4] == "1": #If the input file has loft insulation i don't want the mutation to remove this in the child solutions
				child_solution[mutate_house][4] = "1"
			if self.seed[i][4] == "0": #If input file does'nt have loft insulation it can mutate freely 
				if child_solution[mutate_house][4] == "1":
					child_solution[mutate_house][4] = "0"
				if child_solution[mutate_house][4] == "0":
					child_solution[mutate_house][4] = "1"
			if self.seed[i][4] != "1" and self.seed[i][4] != "0": #If it is not possible for the house to have loft insulation ensure the mutation does not cause it to occure
				child_solution[mutate_house][4] = "0"

		#The final restiriction i need to code for is to prevent solutions that are not in the database 
		if mutate_gene == 10:
			if self.seed[i][10] == "0" or self.seed[i][10] == "1": #if the house can have pv fitted
				if child_solution[mutate_house][2] == "0":
					if child_solution[mutate_house][3] == "0": 
						if child_solution[mutate_house][4] == "0":
							if child_solution[mutate_house][5] == "1":
								if child_solution[mutate_house][0] == "1":
									pass #if this condition is met no mutation occures this generation
								else: #if condition is not met index may nutate freely
									if child_solution[mutate_house][10] == "0":
										child_solution[mutate_house][10] = "1"
									if child_solution[mutate_house][10] == "1":
										child_solution[mutate_house][10] = "0"
							else: #if condition is not met index may mutate freely 
								if child_solution[mutate_house][10] == "0":
									child_solution[mutate_house][10] = "1"
								if child_solution[mutate_house][10] == "1":
									child_solution[mutate_house][10] = "0"
						else: #if condition is not met index may freely mutate
							if child_solution[mutate_house][10] == "0":
								child_solution[mutate_house][10] = "1"
							if child_solution[mutate_house][10] == "1":
								child_solution[mutate_house][10] = "0"
					else: #if condition is not met this index may freely mutate
						if child_solution[mutate_house][10] == "0":
							child_solution[mutate_house][10] = "1"
						if child_solution[mutate_house][10] == "1":
							child_solution[mutate_house][10] = "0"
				else: #if the condition is not met this index may freely mutate
					if child_solution[mutate_house][10] == "0":
						child_solution[mutate_house][10] = "1"
					if child_solution[mutate_house][10] == "1":
						child_solution[mutate_house][10] = "0"

		if mutate_gene == 11:
			if self.seed[i][11] == "0" or self.seed[i][11] == "1":
				if child_solution[mutate_house][2] == "0":
					if child_solution[mutate_house][3] == "0": 
						if child_solution[mutate_house][4] == "0":
							if child_solution[mutate_house][5] == "1":
								if child_solution[mutate_house][0] == "1":
									pass #if this condition is met no mutation occures this generation 
								else:
									if child_solution[mutate_house][11] == "0":
										child_solution[mutate_house][11] = "1"
									if child_solution[mutate_house][11] == "1":
										child_solution[mutate_house][11] = "0"
							else: #if condition is not met index may mutate freely 
								if child_solution[mutate_house][11] == "0":
									child_solution[mutate_house][11] = "1"
								if child_solution[mutate_house][11] == "1":
									child_solution[mutate_house][11] = "0"
						else: #if condition is not met index may freely mutate
							if child_solution[mutate_house][11] == "0":
								child_solution[mutate_house][11] = "1"
							if child_solution[mutate_house][11] == "1":
								child_solution[mutate_house][11] = "0"
					else: #if condition is not met this index may freely mutate
						if child_solution[mutate_house][11] == "0":
							child_solution[mutate_house][11] = "1"
						if child_solution[mutate_house][11] == "1":
							child_solution[mutate_house][11] = "0"
				else: #if the condition is not met this index may freely mutate
					if child_solution[mutate_house][11] == "0":
						child_solution[mutate_house][11] = "1"
					if child_solution[mutate_house][11] == "1":
						child_solution[mutate_house][11] = "0"

		# 2,6,5,7,8,9,10,11,   3,4,

		self.pop.append(child_solution)


	def clean_up(self):
		"""
		This module pools all rank zero solutions and child solutions then removes all other solutions from the population
		"""
		survivors = [] #stores a list of all the solutions that survive the generation 
		for i in self.rank_crowd:
			if i[1] == 0: 
				survivors.append(i[0])

		for i in survivors:
			self.survivors.append(self.pop[i])	

		#reset population scores and population rank and crowding distance
		self.pop_scores = []
		self.rank_crowd = []
		self.pop = []

		#First the initial data is taken and the predicted energy use is removed 
		transform = []
		#The immutable part of the solution is removed from the seed and stored in the immutable variable 
		for i in self.seed: 
			transform.append(i[0:-1])
		seed = transform

		#The mutable part of the seed is stored in the retrofit variable 
		transform = []
		for i in self.seed:
			transform.append(i[2:])

		retrofit = transform

		#Now i have each record split in two the immutable parts are still stored in the initial seed and the mutable parts are in retrofit
		#Solitions have further rules is you have Cavity wall insulation you can't have solid wall insulation 
		#also condensing boilers, air source heat pumps, ground source heat pumps and biomass heaters are mutually exclusive 
		#FOR CODING PURPOSES ONLY DELETE LATER cwi[0], loft[1], dg[2], cond[3], swi[4], ashp[5], gshp[6], bio[7], pv[8], shw[9]
		counter = 0
		h_counter = 0 #used to assign detatched status and age band to each new solution,(these need to be the same as in the input file )
		while  counter < self.population_size:
			houses = [] #if user has a portfolio larger than 1 house each house in a solution is stored in houses which will be appended to the population
			for i in retrofit:
				detach = self.seed[h_counter][0]
				if self.seed[h_counter][2] != "0" and self.seed[h_counter][2] != "1": #if cwi equals any non binary value in the input file the house cant have it hence it always equals 0
					cwi = 0
				if self.seed[h_counter][6] == "1": #If the house in the input file has solid wall insulation it can't have cavity wall insulation 
					cwi = 0
					swi = 1
				if self.seed[h_counter][2] == "0" and self.seed[h_counter][6] != "1": #If in the input file cwi is not present then it can take a random value of 1 or 0
					cwi = random.randint(0,1) #Set value for cavity wall insulation
				if self.seed[h_counter][6] != "0" and self.seed[h_counter][6] != "1": #if swi equals any non binary value in the input file the house cant have it hence it always equals 0
					swi = 0
				if self.seed[h_counter][2] == "1": #If the house in the input file has cavity wall insulation it can't have solid wall insulation 
					swi = 0
					cwi = 1
				if self.seed[h_counter][6] == "0" and self.seed[h_counter][2] != "1": #If in the input file swi is not present then it can take a random value of 1 or 0
					swi = random.randint(0,1)

				if self.seed[h_counter][3] == "0":
					loft = random.randint(0,1) #set value for loft insulation
				if self.seed[h_counter][3] == "1":
					loft = 1
				if self.seed[h_counter][3] != "0" and self.seed[h_counter][3] != "1": #if a house can't have loft insulation
					loft = 0
				if self.seed[h_counter][4] == "0":
					dg = random.randint(0,1) #set value for double glaszing
				if self.seed[h_counter][4] == "1":
					dg = 1
				if self.seed[h_counter][4] != "1" and self.seed[h_counter][4] != "0":
					dg = 0

				#Boilers need to be mutually exclussive but houses won't neccesarily be able to fit all boilers so this block of code intends to 
				#check the input file and ensure that a house only has boilers it can actually have fitted in the population 
				invalid_boilers = [] #will store values if a house can't have a certain type of boiler fitted
				boiler_list = [5,7,8,9]
				#a selection of if statements to check which boilers a house can have 
				if self.seed[h_counter][5] != "1" and self.seed[h_counter][5] != "0":
					invalid_boilers.append(5) 
				if self.seed[h_counter][7] != "1" and self.seed[h_counter][7] != "0":
					invalid_boilers.append(7) 
				if self.seed[h_counter][8] != "1" and self.seed[h_counter][8] != "0":
					invalid_boilers.append(8) 
				if self.seed[h_counter][9] != "1" or self.seed[h_counter][9] != "0":
					invalid_boilers.append(9) 
				if len(invalid_boilers) != 4: #If the house can have at least one boiler
					boiler_index = random.randint(0,3) #select a boiler for each house they are mutually exclusive so only 1 can be selected
					boiler = boiler_list[boiler_index]
					while boiler in invalid_boilers: #if boiler is in the invalid boiler list keep changing the value until a valid boiler is selected 
						boiler_index = random.randint(0,3)
						boiler = boiler_list[boiler_index]
					if boiler == 5:
						cond = 1
						ashp = 0
						gshp = 0
						bio = 0
		
					if boiler == 7:
						cond = 0
						ashp = 1
						gshp = 0
						bio = 0
					if boiler == 8:
						cond = 0
						ashp = 0
						gshp = 1
						bio = 0
					if boiler == 9:
						cond = 0
						ashp = 0
						gshp = 0
						bio = 1	
				if len(invalid_boilers) == 4:
					cond = 0
					ashp = 0
					gshp = 0
					bio = 0

				if cwi == 0 & loft == 0 & dg == 0:
					if cond == 1:
						if detach == "1":
							pv = 0
							shw = 0
						else:
							if self.seed[h_counter][11] == "0": #If the house in the input file does not have solar hot water, randomly select if it has it or not in the population
								shw = random.randint(0,1)
							if self.seed[h_counter][11] == "1": #If the house in the input file already has solar hot water ensure it keeps solar hot water
								shw = 1
							if self.seed[h_counter][11] != "0" and self.seed[h_counter][11] != "1": #if house in the input file can't have solar hot water ensure it does not have solar hot water
								shw = 0
							if self.seed[h_counter][10] == "0": #If the house in the input file does not have solar panels, randomly select if it has it or not in the population
								pv = random.randint(0,1)
							if self.seed[h_counter][10] == "1": #If the house in the input file already has solar panels ensure it keeps solar panels.
								pv = 1
							if self.seed[h_counter][10] != "0" and self.seed[h_counter][10] != "1": #if house in the input file cant have solar panels ensure it does not occur in the population 
								pv = 0
					else:
						if self.seed[h_counter][11] == "0": #If the house in the input file does not have solar hot water, randomly select if it has it or not in the population
							shw = random.randint(0,1)
						if self.seed[h_counter][11] == "1": #If the house in the input file already has solar hot water ensure it keeps solar hot water
							shw = 1
						if self.seed[h_counter][11] != "0" and self.seed[h_counter][11] != "1": #if house in the input file can't have solar hot water ensure it does not have solar hot water
							shw = 0
						if self.seed[h_counter][10] == "0": #If the house in the input file does not have solar panels, randomly select if it has it or not in the population
							pv = random.randint(0,1)
						if self.seed[h_counter][10] == "1": #If the house in the input file already has solar panels ensure it keeps solar panels.
							pv = 1
						if self.seed[h_counter][10] != "0" and self.seed[h_counter][10] != "1": #if house in the input file cant have solar panels ensure it does not occur in the population 
							pv = 0

				else:
					if self.seed[h_counter][11] == "0": #If the house in the input file does not have solar hot water, randomly select if it has it or not in the population
						shw = random.randint(0,1)
					if self.seed[h_counter][11] == "1": #If the house in the input file already has solar hot water ensure it keeps solar hot water
						shw = 1
					if self.seed[h_counter][11] != "0" and self.seed[h_counter][11] != "1": #if house in the input file can't have solar hot water ensure it does not have solar hot water
						shw = 0
					if self.seed[h_counter][10] == "0": #If the house in the input file does not have solar panels, randomly select if it has it or not in the population
						pv = random.randint(0,1)
					if self.seed[h_counter][10] == "1": #If the house in the input file already has solar panels ensure it keeps solar panels.
						pv = 1
					if self.seed[h_counter][10] != "0" and self.seed[h_counter][10] != "1": #if house in the input file cant have solar panels ensure it does not occur in the population 
						pv = 0

				house = [] #Create an empty list to store the values of a new house 
				house.append(seed[h_counter][0]) #Set the age and and detached status equal to the house in the input data (we are retrofitting these things can't chang)
				house.append(seed[h_counter][1])
				h_counter += 1
				if h_counter == len(seed):
					h_counter = 0
				#append the retrofit values 
				cwi = str(cwi)
				house.append(cwi)
				loft = str(loft)
				house.append(loft)
				dg = str(dg)
				house.append(dg)
				cond = str(cond)
				house.append(cond)
				swi = str(swi)
				house.append(swi)
				ashp = str(ashp)
				house.append(ashp)
				gshp = str(gshp)
				house.append(gshp)
				bio = str(bio)
				house.append(bio)
				pv = str(pv)
				house.append(pv)
				shw = str(shw)
				house.append(shw)
				
				houses.append(house)
			counter += 1

			self.pop.append(houses)

	def analyse(self):
		"""
		At this stage my algorithm often makes strange recommendations such as removing cavity wall insulation and it sometimes make impossible recommendations
		such as replacing cavity wall insulation with solid wall insulation. At this stage i take my best solutions so far fix any anomolies and then review the solutions
		if any house has a worse energy performance than its initial performance this house is retuned to its initial setting so the system does not make any unneccisary 
		recommendations.  Then each solution can be broken down house by house and the changes made to each house can be shown to the user. For example if an input file
		has 3 houses and we have a population of 10, 2 of these solutions are rank 0 these solutions are each made up of 3 houses, if one of the houses in the solution has a worse 
		energy performance than the same house in the input file the program will keep that house as it is 
		"""
		recommended_sols = []
		for sol in self.rank_crowd:
			if sol[1] == 0:
				index = sol[0]
				if self.pop_scores[index][1] < self.total_init_score:
					recommended_sols.append(sol[0])

		#sol_counter = 0
		#file = open(r"C:\Users\Glenn's pc\Documents\Uni\Disertation\recommendation.txt", 'w') #file where the recommendations will be written to 
		#for i in recommended_sols:
		#	house_counter = 0
		#	print()
		#	print()
		#	print("SOLUTION ", sol_counter)
		#	file.write("Solution ") #Write solution to file
		#	file.write(str(sol_counter)) #write the solution number to file
		#	file.write(":\n") #Create a new line to write to start writing recommendations
		#	for house in self.pop[i]:
		#		print()
		#		print("house ", house_counter)
		#		file.write("\n")
		#		file.write("House") #write house to file
		#		file.write(str(house_counter)) #write the number of the house that the recommendation is being written for 
		#		file.write(":\n") #move to the next line
		#		for i in range(len(house)):
		#			if house[i] != self.seed[house_counter][i]:
		#				items = ["Detached", "Ageband", "Cavity Wall Insulation", "Loft Insulation", "Double Glazing", "Condensing Boiler", "Solid Wall Insulation",
		#				"Air Sourced Heat Pump", "Ground Sourced Heat Pump", "Biomass Heater", "Solar Panels", "Solar Heated Hot Water"]
		#				if self.seed[house_counter][i] == "0": 
		#					print("Add to House ", house_counter, " " , items[i])
		#					file.write("Add to House ")
		#					file.write(items[i])
		#					file.write("\n")
		#				if self.seed[house_counter][i] == "1":
		#					print("Remove From House: ", house_counter, " ", items[i])
		#					file.write("Remove From House ")
		#					file.write(items[i])
		#					file.write("\n")

#				house_counter += 1
#			sol_counter += 1
#		file.close() #close recommendation file

		print("RECOMENDATIONS: ",recommended_sols)
		recomendation_population = [] #will store the solutions from the population which the recommendations will be based on
		#check my population 
		#for i in self.pop:
		#	print(i)
		for i in recommended_sols: #recommended solutions are added to the recommended population list 
		#	print("OOOOOOO", self.pop[i])
			recomendation_population.append(self.pop[i])

		self.pop = recomendation_population #the population becomes the population of recomended solutions 
		del(recomendation_population) #recommendation population list is deleted as it is no longer needed

		engine = create_engine('sqlite:///housing.db', echo=False)
 
		# create a Session
		Session = sessionmaker(bind=engine)
		session = Session()

		returned = [] #Will store the values of total energy usage for each query 
		values = []
		pop_scores = [] #stores the sum of the total energy usage for each solution

		
		#Now the population is not constantly evolving i am going to append the energy usage of each house to each house in the solution and based on this score
		#i will then decide if the solution will use the house altered by the algorithm in the solution or the house in the input file, some houses don't improve
		# these are the houses which will return to their input value this will improve the energy usage score of the solution and the cost 
		counter = 0 #used to count which solution is being assessed
		for sol in self.pop: #for each solution in the population 
			for record in sol: #for each house in the solution 
	
				for house in session.query(housing).filter(housing.Detached == record[0], housing.Ageband == record[1], housing.Cwi == record[2], housing.Loft == record[3], 
					housing.Dg == record[4], housing.Cond == record[5], housing.Swi == record[6], housing.Ashp == record[7], housing.Gshp == record[8], housing.Bio == record[9], 
					housing.Pv == record[10], housing.Shw  == record[11]):
					returned.append(house.Total_Energy_Use)
				l = len(returned) # used to check if the database returns any results 

				#If the database returns no result the program removes age band and searches again
				if l == 0:
					for house in session.query(housing).filter(housing.Detached == record[0], housing.Cwi == record[2], housing.Loft == record[3], 
					housing.Dg == record[4], housing.Cond == record[5], housing.Swi == record[6], housing.Ashp == record[7], housing.Gshp == record[8], housing.Bio == record[9], 
					housing.Pv == record[10],housing.Shw  == record[11]):
						returned.append(house.Total_Energy_Use)
					values.append(np.mean(returned)) #returned stores several values for most houses so the value given is the mean of all these houses
				else:
					values.append(np.mean(returned))
				#print(returned)
				returned = [] #empty the returned list ready for the next house 
			value_counter = 0 #keeps track of which index in the value list needs to be appended 
			for house in self.pop[counter]: #for each house in a solution append the energy use score 
				house.append(values[value_counter]) 
				value_counter += 1 #keeps track of which index in the value list needs to be appended 
					 
			counter += 1 #increse the counter
			values = [] #empty the values list ready for the next solution 
		
		counter = 0 #used to count which solution is being assessed
		house_costs = [] #list of costs for each house in a solution
		sol_costs = [] #a list of costs for each solution in the population, takes in the sum of house costs for each house in a solution
		pop_costs = [] #takes in the sum of all the house costs in a soulution, takes in the sum of sol_costs 

		
		counter = 0 #used to index which solution in the population the costs need to be appended to 
		#finds the cost for each house in a solution sums all the costs for the houses in a solution to get the cost of a solution 
		for sol in self.pop:
			index_counter = 0 #used to count through each house in the input file
			#print(len(sol))
			for record in sol: 
				#print(index_counter)
				if self.seed[index_counter][2] != record[2]:
					if self.seed[index_counter][2] == "1" or self.seed[index_counter][2] == "0":
						house_costs.append(self.cwi_cost) 

				if self.seed[index_counter][3] != record[3]:
					if self.seed[index_counter][3] == "1" or self.seed[index_counter][3] == "0":
						house_costs.append(self.loft_cost)

				if self.seed[index_counter][4] != record[4]:
					if self.seed[index_counter][4] == "1" or self.seed[index_counter][4] == "0":
						house_costs.append(self.dg_cost)

				if self.seed[index_counter][5] != record[5]:
					if self.seed[index_counter][5] == "1" or self.seed[index_counter][5] == "0":
						house_costs.append(self.cond_cost)

				if self.seed[index_counter][6] != record[6]:
					if self.seed[index_counter][6] == "1" or self.seed[index_counter][6] == "0":
						house_costs.append(self.swi_cost)
					
				if self.seed[index_counter][7] != record[7]:
					if self.seed[index_counter][7] == "1" or self.seed[index_counter][7] == "0":
						house_costs.append(self.ashp_cost)

				if self.seed[index_counter][8] != record[8]:
					if self.seed[index_counter][8] == "1" or self.seed[index_counter][8] == "0":
						house_costs.append(self.gsph_cost)

				if self.seed[index_counter][9] != record[9]:
					if self.seed[index_counter][9] == "1" or self.seed[index_counter][9] == "0":
						house_costs.append(self.bio_cost)

				if self.seed[index_counter][10] != record[10]:
					if self.seed[index_counter][10] == "1" or self.seed[index_counter][10] == "0":
						house_costs.append(self.pv_cost)
				
				if self.seed[index_counter][11] != record[11]:
					if self.seed[index_counter][11] == "1" or self.seed[index_counter][11] == "0":
						house_costs.append(self.shw_cost)

				score = sum(house_costs) #sum the total cost of the retrofitting for a house 
				sol_costs.append(score) #append the cost of each house to the solution cost list 
				house_costs = [] #empty housing cost list for the next house
				index_counter += 1

		cost_counter = 0 #used to count for the list of costs for each house in the solution
		for sol in self.pop:
			for house in sol:
				house.append(sol_costs[cost_counter])
				cost_counter += 1




		#Summerise the energy saved by each solution and the overall cost of each solution 
		change_sol = [] # an empty list to store the change in energy use scores for each solution as long as the cost of each solution
		e_use = [] #stores the energy use for each house in the solution
		c_sol = [] #stores the cost of each house 
		sol_count = 0 #counts the solution being summed 
		for sol in self.pop:
			for house in sol:
				e_use.append(house[-2])
				c_sol.append(house[-1])
			#print("SOLUTION ", sol_count)
			#print(c_sol)
			bundle = [sol_count, sum(e_use), sum(c_sol)] #stores the current solution and its total energy use 
			change_sol.append(bundle)
			e_use = []
			c_sol = []
			sol_count += 1

		print("INITIAL")
		print(self.total_init_score)

		print("BEFORE")
		print(change_sol)

		for sol in change_sol: #for each solution in energy use sol
			sol[1] = self.total_init_score - sol[1]

		print("AFTER")
		print(change_sol)

		sol_counter = 0
		file = open(r"C:\Users\Glenn's pc\Documents\Uni\Disertation\recommendation.txt", 'w') #file where the recommendations will be written to 
		file.write("Thank You for using the Housing energy use optimiser, here are some recommendations to improve your housing portfolio")
		for sol in self.pop: #for each solution in the polution
			house_counter = 0
			print()
			print()
			print("SOLUTION ", sol_counter)
			file.write("\n")
			file.write("Solution ") #Write solution to file
			file.write(str(sol_counter)) #write the solution number to file
			file.write(":\n") #Create a new line to write to start writing recommendations
			file.write("Reduces Energy Usage By ")
			file.write(str(change_sol[sol_counter][1])) #how much the solution reduces energy usage by
			file.write(" KwH/Year")
			file.write("\n")
			file.write("Total Cost of Solution: £")
			file.write(str(change_sol[sol_counter][2]))
			file.write("\n")
			for house in sol: #for each house in a solution
				returned = []
				for h in session.query(housing).filter(housing.Detached == house[0], housing.Ageband == house[1], housing.Cwi == house[2], housing.Loft == house[3], 
				housing.Dg == house[4], housing.Cond == house[5], housing.Swi == house[6], housing.Ashp == house[7], housing.Gshp == house[8], housing.Bio == house[9], 
				housing.Pv == house[10], housing.Shw  == house[11]):
					returned.append(h.Total_Energy_Use)
				l =len(returned)
				if l == 0:
					for h in session.query(housing).filter(housing.Detached == house[0], housing.Cwi == house[2], housing.Loft == house[3], 
					housing.Dg == house[4], housing.Cond == house[5], housing.Swi == house[6], housing.Ashp == house[7], housing.Gshp == house[8], housing.Bio == house[9], 
					housing.Pv == house[10], housing.Shw  == house[11]):
						returned.append(h.Total_Energy_Use)

				improved = np.mean(returned) #Energy use after housing improvements
				initial = self.seed[house_counter][-1] #energy efficency of house before retrofitting
				change = initial - improved #energy efficiency of house post retrofitting
				print()
				print("INITIAL: ", initial)
				print("POST: ", improved)
				print("house ", house_counter)
				file.write("\n")
				file.write("House ") #write house to file
				file.write(str(house_counter)) #write the number of the house that the recommendation is being written for 
				file.write(". Upgrades improve this houses energy efficency by: ")
				file.write(str(change))
				file.write(" KwH/year")
				file.write(":\n") #move to the next line
				for i in range(len(house) -2): #for each retrofit variable
					if house[i] != self.seed[house_counter][i]:
						items = ["Detached", "Ageband", "Cavity Wall Insulation", "Loft Insulation", "Double Glazing", "Condensing Boiler", "Solid Wall Insulation",
						"Air Sourced Heat Pump", "Ground Sourced Heat Pump", "Biomass Heater", "Solar Panels", "Solar Heated Hot Water"]
						#I would like to add the cost of each improvement to the recommendation file 
						if i == 2:
							cost = self.cwi_cost
						if i == 3:
							cost = self.loft_cost
						if i == 4:
							cost = self.dg_cost
						if i == 5:
							cost = self.cond_cost
						if i == 6:
							cost = self.swi_cost
						if i == 7:
							cost = self.ashp_cost
						if i == 8:
							cost = self.gsph_cost
						if i == 9:
							cost = self.bio_cost
						if i == 10:
							cost = self.pv_cost
						if i == 11:
							cost = self.shw_cost

						if self.seed[house_counter][i] == "0": 
							print("Add to House ", house_counter, " " , items[i])
							file.write("Add to House ")
							file.write(items[i])
							file.write(". Cost of improvement: £")
							file.write(str(cost)) #cost of retrofit 
							file.write("\n")
						if self.seed[house_counter][i] == "1":
							print("Remove From House: ", house_counter, " ", items[i])
							file.write("Remove From House ")
							file.write(items[i])
							file.write(". Cost of removal: £")
							file.write(str(cost)) #cost of retrofit
							file.write("\n")

				house_counter += 1
			sol_counter += 1
		file.close() #close recommendation file






#needs to:
#Clean up
##To do this i will create a repopulate method
### Pools all the rank 0 solutions and the new child solutions (any solution after initial size of population) all other solutions retrofit vaiables are
### deleted and replaced with new random ones 
	
c = FileRead(r"C:\Users\Glenn's pc\Documents\Uni\Disertation\test_database.csv")
c.process()
init_set = c.assesment()

gen = Genetic(10,0.1,1)
gen.populate(init_set)
#print(gen.pop)

i = 0
while i != 10:
	gen.fit()
	#print(gen.pop_scores)
	gen.non_dominated_sort()
	gen.crowding_distance()	
	gen.classic_crossover()
	#print(gen.pop_scores)
	#print()
	#print(gen.rank_crowd)
	gen.clean_up()
	#print(len(gen.pop))
	i += 1
gen.fit()
gen.non_dominated_sort()
gen.crowding_distance()
#print()
#print(gen.rank_crowd)
gen.analyse()
#gen.fit()
print()
print(gen.total_init_score)
print()
print(gen.pop_scores)
print()
print(gen.rank_crowd)
#print(len(gen.pop))
for i in gen.seed:
	print(i)

for sol in gen.pop:
	print()
	for house in sol:
		print(house)
#after the while loop do one more loop with no clean up or creation of child solutions pick out the rank 0 solutions and return them in a readable way 
#Crossover needs work to ensure cwi and swi mutual exlusivity

#ensure we cant remove existing features
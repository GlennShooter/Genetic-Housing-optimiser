# Genetic-Housing-optimiser
takes some simple housing features and optimises energy usage while minimising costs.
This repository contains the three main parts of the program, this is currently a work in progress.  To test the program build database and
just run the genetic.py file

This repository contains
 - FileReader.py 
 - Database.py 
 - DatabaseFiller.py
 - Genetic.py
 - test_database.csv (file to test the program)
 - database_data.csv  (file to fill the database)
 
 To build the database download the database_data.csv file and run DatabaseFiller.py.  
 
 To use your own data ensure that you have the following in a column names in a csv file:
 -Detached (is the house detached)
 -AgeBand (corrosponds to the year the house was built)
 -Cwi (cavity wall insulation)
 -Loft (loft insulation)
 -Dg (Double Glazing)
 -Cond (Condensing Boiler)
 -Swi (Solid Wall Insulation)
 -Ashp (Air Sourced Heat Pump)
 -Gshp (Ground Sourced Heat Pump)
 -Bio (Biomass heater)
 -Pv (Photovoltic cells)
 -Shw (solar heated hot water)
All columns can only accept 1 or 0. 1 = present 0 = not present.  If a none binary value is applied to a column then it is assumed that
that house can't have that item fitted e.g if you represent loft with an 8 then the program will assume that the house can't have loft 
insulation fitted.

There are some further rules for specifying houses.
1. Cwi and Swi are mutually exclusive, you can have cavity wall insulation or solid wall insulation but not both.
2. There are 4 boiler types, Cond, Ashp, Gshp, Bio these are mutually exclusive.


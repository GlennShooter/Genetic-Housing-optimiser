from sqlalchemy import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
 
engine = create_engine('sqlite:///housing.db', echo=True)
Base = declarative_base()

########################################################################
class housing(Base):
    """"""
    __tablename__ = "housing"
 
    id = Column(Integer, primary_key=True)
    Detached = Column(Integer)
    Ageband = Column(Integer)
    Cwi = Column(Integer)
    Loft = Column(Integer)
    Dg = Column(Integer)
    Cond = Column(Integer)
    Swi = Column(Integer)
    Ashp = Column(Integer)
    Gshp = Column(Integer)
    Bio = Column(Integer)
    Pv = Column(Integer)
    Shw = Column(Integer)
    Total_Energy_Use = Column(Integer)

 
    #----------------------------------------------------------------------
    def __init__(self, Detached, Ageband, Cwi, Loft, Dg, Cond, Swi, Ashp, Gshp, Bio, Pv, Shw, Total_Energy_Use):
        """"""
        self.Detached = Detached
        self.Ageband = Ageband
        self.Cwi = Cwi
        self.Loft = Loft
        self.Dg = Dg
        self.Cond = Cond
        self.Swi = Swi
        self.Ashp = Ashp
        self.Gshp = Gshp
        self.Bio = Bio
        self.Pv = Pv
        self.Shw = Shw
        self.Total_Energy_Use = Total_Energy_Use

# create tables
Base.metadata.create_all(engine)
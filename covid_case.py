from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, PrimaryKeyConstraint
Base = declarative_base()


class CovidCase(Base):

    __tablename__ = 'covidcase'

    state = Column(String)
    sick = Column(Integer)
    healed = Column(Integer)
    die = Column(Integer)
    date = Column(DateTime)
    __table_args__ = (
        PrimaryKeyConstraint('date', 'state'),
        {},
    )

    def __init__(self, state, date):
        self.state = state
        self.date = date

    def __setitem__(self, key, value):
        setattr(self, key, value)    

    def __repr__(self):
        return f'{self.state}:{self.sick}|{self.healed}|{self.die} - {self.date}'

    def get_stats(self, obj):
        if self.state != obj.state:
            return None
        return (self.sick - obj.sick, self.healed - obj.healed, self.die - obj.die) 

    @classmethod
    def find_by_name(cls, session, state):
        return session.query(cls).filter(cls.state.like("%{}%".format(state))).order_by(cls.date.desc()).limit(2).all()


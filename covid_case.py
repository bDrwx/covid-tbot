from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, PrimaryKeyConstraint
Base = declarative_base()


class CovidCase(Base):

    __tablename__ = 'covidcase'

    title = Column(String)
    code = Column(String)
    is_city = Column(Boolean)
    coord_x = Column(Integer)
    coord_y = Column(Integer)
    sick = Column(Integer)
    healed = Column(Integer)
    died = Column(Integer)
    sick_incr = Column(Integer)
    healed_incr = Column(Integer)
    died_incr = Column(Integer)
    date = Column(DateTime)
    __table_args__ = (
        PrimaryKeyConstraint('date', 'code'),
        {},
    )

    def __init__(self, title, date):
        self.title = title
        self.date = date

    def __setitem__(self, key, value):
        setattr(self, key, value)    

    def __repr__(self):
        return f'{self.title}:{self.sick}|{self.healed}|{self.die} - {self.date}'

    def get_stats(self, obj):
        if self.title != obj.title:
            return None
        return (self.sick - obj.sick, self.healed - obj.healed, self.die - obj.die) 

    @classmethod
    def find_by_name(cls, session, title):
        return session.query(cls).filter(cls.title.like("%{}%".format(title))).order_by(cls.date.desc()).limit(2).all()


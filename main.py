import requests
from bs4 import BeautifulSoup
import dateparser
import re
from sqlalchemy import create_engine, Column, Integer, String,\
    DateTime, PrimaryKeyConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
    
    @classmethod
    def find_by_name(cls, session, state):
        return session.query(cls).filter(cls.state.like("%{}%".format(state))).all()


engine = create_engine('sqlite:///test.db', echo=True)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Sorce data from parsing
pagedata = requests.get("https://xn--80aesfpebagmfblc0a.xn--p1ai/")
soup = BeautifulSoup(pagedata.text, features="html.parser")

banner_div = soup.findAll("div", {"class": "cv-banner__description"})

# Parse datetime from string По состоянию на 03 апреля 10:30
human_date = re.match(r"^По состоянию на ([\d]{2}\s[\w]{3,6}\s[\d]{2}:[\d]{2})$", banner_div[0].text).group(1)
updated_time = dateparser.parse(human_date)


def save_to_base(session, state_list):
    try:
        session.bulk_save_objects(state_list)
        session.commit()
    except IntegrityError as e:
        print(f'Error record to DB {e}')
        session.rollback()


state_list = []
map_div = soup.find_all("div", {"class": "d-map__list"})
# print(f"{type(soup)} and {type(map_div)}")
tr_list = map_div[0].find_all("tr")
for tr in tr_list:
    covid_case = CovidCase(state=tr.th.text, date=updated_time)
    columns = tr.find_all('td')
    for column in columns:
        result = re.search(r"^d-map__indicator_([\w]+)$", column.span['class'][1])
        covid_case[result.group(1)] = column.text
    state_list.append(covid_case)

save_to_base(session, state_list)

print(CovidCase.find_by_name(session, 'Краснодар'))
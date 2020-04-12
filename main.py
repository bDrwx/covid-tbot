import requests
from bs4 import BeautifulSoup
import dateparser
import re
import os
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from covid_case import Base, CovidCase
from sqlalchemy import create_engine
import telebot


def init_db():
    engine = create_engine('sqlite:///test.db', echo=True)

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def save_to_base(session, state_list):
    try:
        session.bulk_save_objects(state_list)
        session.commit()
    except IntegrityError as e:
        print(f'Error record to DB {e}')
        session.rollback()


def get_data_from_web():

    # Sorce data from parsing
    pagedata = requests.get("https://xn--80aesfpebagmfblc0a.xn--p1ai/")
    soup = BeautifulSoup(pagedata.text, features="html.parser")

    banner_div = soup.findAll("div", {"class": "cv-banner__description"})

    # Parse datetime from string По состоянию на 03 апреля 10:30
    human_date = re.match(r"^По состоянию на ([\d]{2}\s[\w]{3,6}\s[\d]{2}:[\d]{2})$", banner_div[0].text).group(1)
    updated_time = dateparser.parse(human_date)

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
    return state_list

def main():
    session = init_db()
    covid_case_list = get_data_from_web()
    save_to_base(session, covid_case_list)
    bot = telebot.TeleBot(os.environ.get('BOT_KEY'))

    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        if message.text == "/covid":
            bot.send_message(message.from_user.id, "Какой регион Вас интересует?")
            bot.register_next_step_handler(message, get_covid_stats_by_region)
        elif message.text == "/help":
            bot.send_message(message.from_user.id, "Напиши привет")
        else:
            bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")

    @bot.message_handler(content_types=['text'])
    def get_covid_stats_by_region(message):
        cc = CovidCase.find_by_name(session, message.text)
        bot.send_message(message.from_user.id, cc[0])
        session.close()

    bot.polling(none_stop=True, interval=0)


if __name__ == "__main__":
    main()

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
import json


def init_db():
    engine = create_engine('sqlite:///test_upd.db', echo=True)

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
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    headers = {'User-Agent': user_agent}
    # Sorce data from parsing
    pagedata = requests.get("https://xn--80aesfpebagmfblc0a.xn--p1ai/information/",headers=headers)
    soup = BeautifulSoup(pagedata.text, features="html.parser")
    with open('sorce.html', 'w') as file:
        file.write(soup.prettify())

    banner_div = soup.find("small")
    # TODO Log this in debug mode
    print(banner_div.text)

    # Parse datetime from string По состоянию на 03 апреля 10:30
    human_date = re.match(r"^По состоянию на ([\d]{2}\s[\w]{3,6}\s[\d]{2}:[\d]{2})$", banner_div.text).group(1)
    updated_time = {'date': dateparser.parse(human_date)}

    map_div = soup.find("cv-spread-overview")
    state_list = json.loads(map_div[':spread-data'])
    new_state_list = [{**state, **updated_time} for state in state_list]
    
    return new_state_list


def main():
    session = init_db()
    covid_case_list = get_data_from_web()
    for state in covid_case_list:
        print(state)
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
        sick, healed, die = cc[0].get_stats(cc[1])

        text = (
            f'{cc[0].title} по состоянию на {cc[0].date}:\n'
            f'Выявлено:     {cc[0].sick:4}  +{sick:3} за последние сутки\n'
            f'Выздоровели:  {cc[0].healed:4}    +{healed:3} за последние сутки\n'
            f'Умерли:       {cc[0].die:4}   +{die:3} за последние сутки'
        )
        bot.send_message(message.from_user.id, text.encode('utf-8'))
        session.close()

    bot.polling(none_stop=True, interval=0)


if __name__ == "__main__":
    main()

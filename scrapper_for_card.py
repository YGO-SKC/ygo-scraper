import requests
import urllib.parse
from bs4 import BeautifulSoup
from collections import defaultdict
import re
import json

from db import *
from scrapper_for_product_details import get_soup_for_card_info


monster_sql = """\t, (
\t\t'{CARD_ID}', {CARD_COLOR_SQL}, '{CARD_NAME}', '{MONSTER_ATTRIBUTE}'
\t\t, "{CARD_EFFECT}"
\t\t, '{MONSTER_TYPE}', {MONSTER_ATK}, {MONSTER_DEF}, '{MONSTER_ASSOCIATION}'
\t)"""


spell_and_trap_sql = """\t, (
\t\t'{CARD_ID}', {CARD_COLOR_SQL}, '{CARD_NAME}', '{CARD_COLOR}'
\t\t, "{CARD_EFFECT}"
\t\t, '{CARD_PROPERTY}'
\t)"""

card_color_sql_dict = { 'Normal': '@normalCardColor', 'Effect': '@effectCardColor', 'Ritual': '@ritualCardColor', 'Fusion': '@fusionCardColor', 'Synchro': '@synchroCardColor', 'Xyz': '@xyzCardColor', 'Pendulum-Normal': 'pendulumNormalCardColor', 'Pendulum-Effect': '@pendulumCardColor', 'Pendulum-Fusion': 'pendulumFusionCardColor', 'Pendulum-Synchro': '@pendulumSynchroCardColor', 'Pendulum-Xyz': '@pendulumXyzCardColor', 'Link': '@linkCardColor', 'Spell': '@spellCardColor', 'Trap': '@trapCardColor' }

def double_quote_escape(item):
    return item.replace('"', '""')


def single_quote_escape(item):
    return item.replace("'", "''")


def get_card_details(cards_to_fetch_info_for):
    card_url = 'yugipedia.com/wiki/{CARD_NAME}'
    card_info_dict = defaultdict(list)

    for card_name in cards_to_fetch_info_for:
        soup = get_soup_for_card_info(card_url, card_name)

        card_name = soup.find('div', attrs={'class': 'card-table'}).find_all('div', attrs={'class': 'heading'})[0].text.strip()
        card_name = single_quote_escape(card_name)

        card_info_tr = soup.find('table', attrs={'class': 'innertable'}).find_all('tr')
        card_id = [tr for tr in card_info_tr if 'Password' in str(tr)][0].find('td').text.strip()

        card_color = [tr for tr in card_info_tr if 'Card type' in str(tr)][0].find('td').text.strip()
        if card_color not in ['Spell', 'Trap']:
            monster_types = [tr for tr in card_info_tr if 'Type' in str(tr)][0].find('td').text.strip().replace(' / ', '/')
            monster_types_cleaned = monster_types.replace('/Gemini', '').replace('/Flip', '') \
                .replace('/Toon', '').replace('/Spirit', '').replace('/Union', '').replace('/Tuner', "")

            # appending /Normal to Normal cards or /Effect to modernize older cards
            if '/' not in monster_types:
                monster_types_cleaned += '/Normal'
                monster_types += '/Normal'
            elif len(monster_types_cleaned.split('/')) == 1:
                monster_types_cleaned += '/Effect'
                monster_types += '/Effect'
            card_color = monster_types_cleaned.split('/')[1]


        card_effect = [tr for tr in card_info_tr if 'lore' in str(tr)][0].find('p')

        if card_effect is None:
            effects = [tr for tr in card_info_tr if 'lore' in str(tr)][0].find_all('dd')
            card_effect = 'Pendulum Effect\n' + effects[0].text.strip() + '\n\nMonster Effect\n' + effects[0].text.strip()
            card_color += '-'
            card_color += monster_types_cleaned.split('/')[2]
        else:
            for br in card_effect.find_all('br'):
                br.replace_with("\n")
            card_effect = card_effect.text.strip()
        card_effect = double_quote_escape(card_effect).replace('●', '\n&bull;').replace('\n\n&bull;', '\n&bull;')

        if 'FLIP:' in card_effect and monster_types.split('/')[1] != 'Flip':
            monster_types = monster_types.split('/')[0:1] + ['Flip'] + monster_types.split('/')[1:]
            monster_types = '/'.join(monster_types)


        if card_color in ['Spell', 'Trap']:
            card_property = [tr for tr in card_info_tr if 'Property' in str(tr)][0].find('td').find('p').a.text.strip()

            card_info_dict[card_color].append({ 'card_id': card_id, 'card_name': card_name, 'card_effect': card_effect, 'card_property': card_property })
        else:
            monster_attribute = [tr for tr in card_info_tr if 'Attribute' in str(tr)][0].find('p').find_all('a')[0].text.title()

            monster_atk = [tr for tr in card_info_tr if 'ATK' in str(tr)][0].find('td').text.strip().split('/')[0].strip()
            monster_atk = 'null' if monster_atk == '?' else monster_atk

            monster_def = [tr for tr in card_info_tr if 'ATK' in str(tr)][0].find('td').text.strip().split('/')[1].strip()
            monster_def = 'null' if monster_def == '?' else monster_def

            if card_color == 'Xyz':
                monster_association = {'rank': [tr for tr in card_info_tr if 'Rank' in str(tr)][0].find('p').find_all('a')[0].text}
            elif card_color == 'Link':
                link_rating = monster_def
                arrows = [tr for tr in card_info_tr if 'Link Arrows' in str(tr)][0].find('td').div.findChildren('div', recursive=False)[1].find_all('a')
                link_arrows = []
                for arrow in arrows:
                    link_arrows.append(re.sub('[a-z]*', '', arrow.text.strip()))
                monster_association = {'linkRating': link_rating, 'linkArrows': link_arrows}
            elif 'Pendulum' in card_color:
                scale = [tr for tr in card_info_tr if 'Pendulum Scale' in str(tr)][0].find('td').find('p').find_all('a')[1].text.strip()
                monster_association = {'level': [tr for tr in card_info_tr if 'Level' in str(tr)][0].find('p').find_all('a')[0].text, 'scaleRating': scale}
            else:
                monster_association = {'level': [tr for tr in card_info_tr if 'Level' in str(tr)][0].find('p').find_all('a')[0].text}

            monster_type = monster_types

            card_info_dict[card_color].append({ 'card_id': card_id, 'card_name': card_name, 'card_effect': card_effect, 'monster_atk': monster_atk, 'monster_def': monster_def, 'monster_type': monster_type, 'monster_attribute': monster_attribute, 'monster_association': json.dumps(monster_association) })

    return card_info_dict


def get_card_detail_queries(card_info_dict):
    for card_color, cards in card_info_dict.items():
        print(card_color)
        for card in cards:
            if card_color in ['Spell', 'Trap']:
                print(spell_and_trap_sql.format(CARD_ID=card['card_id'], CARD_COLOR_SQL=card_color_sql_dict[card_color], CARD_NAME=card['card_name'], CARD_COLOR=card_color, CARD_EFFECT=card['card_effect'], CARD_PROPERTY=card['card_property']))
            elif card_color == 'Link':
                print(monster_sql.replace(', {MONSTER_DEF}', '').format(CARD_ID=card['card_id'], CARD_COLOR_SQL=card_color_sql_dict[card_color], CARD_NAME=card['card_name'], MONSTER_ATTRIBUTE=card['monster_attribute'], CARD_EFFECT=card['card_effect'], MONSTER_TYPE=card['monster_type'], MONSTER_ATK=card['monster_atk'], MONSTER_ASSOCIATION=card['monster_association']))
            else:
                print(monster_sql.format(CARD_ID=card['card_id'], CARD_COLOR_SQL=card_color_sql_dict[card_color], CARD_NAME=card['card_name'], MONSTER_ATTRIBUTE=card['monster_attribute'], CARD_EFFECT=card['card_effect'], MONSTER_TYPE=card['monster_type'], MONSTER_ATK=card['monster_atk'], MONSTER_DEF=card['monster_def'], MONSTER_ASSOCIATION=card['monster_association']))
        print()


if __name__ == '__main__':
    dbConn, dbCursor = get_db_connections()

    query = "select card_name from cards where color_id = '12' and monster_association is NULL order by card_name"
    dbCursor.execute(query)
    cards = []
    for row in dbCursor.fetchall():
        cards.append(row[0])

    print(cards)
    exit
    card_info = get_card_details(cards)
    queries = get_card_detail_queries(card_info)
    print(queries)

    db_cleanup(dbConn, dbCursor)
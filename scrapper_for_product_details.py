import requests
import urllib.parse
from bs4 import BeautifulSoup

from db import *


product_info_query_prefix = """INSERT INTO product_details
\t(product_id, product_position, card_number, card_rarity, is_short_printed)
VALUES"""

find_card_with_id_query = 'select card_number from cards where card_number = {CARD_NUMBER}'.format(CARD_NUMBER='1')


def get_soup_for_card_info(card_url, card_name):
    url = 'https://' + urllib.parse.quote(card_url.format(CARD_NAME=card_name.replace('#', '')))
    card_info_html = requests.get(url)
    card_info_soup = BeautifulSoup(card_info_html.content, 'html.parser')

    # checks for table with class name "innertable", if it doesn't exist then there are two wiki pages with the
    # same name - one for a Card (wanted) and one for a product/character/etc.
    if card_info_soup.find('table', attrs={'class': 'innertable'}) is None:
        fixed_url = card_name + '_(card)'  # adds explicit page identifier for card info
        url = 'https://' + urllib.parse.quote(card_url.format(CARD_NAME=fixed_url.replace('#', '')))
        card_info_html = requests.get(url)
        card_info_soup = BeautifulSoup(card_info_html.content, 'html.parser')

    return card_info_soup


# get cards from tables with given id's
def get_pack_content_by_table_element(soup):
    pack_content = []
    tables = soup.find_all(class_='card-list')

    for table in tables:
        table_body = table.find('tbody')
        for tr in table_body.find_all('tr'):
            if tr.find('td') is not None:
                pack_content.append(tr)

    return pack_content



def get_product_details(soup):
    # Database connection
    dbConn, dbCursor = get_db_connections()

    pack_content = get_pack_content_by_table_element(soup)
    card_url = 'yugipedia.com/wiki/{CARD_NAME}'

    cards_not_in_db = []


    product_info_query_content_stub = """\t{COMMA}('{PRODUCT_ID}', '{CARD_POSITION}', '{CARD_ID}', '{RARITY}', {SHORT_PRINT})"""
    print(product_info_query_prefix)
    for index, row in enumerate(pack_content):
        short_print = 0

        # if index != 61: continue
        row = row.find_all('td')
        if len(row) > 0:

            card_position_and_pack_id = row[0].text.strip()
            card_position = card_position_and_pack_id.split('-EN')[1] if '-EN' in card_position_and_pack_id \
                             else card_position_and_pack_id.split('-')[1]
            product_id = card_position_and_pack_id.split('-')[0]

            card_name = row[1].text.strip()
            card_name = card_name[1:len(card_name) - 1].strip()

            if '" (as' in card_name:
                card_name = card_name.split('" (as')[0]
            elif '" (alternate art' in card_name:
                card_name = card_name.split('" (alternate art')[0]
            elif '" (Alternate art' in card_name:
                card_name = card_name.split('" (Alternate art')[0]
            elif '" ("' in card_name:
                card_name = card_name.split('" ("')[0]

            card_info_soup = get_soup_for_card_info(card_url, card_name)

            # Find table that contains info about password, get all rows from table, find the only row that references
            # the word Password (card id) and get the <td> content as that is where the password is
            card_id = [tr for tr in card_info_soup.find('table', attrs={'class': 'innertable'}).find_all('tr') if 'Password' in str(tr)][0].find('td').text.strip()

            # replaces <br /> with \n to get all unique rarities for each card.
            card_rarities = row[2]
            for br in card_rarities.find_all('br'):
                br.replace_with("\n")
            card_rarities = card_rarities.text.strip().splitlines()

            for rarity in card_rarities:
                if index > 1:
                    comma = ', '
                else:
                    comma = ''

                if 'Short' in rarity:
                    rarity = 'Common'
                    short_print = 1


                print(product_info_query_content_stub.format(PRODUCT_ID=product_id, CARD_POSITION=card_position, CARD_ID=card_id, RARITY=rarity, COMMA=comma, SHORT_PRINT=short_print))

            # check DB and see if current card in pack is new or not, if new add to list to fetch info about later
            if card_id != 'None':   # God cards/etc dont have card id
                dbCursor.execute('select card_number from cards where card_number = {CARD_NUMBER}'.format(CARD_NUMBER=card_id))
                if dbCursor.rowcount == 0:
                    cards_not_in_db.append(card_name)

    print(';')

    # close DB connection
    db_cleanup(dbConn, dbCursor)

    return cards_not_in_db
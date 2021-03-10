import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse


product_query_stub = ('INSERT INTO products\n'
                      '\t(product_id, product_locale, product_name, product_release_date, product_type, product_sub_type)\n'
                      'VALUES\n'
                      '\t(\'{PRODUCT_ID}\', \'EN\', \'{PRODUCT_NAME}\', \'{PRODUCT_RELEASE_DATE}\', \'{PRODUCT_TYPE}\', \'{PRODUCT_SUB_TYPE}\');')


def get_stat_from_product_info_table(stat, product_info_table):
    for row in product_info_table:
        th = row.find('th')
        td = row.find('td')
        if th is not None and th.text.strip() == stat:
            return td.text.strip()


def get_product_info(soup, product_type, product_sub_type):

    product_name = soup.find('h1', attrs={'id': 'firstHeading'}).text.strip().replace('Structure Deck: ', "")

    product_info_table = soup.find('table', attrs={'class': 'infobox list-noicon'}).find_all('tr')

    if get_stat_from_product_info_table('English (na)', product_info_table) is not None:
        product_release_date = parse(get_stat_from_product_info_table('English (na)', product_info_table)).date()
    else:
        product_release_date = parse(get_stat_from_product_info_table('English (world)', product_info_table)).date()

    product_id = \
    [product_id for product_id in get_stat_from_product_info_table('Prefix', product_info_table).splitlines() if
     'EN' in product_id or 'en' in product_id][0].split('-')[0]

    if ' ' in product_id.strip():
        product_id = product_id.split(' ')[0]

    return product_query_stub.format(PRODUCT_ID=product_id, PRODUCT_NAME=product_name,
                                    PRODUCT_RELEASE_DATE=product_release_date, PRODUCT_TYPE=product_type, PRODUCT_SUB_TYPE=product_sub_type)
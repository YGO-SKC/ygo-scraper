import requests
from bs4 import BeautifulSoup
from scrapper_for_product_info import get_product_info
from scrapper_for_product_details import get_product_details
from scrapper_for_card import get_card_details, get_card_detail_queries

product_url = input('Product URL: ')
product_type = input('Product Type: ')
product_sub_type = input('Product Sub Type: ')

html = requests.get(product_url)
soup = BeautifulSoup(html.content, 'html.parser')

print(get_product_info(soup, product_type, product_sub_type))
print()
cardsNotInDb = get_product_details(soup)

card_info_dict = get_card_details(cardsNotInDb)
get_card_detail_queries(card_info_dict)




# for key, value in card_info_dict.items():
#     print(key)
#     for item in value:
#         for k, v in item.items():
#             print(k, v)
#         print()
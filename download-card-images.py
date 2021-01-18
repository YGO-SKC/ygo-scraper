from db import *
import requests
import os


if __name__ == '__main__':
    dbConn, dbCursor = get_db_connections()

    sql = 'select card_number from cards;'
    dir = 'images'

    try:
        os.mkdir(dir)
    except OSError as error:
        print('Dir already created - skipping')

    dbCursor.execute(sql)


    for row in dbCursor.fetchall():
        filename = f'{row[0]}.jpg'
        skc_img_url = f'https://yugiohsiteimages.s3.us-east-2.amazonaws.com/{filename}'
        ygo_pro_img_url = f'https://storage.googleapis.com/ygoprodeck.com/pics_artgame/{filename}'


        req = requests.get(skc_img_url)
        if req.status_code != 200:
            print(f'card with id {row[0]} not found in SKC, trying to fetch from ygo pro')
            req = requests.get(ygo_pro_img_url, stream=True)
            if req.status_code == 200:
                req.raw.decode_content = True

                with open(f'{dir}/{filename}', 'wb') as file:
                    file.write(req.content)
                print('Image downloaded successfully')
            else:
                print(f'Image {filename} - not found')

    db_cleanup(dbConn, dbCursor) # Close dB connections
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
        img = f'https://storage.googleapis.com/ygoprodeck.com/pics_artgame/{filename}'

        req = requests.get(img, stream=True)
        if req.status_code == 200:
            req.raw.decode_content = True

            with open(f'{dir}/{filename}', 'wb') as file:
                file.write(req.content)
            print('Image downloaded successfully')
        else:
            print(f'Image {filename} - not found')

    db_cleanup(dbConn, dbCursor)
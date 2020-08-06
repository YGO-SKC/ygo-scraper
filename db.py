import pymysql

def get_db_connections():
    dbConn = pymysql.connect(host='localhost', user='root', passwd='', database='yugioh_API_DB')
    dbCursor = dbConn.cursor()

    return dbConn, dbCursor


def db_cleanup(dbConn, dbCursor):
    dbCursor.close()
    dbConn.commit()
    dbConn.close()
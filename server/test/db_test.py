import sys

sys.path.append('../')

from db.sqlalchemy import api as db_api
from db.sqlalchemy import models


if __name__ == '__main__':
    conf = {
        'driver':'mysql',
        'user': 'backup',
        'password': '123456',
        'host': '10.202.127.11',
        'database': 'test'
    }
    db = db_api.get_database(conf)
    print db.get_user_by_name('lucy')


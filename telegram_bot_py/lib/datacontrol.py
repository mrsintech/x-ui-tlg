import random
import json
import uuid
import datetime

from .sqlite_orm import SQLiteManager
from .server import Server

from dateutil.relativedelta import relativedelta


class XUI_DB(SQLiteManager):
    def __init__(self, host):
        self.host = host
        file = "C:\\Users\\mrsintech\\Desktop\\x-ui-english.db"
        SQLiteManager.__init__(self, file)

    @property
    def users_uuid(self):
        rows = self.get_table_rows_list('inbounds')
        uuids = []
        for row in rows:
            json_row = json.loads(row[11])
            uuids.append(json_row['clients'][0]['id'])

        return uuids

    @property
    def users_port(self):
        rows = self.get_table_rows_list('inbounds')
        ports = [row[9] for row in rows]
        return ports

    @property
    def users_phone(self):
        rows = self.get_table_rows_list('inbounds')
        phones = []
        for row in rows:
            json_row = json.loads(row[11])
            phones.append(json_row['clients'][0]['email'])

        return phones

    def generate_uuid(self):
        while True:
            new_uuid = str(uuid.uuid4())
            # make sure uuid is unique every time a new inbound added, because its not a good idea to change default sqlite behaviour that x-ui is using
            if new_uuid not in self.users_uuid:
                return new_uuid

    def generate_port(self):
        while True:
            new_port = random.randint(10000, 100000)
            # make sure uuid is unique every time a new inbound added, because its not a good idea to change default sqlite behaviour that x-ui is using
            if new_port not in self.users_port:
                return new_port

    def check_phone(self, phone):
        if phone in self.users_phone:
            raise ValueError(f"Duplicated phone value {phone}.")
        return phone

    def inbound_data(self, remark, phone, total_gb, expire_date, user_count):
        port = self.generate_port()
        settings = {
            "clients": [
                {
                    "id": self.generate_uuid(),
                    "flow": "xtls-rprx-direct",
                    "email": str(self.check_phone(phone)),
                    "limitIp": user_count,
                    "totalGB": total_gb,
                    "expiryTime": ""
                }
            ],
            "decryption": "none",
            "fallbacks": []
        }

        stream_settings = {
            "network": "ws",
            "security": "tls",
            "tlsSettings": {
                "serverName": self.host,
                "certificates": [
                    {
                        "certificateFile": "/root/cert.crt",
                        "keyFile": "/root/private.key"
                    }
                ],
                "alpn": "http/1.1"
            },
            "wsSettings": {
                "acceptProxyProtocol": False,
                "path": "/",
                "headers": {}
            }
        }

        sniffing = {
            "enabled": True,
            "destOverride": [
                "http",
                "tls"
            ]
        }

        settings_json = json.dumps(settings)
        stream_settings_json = json.dumps(stream_settings)
        sniffing_json = json.dumps(sniffing)

        inbound = {
            "id": self.get_table_rows_list('inbounds')[-1][0] + 1,
            # last inbound id + 1 # because sqlite isn't autoincrement :)
            "user_id": 1,
            "up": 0,
            "down": 0,
            "total": 0,
            "remark": remark,
            "enable": 1,
            "expiry_time": int(expire_date * 1000),
            "listen": "",
            "port": port,
            "protocol": "vless",
            "settings": settings_json,
            "stream_settings": stream_settings_json,
            "tag": "inbound-" + str(port),
            "sniffing": sniffing_json
        }
        return inbound

    def add_inbound(self, remark, phone, expire_date: datetime, total_gb=0, user_count=1):
        self.add_row('inbounds', **self.inbound_data(remark, phone, total_gb,
                                                     expire_date.timestamp(), user_count))

    def get_inbound_by_email(self, email):
        # TODO: add multiple kw support and relations
        query = f"SELECT * FROM inbounds WHERE settings LIKE '%{email}%';"
        self.cursor.execute(query)
        return self.cursor.fetchone()

class TelegramBotDB(SQLiteManager):
    def __init__(self):
        file = "tlg_bot.db"
        SQLiteManager.__init__(self, file)

    def migrate(self):
        query = "CREATE TABLE IF NOT EXISTS users (" \
                "chat_id INTEGER PRIMARY KEY," \
                "inbound_id TEXT NOT NULL, " \
                "is_active INTEGER DEFAULT 0);"
        self.cursor.execute(query)

        query = "CREATE TABLE IF NOT EXISTS pre_payment(" \
                "id INTEGER PRIMARY KEY," \
                "chat INTEGER," \
                "date_added TEXT," \
                "is_accepted INTEGER DEFAULT 0," \
                "data TEXT NOT NULL," \
                "total_amount INTEGER NOT NULL," \
                "FOREIGN KEY(chat) REFERENCES users(chat_id));"
        self.cursor.execute(query)

        self.commit()

    # def add_user_chat(self, chat_id, inbound_id):
    #     self.add_row('users', chat_id=chat_id, inbound_id=inbound_id, is_active=False)
    #     self.commit()
    #
    # def add_pre_payment(self):

if __name__ == '__main__':
    with TelegramBotDB() as db:
        db.migrate()
        # db.add_user_chat(32383, '(32, 33)')



import datetime
import sqlite3
import uuid
import json
import random

from server import Server
from dateutil.relativedelta import relativedelta


class SQLiteManager:

    def __init__(self, file):
        self.db_file = file
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print(f"An exception of type {exc_type} occurred with message: {exc_val}")

        self.conn.close()

    def get_table_rows_list(self, table):
        self.cursor.execute(f"SELECT * FROM {table};")
        columns = [column[0] for column in self.cursor.description]
        rows = self.cursor.fetchall()
        # TODO: remove this
        # print(list(enumerate(columns)))

        return rows

    def print(self, table):
        rows = self.get_table_rows_list(table)
        for row in rows:
            print(row)

    def delete_row(self, table, **kwargs):
        key, value = next(iter(kwargs.items()))
        self.cursor.execute(f"DELETE FROM {table} WHERE {key}=?;", (value,))
        self.conn.commit()

    def add_row(self, table, **kwargs):
        query = f"INSERT INTO {table} VALUES ({', '.join('?' for _ in kwargs)})"
        values = tuple(value for value in kwargs.values())
        self.cursor.execute(query, values)

    def get_latest_row_added(self, table):
        last_row_id = self.cursor.lastrowid
        # Fetch and return the created row
        latest_row_query = f"SELECT * FROM {table} WHERE id = ?"
        self.cursor.execute(latest_row_query, (last_row_id,))
        latest_row = self.cursor.fetchone()
        return latest_row

    def commit(self):
        self.conn.commit()

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

    def inbound_data(self, remark, phone, total_gb, expire_date):
        port = self.generate_port()
        settings = {
            "clients": [
                {
                    "id": self.generate_uuid(),
                    "flow": "xtls-rprx-direct",
                    "email": str(self.check_phone(phone)),
                    "limitIp": 0,
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

    def add_inbound(self, remark, phone, expire_date: datetime, total_gb=0):
        self.add_row('inbounds', **self.inbound_data(remark, phone, total_gb,
                                                     expire_date.timestamp()))


if __name__ == '__main__':
    with XUI_DB(host="test1.raptor.guru") as db:
        expire = datetime.datetime.now() + relativedelta(months=1)
        print(expire)
        db.add_inbound('test48856', 'test67079', expire)
        db.commit()
        db.print('inbounds')
        print(db.get_latest_row_added('inbounds'))

        # print(db.users_phone)
        # db.print('inbounds')
        Server()

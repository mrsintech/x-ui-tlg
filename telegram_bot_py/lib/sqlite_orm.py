import datetime
import sqlite3
import uuid
import json
import random

from .server import Server
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
        query = f"INSERT INTO {table} ({', '.join(item[0] for item in kwargs.items())}) " \
                f"VALUES({', '.join('?' for _ in kwargs.items())})"
        values = tuple(value for value in kwargs.values())
        self.cursor.execute(query, values)

    def comma_handler(self, command, all_items: dict):
        query = f'{command} '
        for item in enumerate(all_items.items()):
            query += f"{item[1][0]} = "
            if type(item[1][1]) == str:
                query += f'"{item[1][1]}" '
            else:
                query += f'{item[1][1]} '

            if len(all_items) > 1 and item[0] < len(all_items) - 1:
                query += ',\n'
            else:
                query += '\n'

        return query

    def update_row(self, table, update_data: dict, **kwargs):
        # prepare updated columns
        query = f"UPDATE {table}\n"
        query += self.comma_handler('SET', update_data)

        # prepare updated rows
        query += self.comma_handler('WHERE', kwargs)
        query = query.strip() + ";"
        print(query)
        self.cursor.execute(query)
        self.commit()

    def get_latest_row_added(self, table):
        last_row_id = self.cursor.lastrowid
        # Fetch and return the created row
        latest_row_query = f"SELECT * FROM {table} WHERE id = ?"
        self.cursor.execute(latest_row_query, (last_row_id,))
        latest_row = self.cursor.fetchone()
        return latest_row

    def get_row(self, table, **kwargs):
        key, value = next(iter(kwargs.items()))
        self.cursor.execute(f"SELECT * FROM {table} WHERE {key}=?;", (value,))
        return self.cursor.fetchone()
        # self.conn.commit()

    def commit(self):
        self.conn.commit()

if __name__ == "__main__":
    with SQLiteManager('tlg_bot.db') as db:
        db.update_row('users', update_data={'inbound_id': '[23, 22]', 'is_active':2}, chat_id=32383)

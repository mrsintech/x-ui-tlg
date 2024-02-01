import os
import sys
from .datacontrol import TelegramBotDB
from telegram_bot_py.main import app

@app.task
def remove_pre_payment(id):
    with TelegramBotDB() as db:
        db.delete_row('pre_peyment', id=id)


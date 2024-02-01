from celery import Celery

app = Celery('telegram_bot')
app.config_from_object('celery_config')




if __name__ == "__main__":
    from telegram_bot_py.lib.telegram_bot import TelegramBot
    TelegramBot()

import datetime
import json
import os
from typing import Final
import dotenv

import telegram.ext
from telegram.ext import (
    ConversationHandler,
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext,
)
import telegram as tlg

from .option_buttons import *
from .messages import *

from .celery_tasks import *
from .datacontrol import TelegramBotDB

dotenv.load_dotenv()

TOKEN: Final = os.environ['BOT_TOKEN']

ACC_BASE_PRICE = 120000
TWO_USERS_DISCOUNT_PERCENT = 5
TWO_MONTH_DISCOUNT_PERCENT = 5
MAX_NORMAL_DISCOUNT = 8

class TelegramBot:
    def __init__(self):

        # purchase states
        self.WAITING_FOR_ACC_TYPE = 0
        self.WAITING_FOR_EXPIRE_DATE = 1
        self.WAITING_FOR_PHONENUMBER = 2
        self.WAITING_FOR_PAYMENT = 3

        # setup bot
        print('Bot is starting...')
        app = Application.builder().token(TOKEN).build()

        # handlers
        app.add_handler(CommandHandler('start', self.start))
        app.add_handler(CommandHandler('custom', self.get))
        app.add_handler(MessageHandler(filters.Regex(f'^{MAIN_PAGE}$'), self.landing))
        app.add_handler(self.conv_purchase)

        # Error Handler
        app.add_error_handler(self.error)

        print("server is starting...")
        app.run_polling(poll_interval=1)

    @property
    def login_landing_menu(self):
        return [[SHOW_ACCOUNT_REMAIN], [BUY_EXTRA_GB, EXTEND_SERVICE], [SHOW_EXTRA_GB]]

    @property
    def no_login_landing_menu(self):
        return [[SHOW_PRICES, BUY_SERVICE], [GET_TEST_ACCOUNT, GET_DISCOUNT]]

    @property
    def account_type_menu(self):
        return [[ONE_USER_ACCOUNT, TWO_USER_ACCOUNT], [MAIN_PAGE]]

    @property
    def account_expire_menu(self):
        return [[ONE_MONTH_ACCOUNT, TWO_MONTH_ACCOUNT], [MAIN_PAGE]]

    @property
    def main_page_only_menu(self):
        return [[MAIN_PAGE]]

    @property
    def discount_menu(self):
        return [[I_HAVE_DISCOUNT], [MAIN_PAGE]]

    @property
    def conv_purchase(self) -> ConversationHandler:
        """
        stages:
        0 : enter type of account, 1 user or 2 users
        1 : process account_type and show message expire time of account 1 Month or 2 Months
        2:  process account time and show message enter phone number
        3 : process phonenumber and show total payment and creditcard number and ask user to do the payment and send invoice
        :return:
        """
        return tlg.ext.ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(f'^{BUY_SERVICE}$'), self.purchase)],
            states={
                self.WAITING_FOR_ACC_TYPE: [telegram.ext.MessageHandler(telegram.ext.filters.TEXT, self.process_account_type_and_ask_expire_in_purchase)],
                self.WAITING_FOR_EXPIRE_DATE: [MessageHandler(filters.TEXT, self.process_account_expire_and_ask_phonenumber_in_purchase)],
                self.WAITING_FOR_PHONENUMBER: [MessageHandler(filters.TEXT, self.process_phonenumber_and_show_invoice_and_ask_user_to_enter_discount_code)],
            },
            fallbacks=[MessageHandler(filters.Regex(f'^{MAIN_PAGE}$'), self.landing)]
        )

    # tools
    async def calculate_total_payment(self, purchase_data) -> int:
        total_payment = ACC_BASE_PRICE
        total_payment_without_discount = ACC_BASE_PRICE
        total_discount = 0

        if purchase_data['acc_type'] == TWO_USER_ACCOUNT:
            total_payment = total_payment * 2
            total_payment_without_discount = total_payment_without_discount * 2
            total_payment -= (total_payment * (TWO_USERS_DISCOUNT_PERCENT / 100))
            total_discount += TWO_USERS_DISCOUNT_PERCENT

        if purchase_data['expire_time'] == TWO_MONTH_ACCOUNT:
            total_payment = total_payment * 2
            total_payment_without_discount = total_payment_without_discount * 2
            total_payment -= (total_payment * (TWO_MONTH_DISCOUNT_PERCENT / 100))
            total_discount += TWO_MONTH_DISCOUNT_PERCENT

        if total_discount > MAX_NORMAL_DISCOUNT:
            total_payment = total_payment_without_discount - (
                        total_payment_without_discount * (MAX_NORMAL_DISCOUNT / 100))

        # TODO: add refferal functionality
        return total_payment

    async def save_pre_payment_to_db(self, update: tlg.Update, context: ContextTypes.DEFAULT_TYPE, total_payment: int):
        chat_id = update.effective_chat.id

        data = {
            'remark': ('[2U]' if context.user_data['acc_type'] == TWO_USER_ACCOUNT else '') + '@raptor_speed_bot',
            'acc_type': 2 if context.user_data['acc_type'] == TWO_USER_ACCOUNT else 1,
            'expire': 2 if context.user_data['expire_time'] == TWO_MONTH_ACCOUNT else 1,
            'phone': context.user_data['phone_number']
        }
        data_json = json.dumps(data)

        with TelegramBotDB() as tlg_db:
            user = tlg_db.get_row('users', chat_id=chat_id)
            if not user:
                tlg_db.add_row('users', chat_id=chat_id, inbound_id='[]', is_active=False)

            tlg_db.add_row(
                'pre_payment',
                chat=chat_id,
                date_added=str(datetime.datetime.now()),
                is_accepted=False,
                data=data_json,
                total_amount=total_payment
            )

            tlg_db.commit()
        return

    # commands
    async def start(self, update: tlg.Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_markdown_v2(
            f'سلام عزیز',
            reply_markup=tlg.ReplyKeyboardMarkup(
                self.no_login_landing_menu,
                # one_time_keyboard=True,
                resize_keyboard=True
            ),
        )

    async def get(self, update: tlg.Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(context.user_data)

    async def landing(self, update: tlg.Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_markdown_v2(
            f'یکی از گزینه های منو را انتخاب کنید',
            reply_markup=tlg.ReplyKeyboardMarkup(
                self.no_login_landing_menu,
                # one_time_keyboard=True,
                resize_keyboard=True
            ),
        )

    async def error(self, update: tlg.Update, context: ContextTypes.DEFAULT_TYPE):
        print(f'tlg.Update {update} caused error {context.error}')

    # conversation methods
    async def purchase(self, update: tlg.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        reply_markup = tlg.ReplyKeyboardMarkup(
            self.account_type_menu,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_markdown_v2(
                ENTER_ACCOUNT_TYPE,
                reply_markup=reply_markup,
            )
        return self.WAITING_FOR_ACC_TYPE

    async def process_account_type_and_ask_expire_in_purchase(self, update: tlg.Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message.text.lower()
        context.user_data['acc_type'] = message

        # next state prompt
        await update.message.reply_markdown_v2(
            ENTER_ACCOUNT_EXPIRE,
            reply_markup=tlg.ReplyKeyboardMarkup(
                self.account_expire_menu,
                one_time_keyboard=True,
                resize_keyboard=True
            ),
        )
        return self.WAITING_FOR_EXPIRE_DATE

    async def process_account_expire_and_ask_phonenumber_in_purchase(self,
                                                                     update: tlg.Update,
                                                                     context: ContextTypes.DEFAULT_TYPE):
        message = update.message.text.lower()
        context.user_data['expire_time'] = message

        # next state prompt
        await update.message.reply_markdown_v2(
            ENTER_PHONE_NUMBER,
            reply_markup=tlg.ReplyKeyboardMarkup(
                self.main_page_only_menu,
                one_time_keyboard=True,
                resize_keyboard=True
            ),
        )
        return self.WAITING_FOR_PHONENUMBER

    async def process_phonenumber_and_show_invoice_and_ask_user_to_enter_discount_code(self,
                                                                                       update: tlg.Update,
                                                                                context: ContextTypes.DEFAULT_TYPE):
        # process phone
        message = update.message.text.lower()
        context.user_data['phone_number'] = message

        # calculate total payment logic
        total_payment = await self.calculate_total_payment(context.user_data)

        # add chat info to db
        await self.save_pre_payment_to_db(update, context, total_payment)

        # set celery task to remove

        await update.message.reply_text(f"مبلغ قابل پرداخت: {int(total_payment)} تومان")

        # next state prompt
        await update.message.reply_markdown_v2(
            ENTER_DISCOUNT_CODE,
            reply_markup=tlg.ReplyKeyboardMarkup(
                self.discount_menu,
                one_time_keyboard=True,
                resize_keyboard=True
            ),
        )
        return ConversationHandler.END



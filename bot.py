#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Basic example for a bot that uses inline keyboards.
# This program is dedicated to the public domain under the CC0 license.
"""
import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import db
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


default_options = ["fr","sa","so"]
def create_doodle(bot, update):
    doodle_message_id = update.message.message_id + 1 # FIXME this doesn't seem safe - we need to retrieve the message id of the reply we're sending at the end of this method
    doodle_id = db.create_doodle(update.message.chat_id, doodle_message_id, ",".join(default_options))
    doodle = db.get_doodle(update.message.chat_id, doodle_message_id)

    keyboard = [[InlineKeyboardButton(o, callback_data=o) for o in default_options]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(format_doodle(doodle), reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)

def format_answer(answer):
    if answer == "YES":
        return "+"
    if answer == "NO":
        return "-"
    if answer == "MAYBE":
        return "~"
    return "?"

def right_pad(s, width):
    while len(s) < width:
        s = s+" "
    return s

def format_doodle(doodle):
    row_width = 3
    msg = "```\n" + right_pad("", 7) + "".join([right_pad(o, row_width) for o in doodle['options']]) + "\n"
    for user_name, answers in doodle['answers'].items():
        row = right_pad(user_name[:6], 7)
        for option in default_options:
            if option in answers:
                row += right_pad(format_answer(answers[option]), row_width)
            else:
                row += right_pad(format_answer(None), row_width)
        msg += row + "\n"

    msg += '\n```'
    return msg

ANSWERS = ["YES", "NO", "MAYBE"]

def cycle_answer(user, chat_id, message_id, option):
    doodle = db.get_doodle(chat_id, message_id)
    prev_answer = db.get_answer(doodle['id'], user.id, option)
    if not prev_answer:
        next_answer = ANSWERS[0]
    else:
        idx = ANSWERS.index(prev_answer)
        next_answer = ANSWERS[(idx+1)%len(ANSWERS)]
    logger.info("Set answer: (%s):%s" % (option, next_answer))
    db.set_answer(doodle['id'], user.id, user.first_name, option, next_answer)


def button(bot, update):
    query = update.callback_query

    cycle_answer(query.from_user, query.message.chat_id, query.message.message_id, query.data)
    new_doodle = db.get_doodle(query.message.chat_id, query.message.message_id)

    keyboard = [[InlineKeyboardButton(o, callback_data=o) for o in new_doodle['options']]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.edit_message_text(text=format_doodle(new_doodle),
                            parse_mode=telegram.ParseMode.MARKDOWN,
                            reply_markup=reply_markup,
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)


def start(bot, update):
    update.message.reply_text("Hi")

def help(bot, update):
    update.message.reply_text("Use /start to test this bot.")


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.environ['TELEGRAM_TOKEN'])

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('doodle', create_doodle))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()

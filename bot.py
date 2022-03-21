from cgitb import html
import logging
import pip._vendor.requests 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Bot
from telegram.ext import (Updater, 
CommandHandler, CallbackContext)

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    query = '''https://accounts.google.com/o/oauth2/v2/auth?scope=https://www.googleapis.com/auth/calendar.events.freebusy+https://www.googleapis.com/auth/calendar.events.public.readonly+https://www.googleapis.com/auth/calendar.calendarlist.readonly+https://www.googleapis.com/auth/calendar.freebusy+profile+email+openid&response_type=code&state=1125&redirect_uri=http://localhost:8080/api/super-groups/v1/auth/oauth2callback&client_id=239907579223-ucj8cf889nr0tfncfi87auhkadr0g70i.apps.googleusercontent.com&access_type=offline'''

   
    keyboard = [
        [
            InlineKeyboardButton("Authorize me", url = query),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    update.message.reply_text(f"Hi {user.first_name}, Please authorize me for continue to calendrive", reply_markup=reply_markup)

def agenda(update: Update, context: CallbackContext):
    url = f"https://postman-echo.com/post"
    chat_id_int = update.message.chat.id
    chat_id = str(chat_id_int)
    headers = {'chat_id': chat_id}
    payload = ""
    response = pip._vendor.requests.request("POST", url, headers=headers, data=payload)
    text = response.text
    update.message.reply_text(text)

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    token = '2058897666:AAG67ewdPuakUffXbAMeLBwf8hlR7KlBDXk'
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    
    agenda_handler = CommandHandler ('agenda', agenda)

    # Add CommandHandler to dispatcher that will be used for handling updates
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(agenda_handler)

    # Start the Bot
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
import logging
import pip._vendor.requests 
from typing import Tuple, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat, ChatMember, ParseMode, ChatMemberUpdated
from telegram.ext import (Updater, 
CommandHandler, CallbackContext, MessageHandler, Filters, ChatMemberHandler)

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
    user_id_int = update.message.from_user.id
    user_id = str(user_id_int)
    headers = {'user_id': user_id}
    response = pip._vendor.requests.request("POST", url, headers=headers)
    text = response.text
    update.message.reply_text(text)

def group(update: Update, context: CallbackContext):
    url = f"https://postman-echo.com/post"
    chat_id_int = update.message.chat.id
    chat_id = str(chat_id_int)
    headers = {'chat_id': chat_id}
    response = pip._vendor.requests.request("POST", url, headers=headers)
    text = response.text
    update.message.reply_text(text)

def extract_status_change(
    chat_member_update: ChatMemberUpdated,
) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = (
        old_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    )
    is_member = (
        new_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (new_status == ChatMember.RESTRICTED and new_is_member is True)
    )

    return was_member, is_member

def greet_chat_members(update: Update, context: CallbackContext) -> None:
    """Greets new users in chats"""
    member_name = update.chat_member.new_chat_member.user.mention_html()
    result = extract_status_change(update.chat_member)

    if result is None:
        return

    was_member, is_member = result
    
    if is_member:
        update.effective_chat.send_message(
            f"Welcome {member_name}!",
            parse_mode=ParseMode.HTML,
        )
    elif was_member and not is_member:
            return

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    token = '2058897666:AAG67ewdPuakUffXbAMeLBwf8hlR7KlBDXk'
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    
    agenda_handler = CommandHandler ('agenda', agenda)

    group_handler = CommandHandler ('group', group)

    # Add CommandHandler to dispatcher that will be used for handling updates
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(agenda_handler)
    dispatcher.add_handler(group_handler)

    dispatcher.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
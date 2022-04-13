import logging
from typing import Tuple, Optional
import pip._vendor.requests 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember, ParseMode, ChatMemberUpdated
from telegram.ext import (Updater, 
CommandHandler, CallbackContext, MessageHandler, Filters, ChatMemberHandler, ConversationHandler,CallbackQueryHandler)


logger = logging.getLogger(__name__)

#SEND THE USER

def start(update: Update, context: CallbackContext) -> int:
    """Send message on /start."""
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

# SEND THE USER_ID INTO A POSTMAN SERVER

def user(update: Update, context: CallbackContext):
    url = f"https://postman-echo.com/post"
    user_id_int = update.message.from_user.id
    user_id = str(user_id_int)
    headers = {'user_id': user_id}
    response = pip._vendor.requests.request("POST", url, headers=headers)
    text = response.text
    update.message.reply_text(text)

# SEND THE GROUP_ID INTO A POSTMAN SERVER

def group(update: Update, context: CallbackContext):
    url = f"https://postman-echo.com/post"
    chat_id_int = update.message.chat.id
    chat_id = str(chat_id_int)
    headers = {'chat_id': chat_id}
    response = pip._vendor.requests.request("POST", url, headers=headers)
    text = response.text
    update.message.reply_text(text)


# SAY HELLO TO A NEW CHAT MEMBER

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



# DELET AUDIO MESSAGES IN THE GROUP_CHAT

key = 'choise'
key2 = 'message'

# Stages of the ConversationHandler
CHOISES, ACTIVE_CHOISE, INACTIVE_CHOISE = range(3)


def delete(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Activate", callback_data='Activated'),
            InlineKeyboardButton("Inactivate", callback_data='Inactive')
        ],
        [
            InlineKeyboardButton("End", callback_data='End')
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_text = "Forbid audio messages\n"
    if context.user_data:
        status = context.user_data.get(key)
        reply_text += (f'Status: {status}')

    else:
        reply_text += (f'Status: Inactive')
    
    msg = context.bot.send_message(update.message.chat.id,reply_text, reply_markup=reply_markup)
    context.user_data[key2] = msg

    return CHOISES

def active_choise(update: Update, context: CallbackContext):
    query = update.callback_query
    status = query.data
    context.user_data[key] = status
    msg = context.user_data.get(key2)
    reply_text = f"Forbid audio messages\nStatus: {status}"
    keyboard = [
        [
            InlineKeyboardButton("Activate", callback_data='Activated'),
            InlineKeyboardButton("Inactivate", callback_data='Inactive')
        ],
        [
            InlineKeyboardButton("End", callback_data='End')
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = context.bot.edit_message_text(reply_text, query.message.chat.id, msg.message_id, reply_markup=reply_markup)
    context.user_data[key2] = msg
    return ACTIVE_CHOISE

def inactivate_choise(update:  Update, context: CallbackContext):
    query = update.callback_query
    status = query.data
    context.user_data[key] = status
    msg = context.user_data.get(key2)
    reply_text = f"Forbid audio messages\nStatus: {status}"
    keyboard = [
        [
            InlineKeyboardButton("Activate", callback_data='Activated'),
            InlineKeyboardButton("Inactivate", callback_data='Inactive')
        ],
        [
            InlineKeyboardButton("End", callback_data='End')
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = context.bot.edit_message_text(reply_text, query.message.chat.id, msg.message_id, reply_markup=reply_markup)
    context.user_data[key2] = msg
    return INACTIVE_CHOISE

def delete_audio(update: Update, context: CallbackContext) -> int: 
    chat_id = update.message.chat.id
    must_delete = update.message
    context.bot.deleteMessage(chat_id, 
                        must_delete.message_id)
    text = "audio messages arent allowed"
    context.bot.send_message(chat_id, text)

def end(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    context.user_data.clear()

    # query.answer()
    chat_id = query.message.chat.id
    text = "audio messages are allowed"
    context.bot.send_message(chat_id, text)
    return ConversationHandler.END




def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    TOKEN = '2058897666:AAG67ewdPuakUffXbAMeLBwf8hlR7KlBDXk'
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    
    user_handler = CommandHandler ('user', user)

    group_handler = CommandHandler ('group', group)


    # Add CommandHandler to dispatcher that will be used for handling updates
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(user_handler)
    dispatcher.add_handler(group_handler)
    dispatcher.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    # using for test

    conv_handler = ConversationHandler(
        entry_points = [
        CommandHandler('delete', delete)       
            ],

        states={
            CHOISES:[
                CallbackQueryHandler(active_choise, pattern='^' + 'Activated' + '$' ),
                CallbackQueryHandler(inactivate_choise, pattern='^' + 'Inactive' + '$'),
                ],
            INACTIVE_CHOISE:[
                CallbackQueryHandler(active_choise, pattern='^' + 'Activated' + '$' ),
                CommandHandler('delete', delete) 
                ],
            ACTIVE_CHOISE:[
                MessageHandler(Filters.voice, delete_audio),
                CallbackQueryHandler(inactivate_choise, pattern='^' + 'Inactive' + '$'),
                CommandHandler('delete', delete)
            ]
        },

        fallbacks= [
            CallbackQueryHandler(end, pattern='^' + 'End' + '$'),
        ],

        per_user=False,
    )

    updater.dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
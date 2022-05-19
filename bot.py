import logging
from typing import Tuple, Optional
import pip._vendor.requests 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember, ParseMode, ChatMemberUpdated
from telegram.ext import (Updater, 
CommandHandler, CallbackContext, MessageHandler, Filters, ChatMemberHandler, ConversationHandler,CallbackQueryHandler)

# Stages of Conv_handler
SELECTING_ACTION, MESSAGE_DELETE_INACTIVE, MESSAGE_DELETE_ACTIVED, MESSAGE_DELETE_TIME_CHOISE, MESSAGE_DELETE_ACTIVED_TIME_CHOISE, MESSAGE_DELETE_TIME_ACTIVED = range(6)

AUDIO_DELETE_ACTIVED, AUDIO_DELETE_INACTIVE = range(6,8)

AUDIO_DEL_ACTIVED_MSG_DEL_ACTIVED, AUDIO_DEL_ACTIVED_MSG_DEL_INACTIVE = range(8,10) 

AUDIO_DEL_ACTIVED_MSG_DEL_TIME_CHOISE = range(10,11)

#Constants:
MSG, AUDIO_DELETE_STATUS, AUDIO_DELETE_ACTIVED_STATUS, MESSAGE_DELETE_ACTIVED_STATUS, MESSAGE_DELETE_STATUS, SETINGS_MESSAGE_ID  = range(11,17)

# Callback querys
Closed, Messages, Open, Close, Set_time, Back, Activated, Inactive, Audio  = range(17,26)

var_list = []

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


def setings(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Opening hours", callback_data=str(Messages)),
            InlineKeyboardButton("Audio", callback_data=str(Audio))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(Close)) 
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    keyboard_messages = [
        [
            InlineKeyboardButton("Opening hours", callback_data=str(Messages)),
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(Close)) 
        ],
    ]
    reply_markup_messages = InlineKeyboardMarkup(keyboard_messages)
    
    reply_text = "Setings:\n"

    if update.message:
        chat_id = update.message.chat.id
        message_id = update.message.message_id
        context.user_data[SETINGS_MESSAGE_ID] = message_id
        jobs = check_job_if_exists(str(chat_id), context)

        if jobs == True:
            return MESSAGE_DELETE_TIME_ACTIVED

        elif context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS) and context.user_data.get(MESSAGE_DELETE_ACTIVED_STATUS):
            reply_text += "Messages: Forbidden"
            msg = context.bot.send_message(chat_id, reply_text, reply_markup=reply_markup_messages)
            context.user_data[MSG] = msg
            return AUDIO_DEL_ACTIVED_MSG_DEL_ACTIVED

        elif context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS):
            reply_text += "Audio messages: Forbidden"
            msg = context.bot.send_message(chat_id,reply_text, reply_markup=reply_markup)
            context.user_data[MSG] = msg
            return AUDIO_DELETE_ACTIVED
                
        elif context.user_data.get(MESSAGE_DELETE_ACTIVED_STATUS):
            reply_text += "Messages: Forbidden"
            msg = context.bot.send_message(chat_id,reply_text, reply_markup=reply_markup_messages)
            context.user_data[MSG] = msg
            return MESSAGE_DELETE_ACTIVED   
             
        else:
            reply_text += "Messages: Allowed"    
            msg = context.bot.send_message(chat_id,reply_text, reply_markup=reply_markup)
            context.user_data[MSG] = msg
            context.user_data[MESSAGE_DELETE_ACTIVED_STATUS] = False
            context.user_data[AUDIO_DELETE_ACTIVED_STATUS] = False
            return SELECTING_ACTION

    else:
        query = update.callback_query
        msg = context.user_data.get(MSG)
        chat_id = query.message.chat.id

        if context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS) and context.user_data.get(MESSAGE_DELETE_ACTIVED_STATUS):
            reply_text += "Messages: Forbidden"
            msg = context.bot.edit_message_text(reply_text,chat_id, msg.message_id, reply_markup=reply_markup_messages)
            return AUDIO_DEL_ACTIVED_MSG_DEL_ACTIVED
        
        elif context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS):
            reply_text += "Audio messages: Forbidden"
            msg = context.bot.edit_message_text(reply_text,chat_id, msg.message_id, reply_markup=reply_markup)
            return AUDIO_DELETE_ACTIVED

        elif context.user_data.get(MESSAGE_DELETE_ACTIVED_STATUS):
            reply_text += "Messages: Forbidden"
            msg = context.bot.edit_message_text(reply_text,chat_id, msg.message_id, reply_markup=reply_markup_messages)
            return MESSAGE_DELETE_ACTIVED

        else:
            reply_text += "Messages: Allowed"
            msg = context.bot.edit_message_text(reply_text,chat_id, msg.message_id, reply_markup=reply_markup)
            return SELECTING_ACTION

def end_conv_handler(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()
    chat_id = update.message.chat_id
    reply_text = 'ConversationHandler ended'
    context.bot.send_message(chat_id,reply_text)
    return ConversationHandler.END

def close_setings(update: Update, context: CallbackContext) -> int:
    """Delete the keyboard buttons"""
    query = update.callback_query
    chat_id = query.message.chat.id
    must_delete = query.message
    context.bot.deleteMessage(chat_id, 
                        must_delete.message_id)

    """Delete the /setings"""
    message_id_setings = context.user_data.get(SETINGS_MESSAGE_ID)
    context.bot.delete_message(chat_id, message_id_setings)


""" DELET AUDIO MESSAGES IN THE GROUP_CHAT """

def audio_delete_status(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat.id
    msg = context.user_data.get(MSG)
    keyboard = [
        [
            InlineKeyboardButton("Active", callback_data=str(Activated)),
            InlineKeyboardButton("Inactive", callback_data=str(Inactive))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_text = "Forbid audio messages\n"
    
    if context.user_data.get(AUDIO_DELETE_STATUS):
        status = context.user_data.get(AUDIO_DELETE_STATUS)
        reply_text += (f'Status: {status}')

    else:
        reply_text += (f'Status: Inactive')
    
    msg = context.bot.edit_message_text(reply_text,chat_id, msg.message_id, reply_markup=reply_markup)
    context.user_data[MSG] = msg
    
    if context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS):
        return AUDIO_DELETE_ACTIVED
    else: 
        return AUDIO_DELETE_INACTIVE

def audio_delete_actived(update: Update, context: CallbackContext):
    query = update.callback_query
    status = 'Activated'
    context.user_data[AUDIO_DELETE_STATUS] = status
    msg = context.user_data.get(MSG)
    reply_text = f"Forbid audio messages\nStatus: {status}"
    keyboard = [
        [
            InlineKeyboardButton("Active", callback_data=str(Activated)),
            InlineKeyboardButton("Inactive", callback_data=str(Inactive))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = context.bot.edit_message_text(reply_text, query.message.chat.id, msg.message_id, reply_markup=reply_markup)
    context.user_data[MSG] = msg
    context.user_data[AUDIO_DELETE_ACTIVED_STATUS] = True

    return AUDIO_DELETE_ACTIVED

def audio_delete_inactive(update:  Update, context: CallbackContext):
    query = update.callback_query
    status = 'Inactive'
    context.user_data[AUDIO_DELETE_STATUS] = status
    msg = context.user_data.get(MSG)
    reply_text = f"Forbid audio messages\nStatus: {status}"
    keyboard = [
        [
            InlineKeyboardButton("Active", callback_data=str(Activated)),
            InlineKeyboardButton("Inactive", callback_data=str(Inactive))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = context.bot.edit_message_text(reply_text, query.message.chat.id, msg.message_id, reply_markup=reply_markup)
    context.user_data[MSG] = msg
    context.user_data[AUDIO_DELETE_ACTIVED_STATUS] = False

    return AUDIO_DELETE_INACTIVE

def audio_delete(update: Update, context: CallbackContext) -> int: 
    chat_id = update.message.chat.id
    must_delete = update.message
    context.bot.deleteMessage(chat_id, 
                        must_delete.message_id)

    if context.user_data.get(MESSAGE_DELETE_ACTIVED_STATUS) == False:
        text = "audio messages arent allowed"
        context.bot.send_message(chat_id, text)


"""Delete all messages in group chat"""

def message_delete_status(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    chat_id = query.message.chat.id
    msg = context.user_data.get(MSG)
    keyboard = [
        [
            InlineKeyboardButton("Closed", callback_data=str(Closed)),
            InlineKeyboardButton("Open", callback_data=str(Open))
        ],
        [
            InlineKeyboardButton("Set time", callback_data=Set_time)
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_text = "Set opening hours\n"
    if context.user_data.get(MESSAGE_DELETE_STATUS):
        status = context.user_data.get(MESSAGE_DELETE_STATUS) 
        reply_text += (f'Status: {status}\n')

    else:
        context.user_data[MESSAGE_DELETE_STATUS] = 'Open'
        reply_text += (f'Status: Open')
    
    msg = context.bot.edit_message_text(reply_text,chat_id, msg.message_id, reply_markup=reply_markup)
    
    context.user_data[MSG] = msg

    if context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS) and context.user_data.get(MESSAGE_DELETE_ACTIVED_STATUS):
        return AUDIO_DEL_ACTIVED_MSG_DEL_ACTIVED
    elif context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS):
        return AUDIO_DEL_ACTIVED_MSG_DEL_INACTIVE
    elif context.user_data.get(MESSAGE_DELETE_ACTIVED_STATUS):   
        return MESSAGE_DELETE_ACTIVED
    else:
        return MESSAGE_DELETE_INACTIVE

def message_delete_actived(update: Update, context: CallbackContext):
    query = update.callback_query
    status = 'Closed'

    context.user_data[MESSAGE_DELETE_STATUS] = status  
    msg = context.user_data.get(MSG)

    keyboard = [
        [
            InlineKeyboardButton("Closed", callback_data=str(Closed)),
            InlineKeyboardButton("Open", callback_data=str(Open))
        ],
        [
            InlineKeyboardButton("Set time", callback_data=str(Set_time))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    reply_text = f"Set opening hours\nStatus: {status}\n"
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_id = query.message.chat.id

    msg = context.bot.edit_message_text(reply_text, chat_id, msg.message_id, reply_markup=reply_markup)

    if context.user_data[MESSAGE_DELETE_ACTIVED_STATUS] == False: 

        reply_text = 'Messages sent will be deleted'
        context.bot.send_message(chat_id,reply_text)
    
    context.user_data[MSG] = msg
    context.user_data[MESSAGE_DELETE_ACTIVED_STATUS] = True

    if context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS):
        return AUDIO_DEL_ACTIVED_MSG_DEL_ACTIVED     
    else:
        return MESSAGE_DELETE_ACTIVED

def message_delete_inactive(update:  Update, context: CallbackContext):
    query = update.callback_query
    status = 'Open'
    chat_id = query.message.chat.id
    context.user_data[MESSAGE_DELETE_STATUS] = status
    msg = context.user_data.get(MSG)
    reply_text = f"Set opening hours\nStatus: {status}"
    keyboard = [
        [
            InlineKeyboardButton("Closed", callback_data=str(Closed)),
            InlineKeyboardButton("Open", callback_data=str(Open))
        ],
        [
            InlineKeyboardButton("Set time", callback_data=str(Set_time))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]
    
    remove_job_if_exists(str(chat_id), context)
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = context.bot.edit_message_text(reply_text, chat_id, msg.message_id, reply_markup=reply_markup)
    
    if context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS) and context.user_data[MESSAGE_DELETE_ACTIVED_STATUS]:
        reply_text = 'Text messages allowed'
        context.bot.send_message(chat_id,reply_text)
    else: 
        if context.user_data[MESSAGE_DELETE_ACTIVED_STATUS]:
            reply_text = 'Messages allowed'
            context.bot.send_message(chat_id,reply_text)

    context.user_data[MSG] = msg
    context.user_data[MESSAGE_DELETE_ACTIVED_STATUS] = False

    if context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS):
        return AUDIO_DEL_ACTIVED_MSG_DEL_INACTIVE
    else:
        return MESSAGE_DELETE_INACTIVE

def message_delete_time(update: Update, context: CallbackContext):
    query = update.callback_query
    msg = context.user_data.get(MSG)
    reply_text = f"Set time for deleting messages"
    keyboard = [
        [
            InlineKeyboardButton("5s", callback_data=str(Activated))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = context.bot.edit_message_text(reply_text, query.message.chat.id, msg.message_id, reply_markup=reply_markup)

    if context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS) and context.user_data.get(MESSAGE_DELETE_ACTIVED_STATUS):
        return MESSAGE_DELETE_ACTIVED_TIME_CHOISE

    elif context.user_data.get(AUDIO_DELETE_ACTIVED_STATUS):  
        return AUDIO_DEL_ACTIVED_MSG_DEL_TIME_CHOISE

    elif context.user_data.get(MESSAGE_DELETE_ACTIVED_STATUS):
        return MESSAGE_DELETE_ACTIVED_TIME_CHOISE

    else:
        return MESSAGE_DELETE_TIME_CHOISE


def message_delete_time_active(update: Update, context: CallbackContext):
    query = update.callback_query

    chat_id = query.message.chat.id
    msg = context.user_data.get(MSG)
      
    remove_job_if_exists(str(chat_id), context)

    context.job_queue.run_once(send_message_job, 5, context=chat_id, name=str(chat_id))

    context.bot.deleteMessage(chat_id, 
                        msg.message_id)

    reply_text = "Messages arent allowed for the next 5 seconds"
    context.bot.send_message(chat_id, reply_text)

    context.user_data[MESSAGE_DELETE_ACTIVED_STATUS] = False
    context.user_data[MESSAGE_DELETE_STATUS] = "Open"

    return MESSAGE_DELETE_TIME_ACTIVED
  

def send_message_job(context: CallbackContext):
    job = context.job
    context.bot.send_message(job.context, text='Messages are allowed')
    var = 'teste'
    var_list.append(var)

def remove_job_if_exists(name: str,context: CallbackContext):
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        var_list.clear()
        job.schedule_removal()
    return True

def check_job_if_exists(name: str,context: CallbackContext):
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    else:
        return True

def delete_messages_job(update: Update, context: CallbackContext) -> int: 

    if var_list != []:
        var_list.clear()
        if context.user_data[AUDIO_DELETE_ACTIVED_STATUS]:
            return AUDIO_DELETE_ACTIVED
        else:
            return SELECTING_ACTION
    chat_id = update.message.chat.id
    must_delete = update.message
    context.bot.deleteMessage(chat_id, 
                        must_delete.message_id)

def message_delete(update: Update, context: CallbackContext) -> int: 
    chat_id = update.message.chat.id
    must_delete = update.message
    context.bot.deleteMessage(chat_id, 
                        must_delete.message_id)    



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
            CommandHandler('setings', setings),    
            ],
        states={
            SELECTING_ACTION:[
            CallbackQueryHandler(audio_delete_status, pattern='^' + str(Audio) + '$'),
            CallbackQueryHandler(message_delete_status, pattern='^' + str(Messages) + '$'),
            CommandHandler('setings', setings),
            CallbackQueryHandler(close_setings, pattern='^' + str(Close) + '$'),
            ],
            MESSAGE_DELETE_INACTIVE:[
                CallbackQueryHandler(message_delete_actived, pattern='^' + str(Closed) + '$'),
                CallbackQueryHandler(message_delete_time, pattern='^' + str(Set_time) + '$'), 
                CallbackQueryHandler(message_delete_status, pattern='^' + str(Messages) + '$'),
                CallbackQueryHandler(setings, pattern='^' + str(Back) + '$'),
                CommandHandler('setings', setings),
            ],        
            MESSAGE_DELETE_ACTIVED:[
                MessageHandler(~Filters.command, message_delete),
                CallbackQueryHandler(message_delete_inactive, pattern='^' + str(Open) + '$'),
                CallbackQueryHandler(message_delete_time, pattern='^' + str(Set_time) + '$'), 
                CallbackQueryHandler(message_delete_status, pattern='^' + str(Messages) + '$'),
                CallbackQueryHandler(setings, pattern='^' + str(Back) + '$'),
                CommandHandler('setings', setings),
                CallbackQueryHandler(close_setings, pattern='^' + str(Close) + '$'),          
            ],
            MESSAGE_DELETE_TIME_CHOISE: [
                CallbackQueryHandler(message_delete_status, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(message_delete_time_active, pattern='^' + str(Activated) + '$'),
                CommandHandler('setings', setings),
            ],  
            MESSAGE_DELETE_ACTIVED_TIME_CHOISE:[
                MessageHandler(~Filters.command, message_delete),
                CallbackQueryHandler(message_delete_status, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(message_delete_time_active, pattern='^' + str(Activated) + '$'),
                CommandHandler('setings', setings),
            ],
            AUDIO_DELETE_INACTIVE:[
                CallbackQueryHandler(audio_delete_status, pattern='^' + str(Audio) + '$'),
                CallbackQueryHandler(audio_delete_actived, pattern='^' + str(Activated) + '$' ),
                CallbackQueryHandler(setings, pattern='^' + str(Back) + '$'), 
                CommandHandler('setings', setings),            
            ],
            AUDIO_DELETE_ACTIVED:[
                MessageHandler(Filters.voice, audio_delete),
                CallbackQueryHandler(audio_delete_status, pattern='^' + str(Audio) + '$'),
                CallbackQueryHandler(audio_delete_inactive, pattern='^' + str(Inactive) + '$'),
                CallbackQueryHandler(setings, pattern='^' + str(Back) + '$'),
                CommandHandler('setings', setings),
                CallbackQueryHandler(message_delete_status, pattern='^' + str(Messages) + '$'),
                CallbackQueryHandler(close_setings, pattern='^' + str(Close) + '$'),
            ],
            AUDIO_DEL_ACTIVED_MSG_DEL_INACTIVE:[
                MessageHandler(Filters.voice, audio_delete),
                CallbackQueryHandler(message_delete_actived, pattern='^' + str(Closed) + '$'),
                CallbackQueryHandler(message_delete_time, pattern='^' + str(Set_time) + '$'),
                CallbackQueryHandler(setings, pattern='^' + str(Back) + '$'),
                CommandHandler('setings', setings),
            ],
            AUDIO_DEL_ACTIVED_MSG_DEL_ACTIVED:[ 
                MessageHandler(~Filters.command, message_delete),
                CallbackQueryHandler(message_delete_status, pattern='^' + str(Messages) + '$'),
                CallbackQueryHandler(message_delete_inactive, pattern='^' + str(Open) + '$'),
                CallbackQueryHandler(message_delete_time, pattern='^' + str(Set_time) + '$'),
                CallbackQueryHandler(setings, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(close_setings, pattern='^' + str(Close) + '$'),
                CommandHandler('setings', setings),
            ],
            AUDIO_DEL_ACTIVED_MSG_DEL_TIME_CHOISE:[
                MessageHandler(Filters.voice, audio_delete),
                CallbackQueryHandler(message_delete_status, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(message_delete_time_active, pattern='^' + str(Activated) + '$'),
                CommandHandler('setings', setings),
            ],
            MESSAGE_DELETE_TIME_ACTIVED:[
                CommandHandler('setings', setings),
                MessageHandler(~Filters.command, delete_messages_job),
            ],        
        },

        fallbacks= [
           CommandHandler('end', end_conv_handler),   
        ],
        per_user=False
    )
  
    updater.dispatcher.add_handler(conv_handler)


    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
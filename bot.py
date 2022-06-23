import pip._vendor.requests, logging, datetime, pytz 
from typing import Tuple, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember, ParseMode, ChatMemberUpdated
from telegram.ext import (Updater, CommandHandler, CallbackContext, MessageHandler, 
Filters, ChatMemberHandler, ConversationHandler,CallbackQueryHandler)

TOKEN = '2058897666:AAG67ewdPuakUffXbAMeLBwf8hlR7KlBDXk'
updater = Updater(TOKEN)

# Stages of Conv_handler
(SELECTING_ACTION, OPEN, CLOSED, SET_DAYS_AND_OPEN_TIME, SET_CLOSE_TIME, 
AUDIO_DELETE_ACTIVED, AUDIO_DELETE_INACTIVE, AUDIO_DELETE_ACTIVED_CLOSED, AUDIO_DELETE_ACTIVED_OPEN, AUDIO_DELETE_ACTIVED_SET_DAYS_AND_OPEN_TIME, 
AUDIO_DELETE_ACTIVED_SET_CLOSE_TIME) = range(11)

#Constants:
(AUDIO_DELETE_STATUS, AUDIO_DELETE_STATUS_ACTIVED, AUDIO_DELETE_NOTIFICATIONS_ON, 
OPENING_HOURS_STATUS_OPEN, JOB_STATUS_CHANGE,
OPENING_HOURS_STATUS, SETINGS_MESSAGE_ID,  MESSAGE_DELETE_NOTIFICATIONS_ON,
WEEK, START_TIME, END_TIME, FIRST_TIME, TIME, OPEN_TIME, CLOSE_TIME, WEEKDAYS, WEEKEND, FIRST_TIME_AUDIO, FIRST_TIME_OPENING, OPEN_TIME_TEMP)  = range(11,31)

# Callback querys
Closed, Messages, Open, Close, Set_time, Back, Activated, Inactive, Audio, Set_days, on, off  = range(31,43)

delete_message_list = []
var_list = []

time_zone = pytz.timezone('America/Sao_Paulo')
date_time_now = datetime.datetime.now(time_zone)
current_time = date_time_now.strftime("%d/%m/%Y %H:%M")
weekday_number = int(date_time_now.strftime("%w"))

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


def settings(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Opening hours", callback_data=str(Messages)),
            InlineKeyboardButton("Audio messages", callback_data=str(Audio)),
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(Close)) 
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    reply_text = "Setings:\n"

    if update.message:
        chat_id = update.message.chat.id
        message_id = update.message.message_id
        context.bot_data[SETINGS_MESSAGE_ID] = message_id

        if context.user_data.get(FIRST_TIME):
            pass
        else:
            context.user_data[FIRST_TIME_OPENING] = True
            context.user_data[FIRST_TIME_AUDIO] = True
            context.user_data[AUDIO_DELETE_STATUS_ACTIVED] = False
            context.user_data[OPENING_HOURS_STATUS_OPEN] = True
            context.user_data[FIRST_TIME] = True

        if context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True and context.user_data[OPENING_HOURS_STATUS_OPEN] == False:
            reply_text += "Opening hours: Permanently closed"
            context.bot.send_message(chat_id, reply_text, reply_markup=reply_markup)
            return AUDIO_DELETE_ACTIVED_CLOSED

        elif context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True and context.user_data[OPENING_HOURS_STATUS_OPEN] == True:
            if len(delete_message_list) != 0:
                reply_text += "Opening hours: Closed\nAudio messages: Forbidden"
            else:
                reply_text += "Opening hours: Open\nAudio messages: Forbidden"
            context.bot.send_message(chat_id,reply_text, reply_markup=reply_markup)
            return AUDIO_DELETE_ACTIVED
                
        elif context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == False and context.user_data[OPENING_HOURS_STATUS_OPEN] == False:
            reply_text += "Opening hours: Permanently closed"
            context.bot.send_message(chat_id,reply_text, reply_markup=reply_markup)
            return CLOSED   
             
        elif context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == False and context.user_data[OPENING_HOURS_STATUS_OPEN] == True:
            if len(delete_message_list) != 0:
                reply_text += "Opening hours: Closed\nAudio messages: Allowed"
            else:
                reply_text += "Opening hours: Open\nAudio messages: Allowed"
            context.bot.send_message(chat_id, reply_text, reply_markup=reply_markup)    
            return SELECTING_ACTION

    else:
        query = update.callback_query
        query.answer()
    
        if context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True and context.user_data[OPENING_HOURS_STATUS_OPEN] == False:
            reply_text += "Opening hours: Permanently closed"
            query.edit_message_text(reply_text, reply_markup=reply_markup)
            return AUDIO_DELETE_ACTIVED_CLOSED
        
        elif context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True and context.user_data[OPENING_HOURS_STATUS_OPEN] == True:
            if len(delete_message_list) != 0:
                reply_text += "Opening hours: Closed\nAudio messages: Forbidden"
            else:
                reply_text += "Opening hours: Open\nAudio messages: Forbidden"
            query.edit_message_text(reply_text, reply_markup=reply_markup)
            return AUDIO_DELETE_ACTIVED

        elif context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == False and context.user_data[OPENING_HOURS_STATUS_OPEN] == False:
            reply_text += "Opening hours: Permanently closed"
            query.edit_message_text(reply_text, reply_markup=reply_markup)
            return CLOSED

        elif context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == False and context.user_data[OPENING_HOURS_STATUS_OPEN] == True:
            if len(delete_message_list) != 0:
                reply_text += "Opening hours: Closed\nAudio messages: Allowed"
            else:
                reply_text += "Opening hours: Open\nAudio messages: Allowed"
            query.edit_message_text(reply_text, reply_markup=reply_markup)
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
    query.answer()
    chat_id = query.message.chat.id
    must_delete = query.message
    context.bot.deleteMessage(chat_id, must_delete.message_id)

    """Delete /setings"""
    message_id_setings = context.bot_data.get(SETINGS_MESSAGE_ID)
    context.bot.delete_message(chat_id, message_id_setings)
    context.bot_data.clear()
    return

""" DELETE AUDIO MESSAGES IN GROUP_CHAT """

def audio_delete_status(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    keyboard_audio_delete_inactive = [
        [
            InlineKeyboardButton("Active", callback_data=str(Activated)),
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]
    reply_markup_inactive = InlineKeyboardMarkup(keyboard_audio_delete_inactive)

    keyboard_audio_delete_actived_off = [
        [
            InlineKeyboardButton("Inactive", callback_data=str(Inactive))
        ],
        [
            InlineKeyboardButton("Notifications: Active", callback_data=str(on))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]
    reply_markup_actived_off = InlineKeyboardMarkup(keyboard_audio_delete_actived_off)

    keyboard_audio_delete_actived_on = [
        [
            InlineKeyboardButton("Inactive", callback_data=str(Inactive))
        ],
        [
            InlineKeyboardButton("Notifications: Inactive", callback_data=str(off))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]
    reply_markup_actived_on = InlineKeyboardMarkup(keyboard_audio_delete_actived_on)

    if context.user_data[FIRST_TIME_AUDIO] == True:
        context.user_data[AUDIO_DELETE_NOTIFICATIONS_ON] = False
        context.user_data[AUDIO_DELETE_STATUS] = 'Inactive'
        context.user_data[FIRST_TIME_AUDIO] = False
    else:
        pass

    reply_text = "Delete audio messages when sent\n"
    
    status = context.user_data.get(AUDIO_DELETE_STATUS)
    reply_text += (f'Status: {status}\n')
      
    if context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True:
        if context.user_data[AUDIO_DELETE_NOTIFICATIONS_ON] == False:
            reply_text +='Notifications: Off'
            query.edit_message_text(reply_text, reply_markup=reply_markup_actived_off)
        else:
            reply_text +='Notifications: On'
            query.edit_message_text(reply_text, reply_markup=reply_markup_actived_on)

        if context.user_data[OPENING_HOURS_STATUS_OPEN] == True:
            return AUDIO_DELETE_ACTIVED
        else:
            return AUDIO_DELETE_ACTIVED_CLOSED
    else:   
        query.edit_message_text(reply_text, reply_markup=reply_markup_inactive)
        return AUDIO_DELETE_INACTIVE

def audio_delete_actived(update: Update, context: CallbackContext):  
    query = update.callback_query
    query.answer()

    if query.data == str(on):
        context.user_data[AUDIO_DELETE_NOTIFICATIONS_ON] = True
    elif query.data == str(off):
        context.user_data[AUDIO_DELETE_NOTIFICATIONS_ON] = False

    keyboard_audio_delete_actived_off = [
        [
            InlineKeyboardButton("Inactive", callback_data=str(Inactive))
        ],
        [
            InlineKeyboardButton("Notifications: Active", callback_data=str(on))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    keyboard_audio_delete_actived_on = [
        [
            InlineKeyboardButton("Inactive", callback_data=str(Inactive))
        ],
        [
            InlineKeyboardButton("Notifications: Inactive", callback_data=str(off))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    
    reply_text = f"Delete audio messages when sent\n"
    
    status = 'On'
    reply_text += f"Status: {status}\n"

    if context.user_data[AUDIO_DELETE_NOTIFICATIONS_ON] == False:
        reply_text += 'Notifications: Off'
        reply_markup = InlineKeyboardMarkup(keyboard_audio_delete_actived_off)

    elif context.user_data[AUDIO_DELETE_NOTIFICATIONS_ON] == True:
        reply_text += 'Notifications: On'
        reply_markup = InlineKeyboardMarkup(keyboard_audio_delete_actived_on)            
            

    query.edit_message_text(reply_text, reply_markup=reply_markup)

    context.user_data[AUDIO_DELETE_STATUS] = status
    context.user_data[AUDIO_DELETE_STATUS_ACTIVED] = True    

    return AUDIO_DELETE_ACTIVED

def audio_delete_inactive(update:  Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    reply_text = f"Delete audio messages when sent\n"
    
    status = 'Off'
    reply_text += f"Status: {status}"

    keyboard_audio_delete_inactive = [
        [
            InlineKeyboardButton("Active", callback_data=str(Activated)),
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard_audio_delete_inactive)
    query.edit_message_text(reply_text, reply_markup=reply_markup)
    context.user_data[AUDIO_DELETE_STATUS_ACTIVED] = False

    return AUDIO_DELETE_INACTIVE

def audio_delete_message(update: Update, context: CallbackContext) -> int:
    if len(delete_message_list) != 0 or context.user_data[OPENING_HOURS_STATUS_OPEN] == False: 
        chat_id = update.message.chat.id
        must_delete = update.message
        context.bot.deleteMessage(chat_id, must_delete.message_id)
        return           
    else:
        chat_id = update.message.chat.id
        must_delete = update.message
        context.bot.deleteMessage(chat_id, must_delete.message_id)

        if context.user_data[AUDIO_DELETE_NOTIFICATIONS_ON] == True:
            text = "Audio messages arent allowed"
            context.bot.send_message(chat_id, text)      
        return 

"""DELETE MESSAGES IN GROUP CHAT"""

def opening_hours_status(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    keyboard_closed_off = [
        [
            InlineKeyboardButton("Open", callback_data=str(Open)),
        ],
        [
            InlineKeyboardButton("Notification: Active", callback_data=str(on))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]
    keyboard_closed_off = InlineKeyboardMarkup(keyboard_closed_off)

    keyboard_closed_on = [
        [
            InlineKeyboardButton("Open", callback_data=str(Open)),
        ],
        [
            InlineKeyboardButton("Notification: Inactive", callback_data=str(off))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]
    keyboard_closed_on = InlineKeyboardMarkup(keyboard_closed_on)

    keyboard_msg_del_inactived_off = [
        [
            InlineKeyboardButton("Close permanently", callback_data=str(Closed))
        ],
        [
            InlineKeyboardButton("Set time", callback_data=str(Set_time))
        ],
                [
            InlineKeyboardButton("Set weekdays", callback_data=str(Set_days))
        ],
        [
            InlineKeyboardButton("Notifications: Active", callback_data=str(on))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]
    keyboard_msg_del_inactived_off = InlineKeyboardMarkup(keyboard_msg_del_inactived_off)

    keyboard_msg_del_inactived_on = [
        [
            InlineKeyboardButton("Close permanently", callback_data=str(Closed))
        ],
        [
            InlineKeyboardButton("Set time", callback_data=str(Set_time))
        ],
        [
            InlineKeyboardButton("Set weekdays", callback_data=str(Set_days))
        ],        
        [
            InlineKeyboardButton("Notification: Inactive", callback_data=str(off))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]
    keyboard_msg_del_inactived_on = InlineKeyboardMarkup(keyboard_msg_del_inactived_on)

    if context.user_data[FIRST_TIME_OPENING] == True:

        context.user_data[OPENING_HOURS_STATUS] = 'Open'
        context.user_data[TIME] = '24h'
        context.user_data[WEEK] = 'Everyday'
        
        context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] = False
        context.user_data[JOB_STATUS_CHANGE] = True
        context.user_data[CLOSE_TIME] = False
        context.user_data[FIRST_TIME_OPENING] = False

    #Set the keyboard and settings menu    
    reply_text = "Opening hours\n"
    
    if len(delete_message_list) != 0:
        if context.user_data[OPENING_HOURS_STATUS_OPEN] == False:
            status = 'Permanently Closed'
        else:
            status = 'Closed'
    else:
        status = context.user_data.get(OPENING_HOURS_STATUS)
    
    reply_text += (f'Status: {status}\n')

    if context.user_data[OPENING_HOURS_STATUS_OPEN] == True:
        if context.user_data[CLOSE_TIME] == False:
            time = context.user_data.get(TIME)
            reply_text += (f'Time: {time}\n')
        else:
            open_time = context.user_data.get(OPEN_TIME)
            close_time = context.user_data.get(CLOSE_TIME)
            reply_text += f"Open hour: {open_time}h\nClose hour: {close_time}h\n"

            weekday_status = context.user_data[WEEK]        
            reply_text += (f'Working days: {weekday_status}\n')

        if context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] == True:
            reply_text +='Notification: On\n'
        else:
            reply_text +='Notification: Off\n'

        reply_text +=f"Current time: {current_time}"           

    else:
        if context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] == True:
            reply_text +='Notification: On\n'
        else:
            reply_text +='Notification: Off\n'

    if context.user_data[OPENING_HOURS_STATUS_OPEN] == False:
        if context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] == True:
            query.edit_message_text(reply_text, reply_markup=keyboard_closed_on)
        else:
            query.edit_message_text(reply_text, reply_markup=keyboard_closed_off)

        if context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True: 
            return AUDIO_DELETE_ACTIVED_CLOSED
        else:
            return CLOSED

    elif context.user_data[OPENING_HOURS_STATUS_OPEN] == True:
        if context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] == True:
            query.edit_message_text(reply_text, reply_markup=keyboard_msg_del_inactived_on)
        else:
            query.edit_message_text(reply_text, reply_markup=keyboard_msg_del_inactived_off)

        if context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True: 
            return AUDIO_DELETE_ACTIVED_OPEN
        else:
            return OPEN

def opening_hours_open(update: Update, context: CallbackContext):

    keyboard_msg_del_inactived_off = [
        [
            InlineKeyboardButton("Close permanently", callback_data=str(Closed))
        ],
        [
            InlineKeyboardButton("Set time", callback_data=str(Set_time))
        ],
        [
            InlineKeyboardButton("Set week days", callback_data=str(Set_days))
        ],
        [
            InlineKeyboardButton("Notification: Active", callback_data=str(on))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    keyboard_msg_del_inactived_on = [
        [
            InlineKeyboardButton("Close permanently", callback_data=str(Closed))
        ],
        [
            InlineKeyboardButton("Set time", callback_data=str(Set_time))
        ],
        [
            InlineKeyboardButton("Set week days", callback_data=str(Set_days))
        ],        
        [
            InlineKeyboardButton("Notification: Inactive", callback_data=str(off))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    query = update.callback_query
    chat_id = query.message.chat.id 

    if query.data == "0" or query.data == "1" or query.data == "2" or query.data == "3" or query.data == "4" or query.data == "5" or query.data == "6" or query.data == "7" or query.data == "8" or query.data == "9" or query.data == "10" or query.data == "11" or query.data == "12" or query.data == "13" or query.data == "14" or query.data == "15" or query.data == "16" or query.data == "17" or query.data == "18" or query.data == "19" or query.data == "20" or query.data == "21" or query.data == "22" or query.data == "23":
        open_time = context.user_data.get(OPEN_TIME_TEMP)
        if query.data == open_time:
            query.answer(text='Closed time must be different than open time', show_alert=True) 
            return
        else:
            context.user_data[TIME] = query.data
            context.user_data[OPEN_TIME] = open_time
            context.user_data[CLOSE_TIME] = query.data
            context.user_data[JOB_STATUS_CHANGE] = True 
    
    else:
        query.answer()
        if query.data == str(on):
            context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] = True
            context.user_data[JOB_STATUS_CHANGE] = True

        elif query.data == str(off):
            context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] = False
            context.user_data[JOB_STATUS_CHANGE] = True

        elif query.data == 'Everyday' or query.data == 'Weekdays' or query.data == 'Weekends':
            context.user_data[WEEK] = query.data
            context.user_data[JOB_STATUS_CHANGE] = True

        elif query.data == '24h':
            context.user_data[TIME] = query.data
            context.user_data[CLOSE_TIME] = False
            context.user_data[JOB_STATUS_CHANGE] = True
    
    if context.user_data.get(TIME) == '24h':
        open_time = int('0')    
        date_time_open = datetime.time(hour=open_time, tzinfo=time_zone)
        weekdays = context.user_data.get(WEEK)
    else: 
        open_time = int(context.user_data.get(OPEN_TIME))
        close_time = int(context.user_data.get(CLOSE_TIME))
        weekdays = context.user_data.get(WEEK)
        date_time_open = datetime.time(hour=open_time, tzinfo=time_zone)
        date_time_closed = datetime.time(hour=close_time, tzinfo=time_zone)

    if context.user_data[JOB_STATUS_CHANGE] == True:
        context.user_data[JOB_STATUS_CHANGE] = False
        var_list.clear()
        if context.user_data.get(TIME) == '24h':
            var_list.append(open_time)
            var_list.append(weekdays)
        else:
            var_list.append(open_time)
            var_list.append(close_time)
            var_list.append(weekdays)
        
        if context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] == True:

            remove_job_if_exists(str(OPEN_TIME), context)
            remove_job_if_exists(str(CLOSE_TIME), context)
            remove_job_if_exists(str(WEEKDAYS), context)
            remove_job_if_exists(str(WEEKEND), context)

            if context.user_data.get(TIME) == '24h':
                if context.user_data.get(WEEK) == 'Everyday':
                    text = 'Messages are allowed'
                    context.bot.send_message(chat_id, text)
                if context.user_data.get(WEEK) == 'Weekdays':
                    if weekday_number == 0 or weekday_number == 6:
                        delete_message_list.append('on')         
                        context.job_queue.run_daily(job_24h_week_notification, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(WEEKDAYS))
                        text = 'From this moment, until next monday 0h, messages sent will be deleted'
                        context.bot.send_message(chat_id, text)
                    else:
                        context.job_queue.run_daily(job_24h_week_notification, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(WEEKDAYS))
                        text = 'Messages are allowed'
                        context.bot.send_message(chat_id, text)

                elif context.user_data.get(WEEK) == 'Weekends':
                    if weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                        delete_message_list.append('on')     
                        context.job_queue.run_daily(job_24h_weekend_notification, date_time_open, days=(5,6), context=chat_id, name=str(WEEKEND))
                        text = 'From this moment, until next saturday 0h, messages sent will be deleted'
                        context.bot.send_message(chat_id, text)
                    else:
                        context.job_queue.run_daily(job_24h_weekend_notification, date_time_open, days=(5,6), context=chat_id, name=str(WEEKEND))
                        text = 'Messages are allowed'
                        context.bot.send_message(chat_id, text)
                        
            else:
                if open_time < close_time:
                    if context.user_data.get(WEEK) == 'Everyday':
                        if date_time_now.hour < date_time_open.hour:
                            delete_message_list.append('on')                
                            context.job_queue.run_daily(job_open_notification, date_time_open, context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat_id, name=str(CLOSE_TIME))
                            text = f'From this moment, until {open_time}h, messages sent will be deleted'
                            context.bot.send_message(chat_id, text)
                                    
                        elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:                                   
                            context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat_id, name=str(CLOSE_TIME))
                            context.job_queue.run_daily(job_open_notification, date_time_open, context=chat_id, name=str(OPEN_TIME))
                            text = 'Messages are allowed'
                            context.bot.send_message(chat_id, text)
                            
                        elif date_time_now.hour >= date_time_closed.hour:
                            delete_message_list.append('on')                  
                            context.job_queue.run_daily(job_open_notification, date_time_open, context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat_id, name=str(CLOSE_TIME))
                            text = f'From this moment, until {open_time}h, messages sent will be deleted'
                            context.bot.send_message(chat_id, text)
                                            
                    elif context.user_data.get(WEEK) == 'Weekdays':
                        if weekday_number == 0 or weekday_number == 6:
                            delete_message_list.append('on')                                  
                            context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(0,1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                            text = f'From this moment, until next monday {open_time}h, messages sent will be deleted'
                            context.bot.send_message(chat_id, text)
                        else:
                            if date_time_now.hour < date_time_open.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(0,1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                                text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat_id, text)
                                        
                            elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:                                    
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(0,1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(OPEN_TIME))
                                text = 'Messages are allowed'
                                context.bot.send_message(chat_id, text)

                            elif date_time_now.hour >= date_time_closed.hour:
                                delete_message_list.append('on')
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(0,1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                                text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat_id, text)                    

                    elif context.user_data.get(WEEK) == 'Weekends':
                        if  weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                            delete_message_list.append('on')                                   
                            context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(5,6), context=chat_id, name=str(CLOSE_TIME))
                            text = f'From this moment, until next saturday {open_time}h, messages sent will be deleted'
                            context.bot.send_message(chat_id, text)
                        else:
                            if date_time_now.hour < date_time_open.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(5,6), context=chat_id, name=str(CLOSE_TIME))
                                text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat_id, text)
                                        
                            elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:                                    
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(5,6), context=chat_id, name=str(CLOSE_TIME))
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                                text = 'Messages are allowed'
                                context.bot.send_message(chat_id, text)

                            elif date_time_now.hour >= date_time_closed.hour:
                                delete_message_list.append('on')
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(5,6), context=chat_id, name=str(CLOSE_TIME)) 
                                text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat_id, text)

                elif open_time > close_time:
                    if context.user_data.get(WEEK) == 'Everyday':
                        if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                            delete_message_list.append('on')                
                            context.job_queue.run_daily(job_open_notification, date_time_open, context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat_id, name=str(CLOSE_TIME))
                            text = f'From this moment, until {open_time}h, messages sent will be deleted'
                            context.bot.send_message(chat_id, text)
                                    
                        elif date_time_now.hour >= date_time_open.hour:                                    
                            context.job_queue.run_daily(job_open_notification, date_time_open, context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat_id, name=str(CLOSE_TIME))
                            text = 'Messages are allowed'
                            context.bot.send_message(chat_id, text)

                        elif date_time_now.hour < date_time_closed.hour:
                            context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat_id, name=str(CLOSE_TIME))
                            context.job_queue.run_daily(job_open_notification, date_time_open, context=chat_id, name=str(OPEN_TIME))
                            text = 'Messages are allowed'
                            context.bot.send_message(chat_id, text)

                    elif context.user_data.get(WEEK) == 'Weekdays':
                        if weekday_number == 0 or weekday_number == 6:
                            delete_message_list.append('on')                                  
                            context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3), context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                            text = f'From this moment, until next monday {open_time}h, messages sent will be deleted'
                            context.bot.send_message(chat_id, text)
                        else:
                            if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                                text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat_id, text)
                                    
                            elif date_time_now.hour >= date_time_open.hour:                                    
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                                text = 'Messages are allowed'
                                context.bot.send_message(chat_id, text)

                            elif date_time_now.hour < date_time_closed.hour:
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3), context=chat_id, name=str(OPEN_TIME))
                                text = 'Messages are allowed'
                                context.bot.send_message(chat_id, text)                    

                    elif context.user_data.get(WEEK) == 'Weekends':
                        if  weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                            delete_message_list.append('on')                                   
                            context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(6,0), context=chat_id, name=str(CLOSE_TIME))
                            text = f'From this moment, until next saturday {open_time}h, messages sent will be deleted'
                            context.bot.send_message(chat_id, text)
                        else:
                            if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(6,0), context=chat_id, name=str(CLOSE_TIME))
                                text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat_id, text)
                                    
                            elif date_time_now.hour >= date_time_open.hour:                                    
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(6,0), context=chat_id, name=str(CLOSE_TIME))
                                text = 'Messages are allowed'
                                context.bot.send_message(chat_id, text)

                            elif date_time_now.hour < date_time_closed.hour:
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(6,0), context=chat_id, name=str(CLOSE_TIME))
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                                text = 'Messages are allowed'
                                context.bot.send_message(chat_id, text)                   

        elif context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] == False:
            remove_job_if_exists(str(OPEN_TIME), context)
            remove_job_if_exists(str(CLOSE_TIME), context)
            remove_job_if_exists(str(WEEKDAYS), context)
            remove_job_if_exists(str(WEEKEND), context)

            if context.user_data.get(TIME) == '24h':
                if context.user_data.get(WEEK) == 'Weekdays':
                    if weekday_number == 0 or weekday_number == 6:
                        delete_message_list.append('on')         
                        context.job_queue.run_daily(job_24h_week, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(WEEKDAYS))
                    else:
                        context.job_queue.run_daily(job_24h_week, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(WEEKDAYS))

                elif context.user_data.get(WEEK) == 'Weekends':
                    if weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                        delete_message_list.append('on')     
                        context.job_queue.run_daily(job_24h_weekend, date_time_open, days=(5,6), context=chat_id, name=str(WEEKEND))
                    else:
                        context.job_queue.run_daily(job_24h_weekend, date_time_open, days=(5,6), context=chat_id, name=str(WEEKEND))
                    
            else:
                if open_time < close_time:
                    if context.user_data.get(WEEK) == 'Everyday':
                        if date_time_now.hour < date_time_open.hour:
                            delete_message_list.append('on')                
                            context.job_queue.run_daily(job_open, date_time_open, context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed, date_time_closed, context=chat_id, name=str(CLOSE_TIME))

                        elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:
                            context.job_queue.run_daily(job_closed, date_time_closed, context=chat_id, name=str(CLOSE_TIME))                 
                            context.job_queue.run_daily(job_open, date_time_open, context=chat_id, name=str(OPEN_TIME))

                        elif date_time_now.hour >= date_time_closed.hour:
                            delete_message_list.append('on')                                    
                            context.job_queue.run_daily(job_open, date_time_open, context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed, date_time_closed, context=chat_id, name=str(CLOSE_TIME))
                                            
                    elif context.user_data.get(WEEK) == 'Weekdays':
                        if weekday_number == 0 or weekday_number == 6:
                            delete_message_list.append('on')                                  
                            context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed, date_time_closed, days=(0,1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                        else:
                            if date_time_now.hour < date_time_open.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(0,1,2,3,4), context=chat_id, name=str(CLOSE_TIME))

                            elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(0,1,2,3,4), context=chat_id, name=str(CLOSE_TIME))                 
                                context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(OPEN_TIME))

                            elif date_time_now.hour >= date_time_closed.hour:
                                delete_message_list.append('on')                                    
                                context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3,4), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(0,1,2,3,4), context=chat_id, name=str(CLOSE_TIME))                    

                    elif context.user_data.get(WEEK) == 'Weekends':
                        if  weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                            delete_message_list.append('on')                                   
                            context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed, date_time_closed, days=(5,6), context=chat_id, name=str(CLOSE_TIME))
                        else:
                            if date_time_now.hour < date_time_open.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(5,6), context=chat_id, name=str(CLOSE_TIME))

                            elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(5,6), context=chat_id, name=str(CLOSE_TIME))                 
                                context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))

                            elif date_time_now.hour >= date_time_closed.hour:
                                delete_message_list.append('on')                                    
                                context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(5,6), context=chat_id, name=str(CLOSE_TIME))

                elif open_time > close_time:
                    if context.user_data.get(WEEK) == 'Everyday':
                        if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                            delete_message_list.append('on')                
                            context.job_queue.run_daily(job_open, date_time_open, context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed, date_time_closed, context=chat_id, name=str(CLOSE_TIME))
                                    
                        elif date_time_now.hour >= date_time_open.hour:                                    
                            context.job_queue.run_daily(job_open, date_time_open, context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed, date_time_closed, context=chat_id, name=str(CLOSE_TIME))

                        elif date_time_now.hour < date_time_closed.hour:
                            context.job_queue.run_daily(job_closed, date_time_closed, context=chat_id, name=str(CLOSE_TIME))
                            context.job_queue.run_daily(job_open, date_time_open, context=chat_id, name=str(OPEN_TIME))

                    elif context.user_data.get(WEEK) == 'Weekdays':
                        if weekday_number == 0 or weekday_number == 6:
                            delete_message_list.append('on')                                  
                            context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3), context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed, date_time_closed, days=(1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                        else:
                            if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                                    
                            elif date_time_now.hour >= date_time_open.hour:                                    
                                context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(1,2,3,4), context=chat_id, name=str(CLOSE_TIME))

                            elif date_time_now.hour < date_time_closed.hour:
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(1,2,3,4), context=chat_id, name=str(CLOSE_TIME))
                                context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3), context=chat_id, name=str(OPEN_TIME))                    

                    elif context.user_data.get(WEEK) == 'Weekends':
                        if  weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                            delete_message_list.append('on')                                   
                            context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                            context.job_queue.run_daily(job_closed, date_time_closed, days=(6,0), context=chat_id, name=str(CLOSE_TIME))
                        else:
                            if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(6,0), context=chat_id, name=str(CLOSE_TIME))
                                    
                            elif date_time_now.hour >= date_time_open.hour:                                    
                                context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(6,0), context=chat_id, name=str(CLOSE_TIME))

                            elif date_time_now.hour < date_time_closed.hour:
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(6,0), context=chat_id, name=str(CLOSE_TIME))
                                context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat_id, name=str(OPEN_TIME))

    #Set the keyboard and settings menu
    reply_text = "Opening hours\n"

    if len(delete_message_list) != 0:
        status = 'Closed'
    else:
        status = 'Open'

    reply_text += (f'Status: {status}\n')

    if context.user_data[CLOSE_TIME] == False:
        time = context.user_data.get(TIME)
        reply_text += (f'Time: {time}\n')
    else:
        open_time = context.user_data.get(OPEN_TIME)
        close_time = context.user_data.get(CLOSE_TIME)
        reply_text += f"Open hour: {open_time}h\nClose hour: {close_time}h\n"
    
    weekday_status = context.user_data.get(WEEK)
    reply_text += f"Working days: {weekday_status}\n" 

    if context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] == False:
        reply_text +="Notifications: Off\n"
        reply_markup = InlineKeyboardMarkup(keyboard_msg_del_inactived_off)

    elif context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] == True:
        reply_text +="Notifications: On\n"
        reply_markup = InlineKeyboardMarkup(keyboard_msg_del_inactived_on)

    reply_text +=f"Current time: {current_time}"

    query.edit_message_text(reply_text, reply_markup=reply_markup)
    
    context.user_data[OPENING_HOURS_STATUS] = status
    context.user_data[OPENING_HOURS_STATUS_OPEN] = True

    if context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True:
        return AUDIO_DELETE_ACTIVED_OPEN   
    else:
        return OPEN

def job_open_notification(context: CallbackContext):
    delete_message_list.clear()
    job = context.job
    context.bot.send_message(job.context, text='Messages are allowed')    

def job_closed_notification(context: CallbackContext):
    job = context.job
    open_time = var_list[0]
    close_time = var_list[1]
    weekdays = var_list[2]
    weekday_number = int(date_time_now.strftime("%w"))

    if open_time < close_time:
        delete_message_list.append('on')
        if weekdays == 'Everyday':
            context.bot.send_message(job.context, text=f'From this moment, until {open_time}h, messages sent will be deleted')

        elif weekdays == 'Weekdays':
            if weekday_number == 5:
                context.bot.send_message(job.context, text=f'From this moment, until next monday {open_time}h, messages sent will be deleted')
            else:
                context.bot.send_message(job.context, text=f'From this moment, until {open_time}h, messages sent will be deleted')

        elif weekdays == 'Weekends':
            if weekday_number == 0:
                context.bot.send_message(job.context, text=f'From this moment, until next saturday {open_time}h, messages sent will be deleted')
            else:
                context.bot.send_message(job.context, text=f'From this moment, until {open_time}h, messages sent will be deleted')
    else:
        if weekdays == 'Everyday':
            delete_message_list.append('on')
            context.bot.send_message(job.context, text=f'From this moment, until {open_time}h, messages sent will be deleted')
        
        elif weekdays == 'Weekdays':
            delete_message_list.append('on')
            if weekday_number == 5:
                context.bot.send_message(job.context, text=f'From this moment, until next monday {open_time}h, messages sent will be deleted')
            else:
                context.bot.send_message(job.context, text=f'From this moment, until {open_time}h, messages sent will be deleted')

        elif weekdays == 'Weekends':
            if weekday_number == 0:
                delete_message_list.append('on')
                context.bot.send_message(job.context, text=f'From this moment, until next saturday {open_time}h, messages sent will be deleted')

def job_24h_week_notification(context: CallbackContext):
    weekday_number = int(date_time_now.strftime("%w"))
    job = context.job
    if weekday_number == 6 or weekday_number == 0:
        if len(delete_message_list) != 0: 
            delete_message_list.append('on')
            context.bot.send_message(job.context, text='From this moment until next monday 0h, messages sent will be deleted')
    else:
        delete_message_list.clear()
        context.bot.send_message(job.context, text='Messages are allowed')

def job_24h_weekend_notification(context: CallbackContext):
    weekday_number = int(date_time_now.strftime("%w"))
    job = context.job
    if weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
        if len(delete_message_list) != 0:
            delete_message_list.append('on')
            context.bot.send_message(job.context, text='From this moment until next saturday 0h, messages sent will be deleted')
    else:
        delete_message_list.clear()
        context.bot.send_message(job.context, text='Messages are allowed')

def job_open(context: CallbackContext): 
    delete_message_list.clear()
    job = context.job      

def job_closed(context: CallbackContext):
    job = context.job
    open_time = var_list[0]
    close_time = var_list[1]
    weekdays = var_list[2]
    weekday_number = int(date_time_now.strftime("%w"))

    if open_time < close_time:
        delete_message_list.append('on')

    elif open_time > close_time:
        if weekdays == 'Everyday' or weekdays == 'Weekdays':
            delete_message_list.append('on')

        elif weekdays == 'Weekends':
            if weekday_number == 0:
                delete_message_list.append('on')

def job_24h_week(context: CallbackContext):
    weekday_number = int(date_time_now.strftime("%w"))
    job = context.job
    if weekday_number == 6 or weekday_number == 0:
        delete_message_list.append('on')
    else:
        delete_message_list.clear()

def job_24h_weekend(context: CallbackContext):
    weekday_number = int(date_time_now.strftime("%w"))
    job = context.job
    if not weekday_number == 6 or not weekday_number == 0:
        delete_message_list.append('on')
    else:
        delete_message_list.clear()

def opening_hours_closed(update:  Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    keyboard_msg_del_active_off = [
        [
            InlineKeyboardButton("Open", callback_data=str(Open)),
        ],
        [
            InlineKeyboardButton("Notification: Active", callback_data=str(on))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    keyboard_msg_del_active_on = [
        [
            InlineKeyboardButton("Open", callback_data=str(Open)),
        ],
        [
            InlineKeyboardButton("Notification: Inactive", callback_data=str(off))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    reply_text = f"Opening hours\n"

    status = 'Closed'
    reply_text += f"Status: {status}\n"

    if query.data == str(on):
        context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] = True
        # context.user_data[JOB_STATUS_CHANGE] = True
        reply_markup = InlineKeyboardMarkup(keyboard_msg_del_active_on)
        reply_text += f"Notifications: On"


    elif query.data == str(off):
        context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] = False
        # context.user_data[JOB_STATUS_CHANGE] = True
        reply_markup = InlineKeyboardMarkup(keyboard_msg_del_active_off) 
        reply_text += f"Notifications: Off" 

    else:
        if context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] == True:
            reply_markup = InlineKeyboardMarkup(keyboard_msg_del_active_on)
            reply_text += f"Notifications: On"
        else:
            reply_markup = InlineKeyboardMarkup(keyboard_msg_del_active_off)
            reply_text += f"Notifications: Off"

    query.edit_message_text(reply_text, reply_markup=reply_markup)
     
    if context.user_data[MESSAGE_DELETE_NOTIFICATIONS_ON] == True:
        if context.user_data[OPENING_HOURS_STATUS_OPEN] == True or query.data == str(on):
            if len(delete_message_list) == 0:
                chat_id = query.message.chat.id
                reply_text = 'Messages sent will be deleted'
                context.bot.send_message(chat_id,reply_text)

    remove_job_if_exists(str(OPEN_TIME), context)
    remove_job_if_exists(str(CLOSE_TIME), context)
    remove_job_if_exists(str(WEEKDAYS), context)
    remove_job_if_exists(str(WEEKEND), context)

    context.user_data[OPENING_HOURS_STATUS_OPEN] = False
    context.user_data[JOB_STATUS_CHANGE] = True
    context.user_data[OPENING_HOURS_STATUS] = status

    if context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True:
        return AUDIO_DELETE_ACTIVED_CLOSED
    else:
        return CLOSED

def opening_hours_set_time(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    keyboard = [
        [
            InlineKeyboardButton("24h", callback_data=str('24h'))
        ],
        [
            InlineKeyboardButton("Set open/closed time", callback_data=str(Activated))
        ],
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    opening_hours_time_status = context.user_data.get(TIME)

    reply_text = f"Time set for opening hours\n"

    if context.user_data[CLOSE_TIME] == False:
        reply_text += f"Status: {opening_hours_time_status}"

    else:
        open_time = context.user_data.get(OPEN_TIME)
        close_time = context.user_data.get(CLOSE_TIME)
        reply_text += f"Open hour: {open_time}h\nClose hour: {close_time}h"

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(reply_text, reply_markup=reply_markup)


    if context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True:
        return AUDIO_DELETE_ACTIVED_SET_DAYS_AND_OPEN_TIME
    else:
        return SET_DAYS_AND_OPEN_TIME

def opening_hours_set_open_time(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    keyboard = [
        [
            InlineKeyboardButton(" 0h ", callback_data='0'), 
            InlineKeyboardButton(" 1h ", callback_data='1'), 
            InlineKeyboardButton(" 2h ", callback_data='2'), 
            InlineKeyboardButton(" 3h ", callback_data='3'), 
            InlineKeyboardButton(" 4h ", callback_data='4'), 
            InlineKeyboardButton(" 5h ", callback_data='5'),
        ],
        [
            InlineKeyboardButton(" 6h ", callback_data='6'), 
            InlineKeyboardButton(" 7h ", callback_data='7'), 
            InlineKeyboardButton(" 8h ", callback_data='8'), 
            InlineKeyboardButton(" 9h ", callback_data='9'), 
            InlineKeyboardButton(" 10h ", callback_data='10'), 
            InlineKeyboardButton(" 11h ", callback_data='11'),
        ],
        [
            InlineKeyboardButton(" 12h ", callback_data='12'), 
            InlineKeyboardButton(" 13h ", callback_data='13'), 
            InlineKeyboardButton(" 14h ", callback_data='14'), 
            InlineKeyboardButton(" 15h ", callback_data='15'), 
            InlineKeyboardButton(" 16h ", callback_data='16'), 
            InlineKeyboardButton(" 17h ", callback_data='17'),

        ],
        [
            InlineKeyboardButton(" 18h ", callback_data='18'), 
            InlineKeyboardButton(" 19h ", callback_data='19'), 
            InlineKeyboardButton(" 20h ", callback_data='20'), 
            InlineKeyboardButton(" 21h ", callback_data='21'), 
            InlineKeyboardButton(" 22h ", callback_data='22'), 
            InlineKeyboardButton(" 23h ", callback_data='23'),            
        ],
        [
            InlineKeyboardButton(" Back ", callback_data=str(Back))
        ],
    ] 

    reply_text = f"Set open time:\n"

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(reply_text, reply_markup=reply_markup)

    if context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True:
        return AUDIO_DELETE_ACTIVED_SET_CLOSE_TIME
    else:
        return SET_CLOSE_TIME

def opening_hours_set_closed_time(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    open_time = query.data

    keyboard = [
        [
            InlineKeyboardButton(" 0h ", callback_data='0'), 
            InlineKeyboardButton(" 1h ", callback_data='1'), 
            InlineKeyboardButton(" 2h ", callback_data='2'), 
            InlineKeyboardButton(" 3h ", callback_data='3'), 
            InlineKeyboardButton(" 4h ", callback_data='4'), 
            InlineKeyboardButton(" 5h ", callback_data='5'),
        ],
        [
            InlineKeyboardButton(" 6h ", callback_data='6'), 
            InlineKeyboardButton(" 7h ", callback_data='7'), 
            InlineKeyboardButton(" 8h ", callback_data='8'), 
            InlineKeyboardButton(" 9h ", callback_data='9'), 
            InlineKeyboardButton(" 10h ", callback_data='10'), 
            InlineKeyboardButton(" 11h ", callback_data='11'),
        ],
        [
            InlineKeyboardButton(" 12h ", callback_data='12'), 
            InlineKeyboardButton(" 13h ", callback_data='13'), 
            InlineKeyboardButton(" 14h ", callback_data='14'), 
            InlineKeyboardButton(" 15h ", callback_data='15'), 
            InlineKeyboardButton(" 16h ", callback_data='16'), 
            InlineKeyboardButton(" 17h ", callback_data='17'),

        ],
        [
            InlineKeyboardButton(" 18h ", callback_data='18'), 
            InlineKeyboardButton(" 19h ", callback_data='19'), 
            InlineKeyboardButton(" 20h ", callback_data='20'), 
            InlineKeyboardButton(" 21h ", callback_data='21'), 
            InlineKeyboardButton(" 22h ", callback_data='22'), 
            InlineKeyboardButton(" 23h ", callback_data='23'),            
        ],
        [
            InlineKeyboardButton(" Back ", callback_data=str(Back))
        ],
    ] 

    reply_text = f"Set closed time:\n"

    reply_text += f"Open time: {open_time}h\n"
    reply_text += f"Closed_time:"

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(reply_text, reply_markup=reply_markup)

    context.user_data[OPEN_TIME_TEMP] = open_time
    
    if context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True:
        return AUDIO_DELETE_ACTIVED_OPEN
    else:
        return OPEN

def opening_hours_set_week_days(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    keyboard = [
        [
            InlineKeyboardButton("Everyday", callback_data='Everyday')
        ],
        [
            InlineKeyboardButton("Weekdays", callback_data='Weekdays')
        ],
        [
            InlineKeyboardButton("Weekends", callback_data='Weekends')
        ],                
        [
            InlineKeyboardButton("Back", callback_data=str(Back))
        ],
    ]

    opening_hours_days_status = context.user_data.get(WEEK)

    reply_text = f"Set days for opening hours\nStatus: {opening_hours_days_status}"

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(reply_text, reply_markup=reply_markup)
    context.user_data[WEEK] = opening_hours_days_status

    if context.user_data[AUDIO_DELETE_STATUS_ACTIVED] == True:
        return AUDIO_DELETE_ACTIVED_SET_DAYS_AND_OPEN_TIME
    else:
        return SET_DAYS_AND_OPEN_TIME    
    
def remove_job_if_exists(name: str,context: CallbackContext):
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        delete_message_list.clear()
        job.schedule_removal()
    return True

def opening_hours_open_message_delete(update: Update, context: CallbackContext) -> int:
    if len(delete_message_list) != 0 or context.user_data[OPENING_HOURS_STATUS_OPEN] == False: 
        chat_id = update.message.chat.id
        must_delete = update.message
        context.bot.deleteMessage(chat_id, must_delete.message_id)
        return           
    else:
        return

def opening_hours_closed_message_delete(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat.id
    must_delete = update.message
    context.bot.deleteMessage(chat_id, must_delete.message_id)
    return
                

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
            CommandHandler('setings', settings),    
            ],
        states={
            SELECTING_ACTION:[
            CallbackQueryHandler(audio_delete_status, pattern='^' + str(Audio) + '$'),
            CallbackQueryHandler(opening_hours_status, pattern='^' + str(Messages) + '$'),
            CallbackQueryHandler(close_setings, pattern='^' + str(Close) + '$'),
            CommandHandler('setings', settings),
            ],
            OPEN:[
                MessageHandler(~Filters.command, opening_hours_open_message_delete),
                CallbackQueryHandler(settings, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(opening_hours_closed, pattern='^' + str(Closed) + '$'),
                CallbackQueryHandler(opening_hours_set_time, pattern='^' + str(Set_time) + '$'),
                CallbackQueryHandler(opening_hours_set_week_days, pattern='^' + str(Set_days) + '$'), 
                CallbackQueryHandler(opening_hours_status, pattern='^' + str(Messages) + '$'),
                CallbackQueryHandler(audio_delete_status, pattern='^' + str(Audio) + '$'),
                CallbackQueryHandler(opening_hours_open, pattern='^' + str(on) + '$|' + str(off) + '$|' + '0' + '$|' + '1' + '$|' + '2' + '$|' + '3' + '$|' + '4' + '$|' + '5' + '$|' + '6' + '$|' + '7' + '$|' + '8' + '$|' + '9' + '$|' + '10' + '$|' + '11' + '$|' + '12' + '$|' + '13' + '$|' + '14' + '$|' + '15' + '$|' + '16' + '$|' + '17' + '$|' + '18' + '$|' + '19' + '$|' + '20' + '$|' + '21' + '$|' + '22' + '$|' + '23' + '$'),
                CommandHandler('setings', settings),
            ],        
            CLOSED:[
                MessageHandler(~Filters.command, opening_hours_closed_message_delete),
                CallbackQueryHandler(opening_hours_open, pattern='^' + str(Open) + '$'),
                CallbackQueryHandler(opening_hours_closed, pattern='^' + str(on) + '$|' + str(off) + '$'), 
                CallbackQueryHandler(opening_hours_status, pattern='^' + str(Messages) + '$'),
                CallbackQueryHandler(close_setings, pattern='^' + str(Close) + '$'),
                CallbackQueryHandler(audio_delete_status, pattern='^' + str(Audio) + '$'),
                CallbackQueryHandler(settings, pattern='^' + str(Back) + '$'),
                CommandHandler('setings', settings),                        
            ],  
            SET_DAYS_AND_OPEN_TIME:[
                MessageHandler(~Filters.command, opening_hours_open_message_delete),
                CallbackQueryHandler(opening_hours_open, pattern='^' + str(Back) + '$|' + '24h' + '$|' + 'Everyday' + '$|' + 'Weekdays' + '$|' + 'Weekends' + '$'),
                CallbackQueryHandler(opening_hours_set_open_time, pattern='^' + str(Activated) + '$'),
                CommandHandler('setings', settings),
            ],
            SET_CLOSE_TIME:[
                MessageHandler(~Filters.command, opening_hours_open_message_delete),
                CallbackQueryHandler(opening_hours_open, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(opening_hours_set_closed_time, pattern='^' + '0' + '$|' + '1' + '$|' + '2' + '$|' + '3' + '$|' + '4' + '$|' + '5' + '$|' + '6' + '$|' + '7' + '$|' + '8' + '$|' + '9' + '$|' + '10' + '$|' + '11' + '$|' + '12' + '$|' + '13' + '$|' + '14' + '$|' + '15' + '$|' + '16' + '$|' + '17' + '$|' + '18' + '$|' + '19' + '$|' + '20' + '$|' + '21' + '$|' + '22' + '$|' + '23' + '$'),
                CommandHandler('setings', settings),
            ],
            AUDIO_DELETE_INACTIVE:[
                CallbackQueryHandler(audio_delete_status, pattern='^' + str(Audio) + '$'),
                CallbackQueryHandler(audio_delete_actived, pattern='^' + str(Activated) + '$' ),
                CallbackQueryHandler(settings, pattern='^' + str(Back) + '$'), 
                CommandHandler('setings', settings),            
            ],
            AUDIO_DELETE_ACTIVED:[
                MessageHandler(Filters.voice, audio_delete_message),
                MessageHandler(~Filters.command, opening_hours_open_message_delete),

                CallbackQueryHandler(audio_delete_status, pattern='^' + str(Audio) + '$'),
                CallbackQueryHandler(audio_delete_inactive, pattern='^' + str(Inactive) + '$'),
                CallbackQueryHandler(audio_delete_actived, pattern='^' + str(on) + '$|' + str(off) + '$'),

                CallbackQueryHandler(opening_hours_status, pattern='^' + str(Messages) + '$'),

                CallbackQueryHandler(settings, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(close_setings, pattern='^' + str(Close) + '$'),
                
                CommandHandler('setings', settings),
            ],
            AUDIO_DELETE_ACTIVED_OPEN:[
                MessageHandler(Filters.voice, audio_delete_message),
                MessageHandler(~Filters.command, opening_hours_open_message_delete),

                CallbackQueryHandler(opening_hours_closed, pattern='^' + str(Closed) + '$'),
                CallbackQueryHandler(opening_hours_set_time, pattern='^' + str(Set_time) + '$'),
                CallbackQueryHandler(opening_hours_set_week_days, pattern='^' + str(Set_days) + '$'),
                CallbackQueryHandler(opening_hours_open, pattern='^' + str(on) + '$|' + str(off) + '$|' + '0' + '$|' + '1' + '$|' + '2' + '$|' + '3' + '$|' + '4' + '$|' + '5' + '$|' + '6' + '$|' + '7' + '$|' + '8' + '$|' + '9' + '$|' + '10' + '$|' + '11' + '$|' + '12' + '$|' + '13' + '$|' + '14' + '$|' + '15' + '$|' + '16' + '$|' + '17' + '$|' + '18' + '$|' + '19' + '$|' + '20' + '$|' + '21' + '$|' + '22' + '$|' + '23' + '$'),

                CallbackQueryHandler(settings, pattern='^' + str(Back) + '$'),
                CommandHandler('setings', settings),
            ],
            AUDIO_DELETE_ACTIVED_SET_DAYS_AND_OPEN_TIME:[
                MessageHandler(Filters.voice, audio_delete_message),
                MessageHandler(~Filters.command, opening_hours_open_message_delete),

                CallbackQueryHandler(opening_hours_open, pattern='^' + str(Back) + '$|' + '24h' + '$|' + 'Everyday' + '$|' + 'Weekdays' + '$|' + 'Weekends' + '$'),
                CallbackQueryHandler(opening_hours_set_open_time, pattern='^' + str(Activated) + '$'),

                CommandHandler('setings', settings),
            ],
            AUDIO_DELETE_ACTIVED_SET_CLOSE_TIME:[
                MessageHandler(Filters.voice, audio_delete_message),
                MessageHandler(~Filters.command, opening_hours_open_message_delete),

                CallbackQueryHandler(opening_hours_open, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(opening_hours_set_closed_time, pattern='^' + '0' + '$|' + '1' + '$|' + '2' + '$|' + '3' + '$|' + '4' + '$|' + '5' + '$|' + '6' + '$|' + '7' + '$|' + '8' + '$|' + '9' + '$|' + '10' + '$|' + '11' + '$|' + '12' + '$|' + '13' + '$|' + '14' + '$|' + '15' + '$|' + '16' + '$|' + '17' + '$|' + '18' + '$|' + '19' + '$|' + '20' + '$|' + '21' + '$|' + '22' + '$|' + '23' + '$'),
                
                CommandHandler('setings', settings),
            ],
            AUDIO_DELETE_ACTIVED_CLOSED:[ 
                MessageHandler(~Filters.command, opening_hours_closed_message_delete),
                CallbackQueryHandler(opening_hours_status, pattern='^' + str(Messages) + '$'),
                CallbackQueryHandler(audio_delete_status, pattern='^' + str(Audio) + '$'),
                CallbackQueryHandler(close_setings, pattern='^' + str(Close) + '$'),

                CallbackQueryHandler(opening_hours_open, pattern='^' + str(Open) + '$'),
                CallbackQueryHandler(opening_hours_closed, pattern='^' + str(on) + '$|' + str(off) + '$'),
                CallbackQueryHandler(settings, pattern='^' + str(Back) + '$'),
                
                CommandHandler('setings', settings),                
            ],        
        },

        fallbacks= [
           CommandHandler('end', end_conv_handler),   
        ],
        per_user=False,
    )
  
    updater.dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
from telegram.utils import helpers
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler, MessageHandler, Filters, 
PicklePersistence, Updater,CommandHandler,CallbackContext,ChatMemberHandler,Filters,CallbackQueryHandler)
from telegram import (Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, 
Update, Chat, ChatMember, ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup)
import datetime, pytz, logging, tzlocal
from typing import Tuple, Optional, cast, List
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

TOKEN = '2058897666:AAG67ewdPuakUffXbAMeLBwf8hlR7KlBDXk'
persistence = PicklePersistence(filename='supergroups_bot')
updater = Updater(TOKEN, persistence=persistence)

# Stages of Conv_handler:
(SETTINGS_MENU, OPENING_HOURS_MENU, SET_DAYS_AND_OPEN_CLOSE_TIME, VOICE_MENU,  
SET_TIME_ZONE, TIME_ZONE_MENU, CHANGE_TIME_ZONE_IN_PRIVATE) = range(7)

# Constants:
(OPENING_HOURS_WEEKDAYS_JOB, OPENING_HOURS_WEEKEND_JOB, OPENING_HOURS_OPEN_TIME_JOB, OPENING_HOURS_CLOSE_TIME_JOB) = range(7,11)

#Constants of chat_data:
(SETTINGS_MESSAGE_ID, FIRST_TIME_OPENING_HOURS_MENU, FIRST_TIME_VOICE_MENU, VOICE_DELETE_STATUS_ACTIVED, FIRST_TIME_SETTINGS_MENU, 
VOICE_DELETE_NOTIFICATIONS_ON, VOICE_STATUS, OPENING_HOURS_STATUS_OPEN, OPENING_HOURS_STATUS, OPENING_HOURS_TIME, OPENING_HOURS_WEEK,
JOB_STATUS_CHANGE, OPENING_HOURS_NOTIFICATIONS_ON, OPENING_HOURS_OPEN_TIME, OPENING_HOURS_CLOSE_TIME, OPENING_HOURS_OPEN_TIME_TEMP, 
OPENING_HOURS_WEEKDAY_NUMBER, TIME_ZONE, CHAT_DATE_TIME_NOW) = range(11,30)

# Contants of user_data:
USER_ID, CHAT_INVITE_LINK, GROUP_CHAT_ID, CHAT_TITLE = range(30,34)

# Constants of bot_data:

# Meta constants:
CHAT_CURRENT_TIME = range(34,35)

# Callback querys:
(Closed, Opening_hours_menu, Open, Close, Set_time, Back, Activate, Inactivate, Voice_message_menu, Set_days, 
Time_zone_menu, Change_time_zone, Go_private, Turn_notification_on, Turn_notification_off)  = range(35,50)

delete_message_list = []
var_list = [] 
chat_title_list = []
chat_invite_list = []

ADD_AS_ADMIN = "add_as_admin"
ADD_AS_MEMBER = "add_as_member"
SETTINGS = "settings"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def extract_status_change_admin(chat_member_update: ChatMemberUpdated,) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")

    #One way to get chat_id and cause_user_id
    chat_id = chat_member_update.chat.id
    user_id = chat_member_update.from_user.id

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [ChatMember.ADMINISTRATOR] 
    is_member = new_status in [ChatMember.ADMINISTRATOR]

    return was_member, is_member

def track_chats(update: Update, context: CallbackContext) -> None:
    """Tracks the chats the bot is in."""

    result_admin = extract_status_change_admin(update.my_chat_member)
    was_member_admin, is_member_admin = result_admin

    #Other way to get chat_id and cause_user_id
    chat = update.effective_chat
    user_id = update.effective_user.id
    bot_id = update.effective_user.bot.id
    bot_member = context.bot.get_chat_member(chat.id,bot_id)
    bot_status = bot_member.status
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    cause_member_status = chat_member.status

    # Handle chat types differently:
    if chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if cause_member_status == ChatMember.CREATOR:
            if not was_member_admin and is_member_admin:
                context.bot_data.setdefault(user_id, set()).add(chat.id)
                
            elif was_member_admin and not is_member_admin:
                context.bot_data.setdefault(user_id, set()).discard(chat.id)

            elif bot_status == ChatMember.MEMBER:
                bot = context.bot
                url = helpers.create_deep_linked_url(bot.username, ADD_AS_MEMBER)
                text = (
                    "Thanks to add me in to your group\n"
                    "Add me as admin to continue."
                )
                keyboard = InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Continue here!", url=url)
                )
                context.bot.send_message(chat_id=chat.id, text=text, reply_markup=keyboard, disable_notification=True)
                context.bot.leave_chat(chat.id)
       
        elif cause_member_status == ChatMember.ADMINISTRATOR:
            context.bot.leave_chat(chat.id)

    else:
        context.bot.leave_chat(chat.id)

def list_index(current_list:List[str], i:str):
    x = current_list.index(i)
    return x

def bot_added_as_admin(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    """Reached through the CHECK_THIS_OUT payload"""
    text = (
        "Thanks to add me as Admin\n"
        "Type or click /settings to set settings"
    )
    context.bot.send_message(chat_id=chat.id, text=text, disable_notification=True)
    return

def add_bot_as_admin(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    chat = update.effective_chat
    url = helpers.create_deep_linked_url(bot.username, ADD_AS_ADMIN, group=True)
    text = "Add me as admin in to your group to start:"
    keyboard = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(text="Add me as admin!", url=url)
    )
    context.bot.send_message(chat_id=chat.id, text=text, reply_markup=keyboard, disable_notification=True)
    return

def start(update: Update, context: CallbackContext) -> None:

    if update.message:
        chat = update.effective_chat 
        user_id = update.message.from_user.id

    else:
        query = update.callback_query
        query.answer()
        chat = query.message.chat
        user_id = query.from_user.id

    if chat.type == Chat.PRIVATE:
        """Send a deep-linked URL when the command /start is issued."""
        bot = context.bot
        url = helpers.create_deep_linked_url(bot.username, ADD_AS_ADMIN, group=True)
        text = "Welcome to supergroup. Add me to a group do start:"
        keyboard = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(text="Add me to a group!", url=url)
        )
        context.bot.send_message(chat_id=chat.id, text=text, reply_markup=keyboard)
    else:
        chat_member = context.bot.get_chat_member(chat.id,user_id)
        chat_member_status = chat_member.status

        if chat_member_status == ChatMember.CREATOR:
            text = (
            "Type or click /settings to set settings"
            )

            context.bot.send_message(chat_id=chat.id, text=text, disable_notification=True)
        else:
            context.bot.send_message(chat_id=chat.id, text='I only respond to ChatMember CREATOR', disable_notification=True)
    return
    
def settings(update: Update, context: CallbackContext):

    if update.message:
        message_id = update.message.message_id
        user_id = update.message.from_user.id
        chat = update.effective_chat 
        bot_id = update.message.bot.id
    else:
        query = update.callback_query
        query.answer()
        chat = query.message.chat
        message_id = query.message.message_id
        user_id = query.from_user.id
        bot_id = query.message.bot.id
        
    if chat.type == Chat.PRIVATE:
        if user_id not in context.bot_data:
            text='There is no group to /settings available. Make sure that you add me in your group as an admin member' 
            context.bot.send_message(chat_id = chat.id, text=text, disable_notification=True)
            return
        elif user_id in context.bot_data:       
            for gid in context.bot_data.setdefault(user_id,set()):
                chat = context.bot.get_chat(gid)
                chat_title = chat.title
                chat_title_list.append(chat_title)
                chat_link = chat.invite_link
                chat_invite_list.append(chat_link)

            reply_markup = InlineKeyboardMarkup.from_column(
                [InlineKeyboardButton(str(i), url=chat_invite_list[list_index(chat_title_list,i)]) for i in chat_title_list]
            )

            update.message.reply_text('Please choose:', reply_markup=reply_markup)
            chat_title_list.clear()
            chat_invite_list.clear()
            return

    else:
        chat_member = context.bot.get_chat_member(chat.id,user_id)
        chat_member_status = chat_member.status

        if chat_member_status != ChatMember.CREATOR:
            context.bot.send_message(chat_id=chat.id, text='I only respond to ChatMember CREATOR', disable_notification=True)
            return

        else:
            chat_member = context.bot.get_chat_member(chat.id,bot_id)
            bot_status = chat_member.status

            if bot_status == ChatMember.MEMBER:
                text = 'You must put me as chat administrator to use /settings'
                context.bot.send_message(chat_id=chat.id, text=text, disable_notification=True)

            else:
                keyboard = [
                [
                    InlineKeyboardButton("Opening hours", callback_data=str(Opening_hours_menu)),
                ],
                [
                    InlineKeyboardButton("Voice messages", callback_data=str(Voice_message_menu)),
                ],
                [
                    InlineKeyboardButton("Time zone", callback_data=str(Time_zone_menu)),
                ],
                [
                    InlineKeyboardButton("Close", callback_data=str(Close)) 
                ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                reply_text = "Settings:\n" 
                if update.message:       
                    context.chat_data[SETTINGS_MESSAGE_ID] = message_id
                    context.user_data[USER_ID] = user_id

                    if context.chat_data.get(FIRST_TIME_SETTINGS_MENU) == True:
                        time_zone_str = context.bot_data.get(chat.id)
                        time_zone = pytz.timezone(time_zone_str)
                        context.chat_data[TIME_ZONE] = time_zone
                        date_time_now = datetime.datetime.now(time_zone)
                        context.chat_data[CHAT_DATE_TIME_NOW] = date_time_now
                        current_time = date_time_now.strftime("%d/%m/%Y %H:%M")
                        context.chat_data[CHAT_CURRENT_TIME] = current_time
                        weekday_number = int(date_time_now.strftime("%w"))  
                        context.chat_data[OPENING_HOURS_WEEKDAY_NUMBER] = weekday_number
                    else:
                        context.chat_data[FIRST_TIME_OPENING_HOURS_MENU] = True
                        context.chat_data[FIRST_TIME_VOICE_MENU] = True
                        context.chat_data[VOICE_DELETE_STATUS_ACTIVED] = False
                        context.chat_data[OPENING_HOURS_STATUS_OPEN] = True
                        context.chat_data[FIRST_TIME_SETTINGS_MENU] = True
                        time_zone_str=tzlocal.get_localzone_name()
                        time_zone = pytz.timezone(time_zone_str)
                        context.chat_data[TIME_ZONE] = time_zone
                        context.bot_data.update({chat.id:time_zone_str})
                        date_time_now = datetime.datetime.now(time_zone)
                        context.chat_data[CHAT_DATE_TIME_NOW] = date_time_now
                        current_time = date_time_now.strftime("%d/%m/%Y %H:%M")
                        context.chat_data[CHAT_CURRENT_TIME] = current_time
                        weekday_number = int(date_time_now.strftime("%w"))  
                        context.chat_data[OPENING_HOURS_WEEKDAY_NUMBER] = weekday_number
                    
                    if context.chat_data[VOICE_DELETE_STATUS_ACTIVED] == True and context.chat_data[OPENING_HOURS_STATUS_OPEN] == False:
                        
                        reply_text += f"Opening hours: Permanently Closed\n Voice messages: Forbidden\nTime Zone: {time_zone} ({current_time})"

                    elif context.chat_data[VOICE_DELETE_STATUS_ACTIVED] == True and context.chat_data[OPENING_HOURS_STATUS_OPEN] == True:
                        if len(delete_message_list) != 0:
                            reply_text += f"Opening hours: Closed\nVoice messages: Forbidden\nTime Zone: {time_zone} ({current_time})"
                        else:
                            reply_text += f"Opening hours: Open\nVoice messages: Forbidden\nTime Zone: {time_zone} ({current_time})"
                            
                    elif context.chat_data[VOICE_DELETE_STATUS_ACTIVED] == False and context.chat_data[OPENING_HOURS_STATUS_OPEN] == False:
                        reply_text += f"Opening hours: Permanently closed\nVoice messages: Allowed\nTime Zone: {time_zone} - ({current_time})"   
                        
                    elif context.chat_data[VOICE_DELETE_STATUS_ACTIVED] == False and context.chat_data[OPENING_HOURS_STATUS_OPEN] == True:
                        if len(delete_message_list) != 0:
                            reply_text += f"Opening hours: Closed\nVoice messages: Allowed\nTime Zone: {time_zone} ({current_time})"
                        else:
                            reply_text += f"Opening hours: Open\nVoice messages: Allowed\nTime Zone: {time_zone} ({current_time})"

                    context.bot.send_message(chat.id, reply_text, reply_markup=reply_markup, disable_notification=True)    
                    return SETTINGS_MENU

                else:
                    chat_member = context.bot.get_chat_member(chat.id,user_id)
                    chat_member_status = chat_member.status

                    if chat_member_status != ChatMember.CREATOR:
                        query.answer(text='You must be ChatMember CREATOR')
                        return
                    else:
                        query.answer()
                        if context.chat_data[VOICE_DELETE_STATUS_ACTIVED] == True and context.chat_data[OPENING_HOURS_STATUS_OPEN] == False:
                            reply_text += f"Opening hours: Permanently closed\n Voice messages: Forbidden\nTime Zone: {time_zone} - ({current_time})"
                        
                        elif context.chat_data[VOICE_DELETE_STATUS_ACTIVED] == True and context.chat_data[OPENING_HOURS_STATUS_OPEN] == True:
                            if len(delete_message_list) != 0:
                                reply_text += f"Opening hours: Closed\nVoice messages: Forbidden\nTime Zone: {time_zone} - ({current_time})"
                            else:
                                reply_text += f"Opening hours: Open\nVoice messages: Forbidden\nTime Zone: {time_zone} - ({current_time})"

                        elif context.chat_data[VOICE_DELETE_STATUS_ACTIVED] == False and context.chat_data[OPENING_HOURS_STATUS_OPEN] == False:
                            reply_text += f"Opening hours: Permanently closed\nVoice messages: Allowed\nTime Zone: {time_zone} - ({current_time})"

                        elif context.chat_data[VOICE_DELETE_STATUS_ACTIVED] == False and context.chat_data[OPENING_HOURS_STATUS_OPEN] == True:
                            if len(delete_message_list) != 0:
                                reply_text += f"Opening hours: Closed\nVoice messages: Allowed\nTime Zone: {time_zone} - ({current_time})"
                            else:
                                reply_text += f"Opening hours: Open\nVoice messages: Allowed\nTime Zone: {time_zone} - ({current_time})"
                        
                        query.edit_message_text(reply_text, reply_markup=reply_markup)
                        return SETTINGS_MENU


def close_setings(update: Update, context: CallbackContext) -> int:
    """Delete the keyboard buttons"""
    query = update.callback_query
    chat = query.message.chat
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    chat_member_status = chat_member.status

    if chat_member_status != ChatMember.CREATOR:
        query.answer(text='You must be ChatMember CREATOR')
        return
    else:
        query.answer()
        must_delete = query.message
        context.bot.deleteMessage(chat.id, must_delete.message_id)

        """Delete /setings"""
        message_id_setings = context.chat_data.get(SETTINGS_MESSAGE_ID)
        context.bot.delete_message(chat.id, message_id_setings)
        return

""" VOICE MESSAGE MENU """

def voice_delete(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = query.message.chat
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    chat_member_status = chat_member.status

    if chat_member_status != ChatMember.CREATOR:
        query.answer(text='You must be ChatMember CREATOR')
        return
    else:
        query.answer()

        keyboard_voice_delete_inactived = [
            [
                InlineKeyboardButton("Activate", callback_data=str(Activate)),
            ],
            [
                InlineKeyboardButton("Back", callback_data=str(Back))
            ],
        ]
        inline_keyboard_voice_delete_inactived = InlineKeyboardMarkup(keyboard_voice_delete_inactived)

        keyboard_voice_delete_actived_off = [
            [
                InlineKeyboardButton("Inactivate", callback_data=str(Inactivate))
            ],
            [
                InlineKeyboardButton("Notifications: Activate", callback_data=str(Turn_notification_on))
            ],
            [
                InlineKeyboardButton("Back", callback_data=str(Back))
            ],
        ]
        inline_keyboard_voice_delete_actived_off = InlineKeyboardMarkup(keyboard_voice_delete_actived_off)

        keyboard_voice_delete_actived_on = [
            [
                InlineKeyboardButton("Inactivate", callback_data=str(Inactivate))
            ],
            [
                InlineKeyboardButton("Notifications: Inactivate", callback_data=str(Turn_notification_off))
            ],
            [
                InlineKeyboardButton("Back", callback_data=str(Back))
            ],
        ]
        inline_keyboard_voice_delete_actived_on = InlineKeyboardMarkup(keyboard_voice_delete_actived_on)

        if context.chat_data[FIRST_TIME_VOICE_MENU] == True:
            context.chat_data[VOICE_DELETE_NOTIFICATIONS_ON] = False
            context.chat_data[VOICE_STATUS] = 'Inactived'
            context.chat_data[FIRST_TIME_VOICE_MENU] = False

        if query.data == str(Turn_notification_on):
            context.chat_data[VOICE_DELETE_NOTIFICATIONS_ON] = True

        elif query.data == str(Turn_notification_off):
            context.chat_data[VOICE_DELETE_NOTIFICATIONS_ON] = False

        elif query.data == str(Activate):
            status = 'Actived'
            context.chat_data[VOICE_STATUS] = status
            context.chat_data[VOICE_DELETE_STATUS_ACTIVED] = True

        elif query.data == str(Inactivate):
            status = 'Inactived'
            context.chat_data[VOICE_STATUS] = status
            context.chat_data[VOICE_DELETE_STATUS_ACTIVED] = False

        reply_text = "Delete voice messages\n"
        
        status = context.chat_data.get(VOICE_STATUS)
        reply_text += (f'Status: {status}\n')
        
        if context.chat_data[VOICE_STATUS] == 'Actived':
            if context.chat_data[VOICE_DELETE_NOTIFICATIONS_ON] == False:
                reply_text +='Notifications: Off'
                reply_markup=inline_keyboard_voice_delete_actived_off
            else:
                reply_text +='Notifications: On'
                reply_markup=inline_keyboard_voice_delete_actived_on
        else:   
            reply_markup=inline_keyboard_voice_delete_inactived
        
        query.edit_message_text(reply_text, reply_markup=reply_markup)
        return VOICE_MENU   

"""OPENING_HOURS_MENU"""

def opening_hours(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    chat = query.message.chat
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    chat_member_status = chat_member.status

    if chat_member_status != ChatMember.CREATOR:
        query.answer(text='You must be ChatMember CREATOR')
        return
    else:
        query.answer()

        keyboard_opening_hours_closed_off = [
            [
                InlineKeyboardButton("Open", callback_data=str(Open)),
            ],
            [
                InlineKeyboardButton("Notification: Active", callback_data=str(Turn_notification_on))
            ],
            [
                InlineKeyboardButton("Back", callback_data=str(Back))
            ],
        ]
        inline_keyboard_opening_hours_closed_off = InlineKeyboardMarkup(keyboard_opening_hours_closed_off)

        keyboard_opening_hours_closed_on = [
            [
                InlineKeyboardButton("Open", callback_data=str(Open)),
            ],
            [
                InlineKeyboardButton("Notification: Inactive", callback_data=str(Turn_notification_off))
            ],
            [
                InlineKeyboardButton("Back", callback_data=str(Back))
            ],
        ]
        inline_keyboard_opening_hours_closed_on = InlineKeyboardMarkup(keyboard_opening_hours_closed_on)

        keyboard_opening_hours_open_off = [
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
                InlineKeyboardButton("Notifications: Active", callback_data=str(Turn_notification_on))
            ],
            [
                InlineKeyboardButton("Back", callback_data=str(Back))
            ],
        ]
        inline_keyboard_opening_hours_open_off = InlineKeyboardMarkup(keyboard_opening_hours_open_off)

        keyboard_opening_hours_open_on = [
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
                InlineKeyboardButton("Notification: Inactive", callback_data=str(Turn_notification_off))
            ],
            [
                InlineKeyboardButton("Back", callback_data=str(Back))
            ],
        ]
        inline_keyboard_opening_hours_open_on = InlineKeyboardMarkup(keyboard_opening_hours_open_on)

        if context.chat_data[FIRST_TIME_OPENING_HOURS_MENU] == True:
            context.chat_data[OPENING_HOURS_STATUS] = 'Open'
            context.chat_data[OPENING_HOURS_TIME] = '24h'
            context.chat_data[OPENING_HOURS_WEEK] = 'Everyday'
            context.chat_data[OPENING_HOURS_STATUS_OPEN] == True
            context.chat_data[OPENING_HOURS_NOTIFICATIONS_ON] = False
            context.chat_data[JOB_STATUS_CHANGE] = True
            context.chat_data[OPENING_HOURS_CLOSE_TIME] = False
            context.chat_data[FIRST_TIME_OPENING_HOURS_MENU] = False
            
        elif query.data == str(Turn_notification_on):
            context.chat_data[OPENING_HOURS_NOTIFICATIONS_ON] = True
            context.chat_data[JOB_STATUS_CHANGE] = True

        elif query.data == str(Turn_notification_off):
            context.chat_data[OPENING_HOURS_NOTIFICATIONS_ON] = False
            context.chat_data[JOB_STATUS_CHANGE] = True

        elif (query.data == "0" or query.data == "1" or query.data == "2" or query.data == "3" or query.data == "4" or query.data == "5" or query.data == "6" 
        or query.data == "7" or query.data == "8" or query.data == "9" or query.data == "10" or query.data == "11" or query.data == "12" or query.data == "13" 
        or query.data == "14" or query.data == "15" or query.data == "16" or query.data == "17" or query.data == "18" or query.data == "19" or query.data == "20" 
        or query.data == "21" or query.data == "22" or query.data == "23"):

            open_time = context.chat_data.get(OPENING_HOURS_OPEN_TIME_TEMP)
            if query.data == open_time:
                query.answer(text='Closed time must be different than open time', show_alert=True) 
                return
            else:
                context.chat_data[OPENING_HOURS_TIME] = query.data
                context.chat_data[OPENING_HOURS_OPEN_TIME] = open_time
                context.chat_data[OPENING_HOURS_CLOSE_TIME] = query.data
                context.chat_data[JOB_STATUS_CHANGE] = True

        elif query.data == 'Everyday' or query.data == 'Weekdays' or query.data == 'Weekends':
                context.chat_data[OPENING_HOURS_WEEK] = query.data
                context.chat_data[JOB_STATUS_CHANGE] = True

        elif query.data == '24h':
            context.chat_data[OPENING_HOURS_TIME] = query.data
            context.chat_data[OPENING_HOURS_CLOSE_TIME] = False
            context.chat_data[JOB_STATUS_CHANGE] = True

        elif query.data == str(Open):
            if len(delete_message_list) != 0:
                status = 'Closed'
            else:
                status = 'Open'
            context.chat_data[OPENING_HOURS_STATUS] = status
            context.chat_data[OPENING_HOURS_STATUS_OPEN] = True
            context.chat_data[JOB_STATUS_CHANGE] = True

        time_zone = context.chat_data.get(TIME_ZONE)
        weekday_number = context.chat_data.get(OPENING_HOURS_WEEKDAY_NUMBER)
        date_time_now = context.chat_data.get(CHAT_DATE_TIME_NOW)

        if context.chat_data.get(OPENING_HOURS_TIME) == '24h':
            open_time = int('0')    
            date_time_open = datetime.time(hour=open_time, tzinfo=time_zone)
            weekdays = context.chat_data.get(OPENING_HOURS_WEEK)
        else: 
            open_time = int(context.chat_data.get(OPENING_HOURS_OPEN_TIME))
            close_time = int(context.chat_data.get(OPENING_HOURS_CLOSE_TIME))
            weekdays = context.chat_data.get(OPENING_HOURS_WEEK)
            date_time_open = datetime.time(hour=open_time, tzinfo=time_zone)
            date_time_closed = datetime.time(hour=close_time, tzinfo=time_zone)

        if context.chat_data[JOB_STATUS_CHANGE] == True:
            context.chat_data[JOB_STATUS_CHANGE] = False
            var_list.clear()
            if context.chat_data.get(OPENING_HOURS_TIME) == '24h':
                var_list.append(open_time)
                var_list.append(weekdays)
            else:
                var_list.append(open_time)
                var_list.append(close_time)
                var_list.append(weekdays)
            
            if context.chat_data[OPENING_HOURS_NOTIFICATIONS_ON] == True:

                remove_job_if_exists(str(OPENING_HOURS_OPEN_TIME_JOB), context)
                remove_job_if_exists(str(OPENING_HOURS_CLOSE_TIME_JOB), context)
                remove_job_if_exists(str(OPENING_HOURS_WEEKDAYS_JOB), context)
                remove_job_if_exists(str(OPENING_HOURS_WEEKEND_JOB), context)

                if context.chat_data.get(OPENING_HOURS_TIME) == '24h':
                    if context.chat_data.get(OPENING_HOURS_WEEK) == 'Everyday':
                        text = 'Messages are allowed'
                        context.bot.send_message(chat.id, text)

                    elif context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekdays':
                        if weekday_number == 0 or weekday_number == 6:
                            delete_message_list.append('on')         
                            context.job_queue.run_daily(job_24h_week_notification, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_WEEKDAYS_JOB))
                            text = 'From this moment, until next monday 0h, messages sent will be deleted'
                            context.bot.send_message(chat.id, text, disable_notification=True)
                        else:
                            context.job_queue.run_daily(job_24h_week_notification, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_WEEKDAYS_JOB))
                            text = 'Messages are allowed'
                            context.bot.send_message(chat.id, text, disable_notification=True)

                    elif context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekends':
                        if weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                            delete_message_list.append('on')     
                            context.job_queue.run_daily(job_24h_weekend_notification, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_WEEKEND_JOB))
                            text = 'From this moment, until next saturday 0h, messages sent will be deleted'
                            context.bot.send_message(chat.id, text, disable_notification=True)
                        else:
                            context.job_queue.run_daily(job_24h_weekend_notification, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_WEEKEND_JOB))
                            text = 'Messages are allowed'
                            context.bot.send_message(chat.id, text, disable_notification=True)
                            
                else:
                    if open_time < close_time:
                        if context.chat_data.get(OPENING_HOURS_WEEK) == 'Everyday':
                            if date_time_now.hour < date_time_open.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open_notification, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat.id, text, disable_notification=True)
                                        
                            elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:                                   
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                context.job_queue.run_daily(job_open_notification, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                text = 'Messages are allowed'
                                context.bot.send_message(chat.id, text, disable_notification=True)
                                
                            elif date_time_now.hour >= date_time_closed.hour:
                                delete_message_list.append('on')                  
                                context.job_queue.run_daily(job_open_notification, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat.id, text, disable_notification=True)
                                                
                        elif context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekdays':
                            if weekday_number == 0 or weekday_number == 6:
                                delete_message_list.append('on')                                  
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                text = f'From this moment, until next monday {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat.id, text, disable_notification=True)
                            else:
                                if date_time_now.hour < date_time_open.hour:
                                    delete_message_list.append('on')                
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                    context.bot.send_message(chat.id, text, disable_notification=True)
                                            
                                elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:                                    
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    text = 'Messages are allowed'
                                    context.bot.send_message(chat.id, text, disable_notification=True)

                                elif date_time_now.hour >= date_time_closed.hour:
                                    delete_message_list.append('on')
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                    context.bot.send_message(chat.id, text, disable_notification=True)                    

                        elif context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekends':
                            if  weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                                delete_message_list.append('on')                                   
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(5,6), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                text = f'From this moment, until next saturday {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat.id, text, disable_notification=True)
                            else:
                                if date_time_now.hour < date_time_open.hour:
                                    delete_message_list.append('on')                
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(5,6), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                    context.bot.send_message(chat.id, text, disable_notification=True)
                                            
                                elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:                                    
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(5,6), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    text = 'Messages are allowed'
                                    context.bot.send_message(chat.id, text, disable_notification=True)

                                elif date_time_now.hour >= date_time_closed.hour:
                                    delete_message_list.append('on')
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(5,6), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB)) 
                                    text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                    context.bot.send_message(chat.id, text, disable_notification=True)

                    elif open_time > close_time:
                        if context.chat_data.get(OPENING_HOURS_WEEK) == 'Everyday':
                            if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open_notification, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat.id, text, disable_notification=True)
                                        
                            elif date_time_now.hour >= date_time_open.hour:                                    
                                context.job_queue.run_daily(job_open_notification, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                text = 'Messages are allowed'
                                context.bot.send_message(chat.id, text, disable_notification=True)

                            elif date_time_now.hour < date_time_closed.hour:
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                context.job_queue.run_daily(job_open_notification, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                text = 'Messages are allowed'
                                context.bot.send_message(chat.id, text, disable_notification=True)

                        elif context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekdays':
                            if weekday_number == 0 or weekday_number == 6:
                                delete_message_list.append('on')                                  
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                text = f'From this moment, until next monday {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat.id, text, disable_notification=True)
                            else:
                                if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                                    delete_message_list.append('on')                
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                    context.bot.send_message(chat.id, text, disable_notification=True)
                                        
                                elif date_time_now.hour >= date_time_open.hour:                                    
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    text = 'Messages are allowed'
                                    context.bot.send_message(chat.id, text, disable_notification=True)

                                elif date_time_now.hour < date_time_closed.hour:
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(0,1,2,3), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    text = 'Messages are allowed'
                                    context.bot.send_message(chat.id, text, disable_notification=True)                    

                        elif context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekends':
                            if  weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                                delete_message_list.append('on')                                   
                                context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(6,0), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                text = f'From this moment, until next saturday {open_time}h, messages sent will be deleted'
                                context.bot.send_message(chat.id, text, disable_notification=True)
                            else:
                                if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                                    delete_message_list.append('on')                
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(6,0), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    text = f'From this moment, until {open_time}h, messages sent will be deleted'
                                    context.bot.send_message(chat.id, text, disable_notification=True)
                                        
                                elif date_time_now.hour >= date_time_open.hour:                                    
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(6,0), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    text = 'Messages are allowed'
                                    context.bot.send_message(chat.id, text, disable_notification=True)

                                elif date_time_now.hour < date_time_closed.hour:
                                    context.job_queue.run_daily(job_closed_notification, date_time_closed, days=(6,0), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    context.job_queue.run_daily(job_open_notification, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    text = 'Messages are allowed'
                                    context.bot.send_message(chat.id, text, disable_notification=True)                   

            elif context.chat_data[OPENING_HOURS_NOTIFICATIONS_ON] == False:
                remove_job_if_exists(str(OPENING_HOURS_OPEN_TIME_JOB), context)
                remove_job_if_exists(str(OPENING_HOURS_CLOSE_TIME_JOB), context)
                remove_job_if_exists(str(OPENING_HOURS_WEEKDAYS_JOB), context)
                remove_job_if_exists(str(OPENING_HOURS_WEEKEND_JOB), context)

                if context.chat_data.get(OPENING_HOURS_TIME) == '24h':
                    if context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekdays':
                        if weekday_number == 0 or weekday_number == 6:
                            delete_message_list.append('on')         
                            context.job_queue.run_daily(job_24h_week, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_WEEKDAYS_JOB))
                        else:
                            context.job_queue.run_daily(job_24h_week, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_WEEKDAYS_JOB))

                    elif context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekends':
                        if weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                            delete_message_list.append('on')     
                            context.job_queue.run_daily(job_24h_weekend, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_WEEKEND_JOB))
                        else:
                            context.job_queue.run_daily(job_24h_weekend, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_WEEKEND_JOB))
                        
                else:
                    if open_time < close_time:
                        if context.chat_data.get(OPENING_HOURS_WEEK) == 'Everyday':
                            if date_time_now.hour < date_time_open.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))

                            elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:
                                context.job_queue.run_daily(job_closed, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))                 
                                context.job_queue.run_daily(job_open, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))

                            elif date_time_now.hour >= date_time_closed.hour:
                                delete_message_list.append('on')                                    
                                context.job_queue.run_daily(job_open, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                                
                        elif context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekdays':
                            if weekday_number == 0 or weekday_number == 6:
                                delete_message_list.append('on')                                  
                                context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                            else:
                                if date_time_now.hour < date_time_open.hour:
                                    delete_message_list.append('on')                
                                    context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))

                                elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))                 
                                    context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))

                                elif date_time_now.hour >= date_time_closed.hour:
                                    delete_message_list.append('on')                                    
                                    context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(0,1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))                    

                        elif context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekends':
                            if  weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                                delete_message_list.append('on')                                   
                                context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(5,6), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                            else:
                                if date_time_now.hour < date_time_open.hour:
                                    delete_message_list.append('on')                
                                    context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(5,6), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))

                                elif date_time_now.hour >= date_time_open.hour and date_time_now.hour < date_time_closed.hour:
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(5,6), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))                 
                                    context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))

                                elif date_time_now.hour >= date_time_closed.hour:
                                    delete_message_list.append('on')                                    
                                    context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(5,6), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))

                    elif open_time > close_time:
                        if context.chat_data.get(OPENING_HOURS_WEEK) == 'Everyday':
                            if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                                delete_message_list.append('on')                
                                context.job_queue.run_daily(job_open, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                        
                            elif date_time_now.hour >= date_time_open.hour:                                    
                                context.job_queue.run_daily(job_open, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))

                            elif date_time_now.hour < date_time_closed.hour:
                                context.job_queue.run_daily(job_closed, date_time_closed, context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                context.job_queue.run_daily(job_open, date_time_open, context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))

                        elif context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekdays':
                            if weekday_number == 0 or weekday_number == 6:
                                delete_message_list.append('on')                                  
                                context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                            else:
                                if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                                    delete_message_list.append('on')                
                                    context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                        
                                elif date_time_now.hour >= date_time_open.hour:                                    
                                    context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))

                                elif date_time_now.hour < date_time_closed.hour:
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(1,2,3,4), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    context.job_queue.run_daily(job_open, date_time_open, days=(0,1,2,3), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))                    

                        elif context.chat_data.get(OPENING_HOURS_WEEK) == 'Weekends':
                            if  weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
                                delete_message_list.append('on')                                   
                                context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                context.job_queue.run_daily(job_closed, date_time_closed, days=(6,0), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                            else:
                                if date_time_now.hour < date_time_open.hour and date_time_now.hour > date_time_closed.hour:
                                    delete_message_list.append('on')                
                                    context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(6,0), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                        
                                elif date_time_now.hour >= date_time_open.hour:                                    
                                    context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(6,0), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))

                                elif date_time_now.hour < date_time_closed.hour:
                                    context.job_queue.run_daily(job_closed, date_time_closed, days=(6,0), context=chat.id, name=str(OPENING_HOURS_CLOSE_TIME_JOB))
                                    context.job_queue.run_daily(job_open, date_time_open, days=(5,6), context=chat.id, name=str(OPENING_HOURS_OPEN_TIME_JOB))

        reply_text = "Opening hours\n"
        
        if len(delete_message_list) != 0:
            if context.chat_data[OPENING_HOURS_STATUS_OPEN] == False:
                status = 'Permanently Closed'
            else:
                status = 'Closed'
        else:
            status = context.chat_data.get(OPENING_HOURS_STATUS)
        
        reply_text += (f'Status: {status}\n')

        if context.chat_data[OPENING_HOURS_STATUS_OPEN] == True:
            if context.chat_data[OPENING_HOURS_CLOSE_TIME] == False:
                time = context.chat_data.get(OPENING_HOURS_TIME)
                reply_text += (f'Time: {time}\n')
            else:
                open_time = context.chat_data.get(OPENING_HOURS_OPEN_TIME)
                close_time = context.chat_data.get(OPENING_HOURS_CLOSE_TIME)
                reply_text += f"Open hour: {open_time}h\nClose hour: {close_time}h\n"

            weekday_status = context.chat_data.get(OPENING_HOURS_WEEK)        
            reply_text += (f'Days: {weekday_status}\n')

            if context.chat_data[OPENING_HOURS_NOTIFICATIONS_ON] == True:
                reply_text +='Notification: On\n'
                reply_markup=inline_keyboard_opening_hours_open_on
            else:
                reply_text +='Notification: Off\n'
                reply_markup=inline_keyboard_opening_hours_open_off          

        else:
            if context.chat_data[OPENING_HOURS_NOTIFICATIONS_ON] == True:
                reply_text +='Notification: On\n'
                reply_markup=inline_keyboard_opening_hours_closed_on
            else:
                reply_markup=inline_keyboard_opening_hours_closed_off
                reply_text +='Notification: Off\n'

        query.edit_message_text(reply_text, reply_markup=reply_markup)
        return OPENING_HOURS_MENU

def opening_hours_permanently_closed(update:  Update, context: CallbackContext):
    query = update.callback_query
    chat = query.message.chat
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    chat_member_status = chat_member.status

    if chat_member_status != ChatMember.CREATOR:
        query.answer(text='You must be ChatMember CREATOR')
        return
    else:
        query.answer()
        keyboard_opening_hours_closed = [
            [
                InlineKeyboardButton("Open", callback_data=str(Open)),
            ],
            [
                InlineKeyboardButton("Back", callback_data=str(Back))
            ],
        ]
        inline_keyboard_opening_hours_closed = InlineKeyboardMarkup(keyboard_opening_hours_closed)

        reply_text = f"Opening hours\n"

        status = 'Permanently closed'
        reply_text += f"Status: {status}\n"
    
        reply_markup = inline_keyboard_opening_hours_closed
    
        if context.chat_data[OPENING_HOURS_STATUS_OPEN] == True and len(delete_message_list) == 0 and context.chat_data[OPENING_HOURS_NOTIFICATIONS_ON] == True:
            chat_id = query.message.chat.id
            reply_text = 'Messages sent will be deleted'
            context.bot.send_message(chat_id,reply_text)

        query.edit_message_text(reply_text, reply_markup=reply_markup)

        remove_job_if_exists(str(OPENING_HOURS_OPEN_TIME_JOB), context)
        remove_job_if_exists(str(OPENING_HOURS_CLOSE_TIME_JOB), context)
        remove_job_if_exists(str(OPENING_HOURS_WEEKDAYS_JOB), context)
        remove_job_if_exists(str(OPENING_HOURS_WEEKEND_JOB), context)
        context.chat_data[OPENING_HOURS_STATUS_OPEN] = False
        context.chat_data[JOB_STATUS_CHANGE] = True
        context.chat_data[OPENING_HOURS_STATUS] = status

        return OPENING_HOURS_MENU

def opening_hours_set_time(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = query.message.chat
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    chat_member_status = chat_member.status

    if chat_member_status != ChatMember.CREATOR:
        query.answer(text='You must be ChatMember CREATOR')
        return
    else:
        keyboard = [
            [
                InlineKeyboardButton("24h", callback_data=str('24h'))
            ],
            [
                InlineKeyboardButton("Set open/closed time", callback_data=str(Activate))
            ],
            [
                InlineKeyboardButton("Back", callback_data=str(Back))
            ],
        ]

        opening_hours_time_status = context.chat_data.get(OPENING_HOURS_TIME)

        reply_text = f"Time set for opening hours\n"

        if context.chat_data[OPENING_HOURS_CLOSE_TIME] == False:
            reply_text += f"Status: {opening_hours_time_status}"

        else:
            open_time = context.chat_data.get(OPENING_HOURS_OPEN_TIME)
            close_time = context.chat_data.get(OPENING_HOURS_CLOSE_TIME)
            reply_text += f"Open hour: {open_time}h\nClose hour: {close_time}h"

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(reply_text, reply_markup=reply_markup)

        return SET_DAYS_AND_OPEN_CLOSE_TIME

def opening_hours_set_open_time(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = query.message.chat
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    chat_member_status = chat_member.status

    if chat_member_status != ChatMember.CREATOR:
        query.answer(text='You must be ChatMember CREATOR')
        return
    else:

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

        return SET_DAYS_AND_OPEN_CLOSE_TIME

def opening_hours_set_closed_time(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = query.message.chat
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    chat_member_status = chat_member.status

    if chat_member_status != ChatMember.CREATOR:
        query.answer(text='You must be ChatMember CREATOR')
        return
    else:
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

        context.chat_data[OPENING_HOURS_OPEN_TIME_TEMP] = open_time

        return OPENING_HOURS_MENU

def opening_hours_set_week_days(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = query.message.chat
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    chat_member_status = chat_member.status

    if chat_member_status != ChatMember.CREATOR:
        query.answer(text='You must be ChatMember CREATOR')
        return
    else:
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

        opening_hours_days_status = context.chat_data.get(OPENING_HOURS_WEEK)

        reply_text = f"Set days for opening hours\nStatus: {opening_hours_days_status}"

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(reply_text, reply_markup=reply_markup)
        context.chat_data[OPENING_HOURS_WEEK] = opening_hours_days_status    
        
        return SET_DAYS_AND_OPEN_CLOSE_TIME

def job_open_notification(context: CallbackContext):
    delete_message_list.clear()
    job = context.job
    context.bot.send_message(job.context, text='Messages are allowed', disable_notification=True)    

def job_closed_notification(context: CallbackContext):
    date_time_now = context.chat_data.get(CHAT_DATE_TIME_NOW)
    job = context.job
    open_time = var_list[0]
    close_time = var_list[1]
    weekdays = var_list[2]
    weekday_number = int(date_time_now.strftime("%w"))

    if open_time < close_time:
        delete_message_list.append('on')
        if weekdays == 'Everyday':
            context.bot.send_message(job.context, text=f'From this moment, until {open_time}h, messages sent will be deleted', disable_notification=True)

        elif weekdays == 'Weekdays':
            if weekday_number == 5:
                context.bot.send_message(job.context, text=f'From this moment, until next monday {open_time}h, messages sent will be deleted', disable_notification=True)
            else:
                context.bot.send_message(job.context, text=f'From this moment, until {open_time}h, messages sent will be deleted', disable_notification=True)

        elif weekdays == 'Weekends':
            if weekday_number == 0:
                context.bot.send_message(job.context, text=f'From this moment, until next saturday {open_time}h, messages sent will be deleted', disable_notification=True)
            else:
                context.bot.send_message(job.context, text=f'From this moment, until {open_time}h, messages sent will be deleted', disable_notification=True)
    else:
        if weekdays == 'Everyday':
            delete_message_list.append('on')
            context.bot.send_message(job.context, text=f'From this moment, until {open_time}h, messages sent will be deleted', disable_notification=True)
        
        elif weekdays == 'Weekdays':
            delete_message_list.append('on')
            if weekday_number == 5:
                context.bot.send_message(job.context, text=f'From this moment, until next monday {open_time}h, messages sent will be deleted', disable_notification=True)
            else:
                context.bot.send_message(job.context, text=f'From this moment, until {open_time}h, messages sent will be deleted', disable_notification=True)

        elif weekdays == 'Weekends':
            if weekday_number == 0:
                delete_message_list.append('on')
                context.bot.send_message(job.context, text=f'From this moment, until next saturday {open_time}h, messages sent will be deleted', disable_notification=True)

def job_24h_week_notification(context: CallbackContext):
    date_time_now = context.chat_data.get(CHAT_DATE_TIME_NOW)
    weekday_number = int(date_time_now.strftime("%w"))
    job = context.job
    if weekday_number == 6 or weekday_number == 0:
        if len(delete_message_list) != 0: 
            delete_message_list.append('on')
            context.bot.send_message(job.context, text='From this moment until next monday 0h, messages sent will be deleted', disable_notification=True)
    else:
        delete_message_list.clear()
        context.bot.send_message(job.context, text='Messages are allowed', disable_notification=True)

def job_24h_weekend_notification(context: CallbackContext):
    date_time_now = context.chat_data.get(CHAT_DATE_TIME_NOW)
    weekday_number = int(date_time_now.strftime("%w"))
    job = context.job
    if weekday_number == 1 or weekday_number == 2 or weekday_number == 3 or weekday_number == 4 or weekday_number == 5:
        if len(delete_message_list) != 0:
            delete_message_list.append('on')
            context.bot.send_message(job.context, text='From this moment until next saturday 0h, messages sent will be deleted', disable_notification=True)
    else:
        delete_message_list.clear()
        context.bot.send_message(job.context, text='Messages are allowed', disable_notification=True)

def job_open(context: CallbackContext): 
    delete_message_list.clear()   

def job_closed(context: CallbackContext):
    date_time_now = context.chat_data.get(CHAT_DATE_TIME_NOW)
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
    date_time_now = context.chat_data.get(CHAT_DATE_TIME_NOW)
    weekday_number = int(date_time_now.strftime("%w"))
    if weekday_number == 6 or weekday_number == 0:
        delete_message_list.append('on')
    else:
        delete_message_list.clear()

def job_24h_weekend(context: CallbackContext):
    date_time_now = context.chat_data.get(CHAT_DATE_TIME_NOW)
    weekday_number = int(date_time_now.strftime("%w"))
    if not weekday_number == 6 or not weekday_number == 0:
        delete_message_list.append('on')
    else:
        delete_message_list.clear()

def remove_job_if_exists(name: str,context: CallbackContext):
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        delete_message_list.clear()
        job.schedule_removal()
    return True
        
"""CHOOSE TIME ZONE"""

def time_zone_change(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = query.message.chat
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    chat_member_status = chat_member.status

    if chat_member_status != ChatMember.CREATOR:
        query.answer(text='You must be ChatMember CREATOR')
        return
    else:
        query.answer()
        time_zone = context.chat_data.get(TIME_ZONE)
        current_time = context.chat_data.get(CHAT_CURRENT_TIME)

        keyboard = [
            [
                InlineKeyboardButton("Change", callback_data=str(Change_time_zone)),
            ],
            [
                InlineKeyboardButton("Back", callback_data=str(Back))
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        reply_text = f"Change time zone\nCurrent:{time_zone}({current_time})"
        query.edit_message_text(reply_text, reply_markup=reply_markup)
        context.user_data[CHAT_CURRENT_TIME] = current_time

        return TIME_ZONE_MENU

def time_zone_send_location(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat = query.message.chat
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    chat_member_status = chat_member.status
    
    if chat.type == Chat.PRIVATE:      
        must_delete = query.message
        context.bot.deleteMessage(chat.id, must_delete.message_id)

        location_button = KeyboardButton(text="send_location", request_location=True)
        keyboard = [
            [
                location_button,"Cancel"
            ],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True ,one_time_keyboard=True)
        context.bot.send_message(chat.id, text= "type the city name of your location, or send your location", reply_markup=reply_markup, disable_notification=True)

        return CHANGE_TIME_ZONE_IN_PRIVATE
    else:
        if chat_member_status != ChatMember.CREATOR:
            query.answer(text='You must be ChatMember CREATOR')
            return

        else:
            keyboard = [
            [
                InlineKeyboardButton("Open in private", callback_data=str(Go_private)),
            ],
            [
                InlineKeyboardButton("Back", callback_data=str(Back))
            ],
        ]
            reply_markup = InlineKeyboardMarkup(keyboard, resize_keyboard=True ,one_time_keyboard=True)
            query.edit_message_text(text= "Time zone only can be set in private chat", reply_markup=reply_markup)

            return SET_TIME_ZONE

def go_to_bot_private_chat(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = query.message.chat
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member(chat.id,user_id)
    chat_member_status = chat_member.status

    if chat_member_status != ChatMember.CREATOR:
        query.answer(text='You must be ChatMember CREATOR')
        return
    else:
        keyboard = [
            [
                InlineKeyboardButton("Go to private", url="http://telegram.me/Luis_first_bot"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text= "Settings sent in private chat", reply_markup = reply_markup)

def time_zone_change_in_private(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    go_to_bot_private_chat(update, context)

    chat_id = query.message.chat.id
    chat_title = query.message.chat.title
    context.user_data[CHAT_TITLE] = chat_title
    time_zone = context.bot_data.get(chat_id)
    current_time = context.user_data.get(CHAT_CURRENT_TIME)
    chat_invite_link = context.bot.export_chat_invite_link(chat_id)
    context.user_data[CHAT_INVITE_LINK] = chat_invite_link
    context.user_data[GROUP_CHAT_ID] = chat_id

    keyboard = [
        [
            InlineKeyboardButton("Change", callback_data=str(Change_time_zone)),
        ],
        [
            InlineKeyboardButton("Back to chat", url=chat_invite_link)
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
        
    reply_text = f"Change time zone\nGroup: {chat_title}\nCurrent time zone:{time_zone}({current_time})"

    user_id = context.user_data.get(USER_ID)
    context.bot.send_message(user_id, text= reply_text, reply_markup=reply_markup, disable_notification=True)

    return 

def time_zone_change_canceled(update: Update, context: CallbackContext):
    chat_id = update.message.chat.id 

    reply_markup_remove = ReplyKeyboardRemove()
    message=context.bot.send_message(chat_id=chat_id, text = '...', reply_markup = reply_markup_remove)
    context.bot.delete_message(chat_id, message.message_id)

    chat_invite_link = context.user_data.get(CHAT_INVITE_LINK)
    keyboard = [
        [
            InlineKeyboardButton("Back to chat", url=chat_invite_link) 
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_title = context.user_data.get(CHAT_TITLE)
    reply_text = f'Change time zone\nGroup: {chat_title}\nStatus: Time zone unchanged'
    context.bot.send_message(text=reply_text, chat_id=chat_id, reply_markup=reply_markup, disable_notification=True)

    return

def time_zone_set_new_location(update: Update, context: CallbackContext):
    user_location = update.message.location
    obj = TimezoneFinder()
    time_zone_str = obj.timezone_at(lng=user_location.longitude, lat=user_location.latitude)
    new_time_zone = pytz.timezone(time_zone_str)
    date_time_now = datetime.datetime.now(new_time_zone)
    current_time = date_time_now.strftime("%d/%m/%Y %H:%M")

    chat_id = update.message.chat.id 
    reply_markup_remove = ReplyKeyboardRemove()
    message=context.bot.send_message(chat_id=chat_id, text = '...', reply_markup=reply_markup_remove, disable_notification=True)
    context.bot.delete_message(chat_id, message.message_id)

    chat_invite_link = context.user_data.get(CHAT_INVITE_LINK)
    keyboard = [
        [
            InlineKeyboardButton("Back to chat", url=chat_invite_link) 
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    chat_title = context.user_data.get(CHAT_TITLE)
    text=f'Change time zone\nGroup: {chat_title}\nNew time zone is {time_zone_str}\nCurrent time: {current_time}\n'
    context.bot.send_message(chat_id=update.message.chat.id, text=text, reply_markup=reply_markup)

    chat_id = context.user_data.get(GROUP_CHAT_ID)
    context.bot_data[chat_id] = time_zone_str
    return

def time_zone_set_new(update: Update, context: CallbackContext):
    user_location = update.message.text
    geolocator = Nominatim(user_agent="supergroups")
    user_location_lower = user_location.lower()
    location = geolocator.geocode(user_location_lower)
    print("Location address:", user_location_lower)

    obj = TimezoneFinder()
    time_zone_str = obj.timezone_at(lng=location.longitude, lat=location.latitude)
    new_time_zone = pytz.timezone(time_zone_str)
    date_time_now = datetime.datetime.now(new_time_zone)
    current_time = date_time_now.strftime("%d/%m/%Y %H:%M")

    chat_id = update.message.chat.id 
    reply_markup_remove = ReplyKeyboardRemove()
    message=context.bot.send_message(chat_id=chat_id, text = '...', reply_markup=reply_markup_remove, disable_notification=True)
    context.bot.delete_message(chat_id, message.message_id)

    chat_invite_link = context.user_data.get(CHAT_INVITE_LINK)
    keyboard = [
        [
            InlineKeyboardButton("Back to chat", url=chat_invite_link) 
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    chat_title = context.user_data.get(CHAT_TITLE)
    text=f'Change time zone\nGroup: {chat_title}\nNew time zone is {time_zone_str}\nCurrent time: {current_time}\n'
    context.bot.send_message(chat_id=update.message.chat.id, text=text, reply_markup=reply_markup)

    chat_id = context.user_data.get(GROUP_CHAT_ID)
    context.bot_data[chat_id] = time_zone_str
    return

"""DELETE MESSAGES"""

def voice_delete_message(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    chat_member = context.bot.get_chat_member(chat_id,user_id)
    chat_member_status = chat_member.status
    must_delete = update.message
    if chat_member_status == ChatMember.CREATOR:
        pass
    else:
        if context.chat_data[VOICE_DELETE_STATUS_ACTIVED] == True:
            context.bot.deleteMessage(chat_id, must_delete.message_id)

            if context.chat_data[VOICE_DELETE_NOTIFICATIONS_ON] == True:
                text = "Voice messages arent allowed"
                context.bot.send_message(chat_id, text, disable_notification=True) 
        else:
            pass
    return

def opening_hours_delete_message(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    chat_member = context.bot.get_chat_member(chat_id,user_id)
    chat_member_status = chat_member.status
    must_delete = update.message

    if chat_member_status == ChatMember.CREATOR:
        pass

    else:
        if len(delete_message_list) != 0 and context.chat_data[OPENING_HOURS_STATUS_OPEN] == True: 
            context.bot.deleteMessage(chat_id, must_delete.message_id)

        elif context.chat_data[OPENING_HOURS_STATUS_OPEN] == False:
            context.bot.deleteMessage(chat_id, must_delete.message_id)
            
        else:
            "dont do nothing"

    return

def main() -> None:

    dispatcher = updater.dispatcher

    dispatcher.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
    dispatcher.add_handler(CommandHandler("start", bot_added_as_admin, Filters.regex(ADD_AS_ADMIN)))
    dispatcher.add_handler(CommandHandler("start", add_bot_as_admin, Filters.regex(ADD_AS_MEMBER)))
    dispatcher.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(

        entry_points = [
            CommandHandler('settings', settings),
            CallbackQueryHandler(time_zone_send_location, pattern='^' + str(Change_time_zone) + '$'),  
            CallbackQueryHandler(settings, pattern = SETTINGS)  
            ],
        states={
            SETTINGS_MENU:[
                MessageHandler(~Filters.command & ~Filters.voice, opening_hours_delete_message),
                MessageHandler(Filters.voice, voice_delete_message),

                CallbackQueryHandler(voice_delete, pattern='^' + str(Voice_message_menu) + '$'),
                CallbackQueryHandler(opening_hours, pattern='^' + str(Opening_hours_menu) + '$'),
                CallbackQueryHandler(time_zone_change, pattern='^' + str(Time_zone_menu) + '$'),
                CallbackQueryHandler(close_setings, pattern='^' + str(Close) + '$'),
            ],
            OPENING_HOURS_MENU:[
                MessageHandler(~Filters.command & ~Filters.voice, opening_hours_delete_message),
                MessageHandler(Filters.voice, voice_delete_message),

                CallbackQueryHandler(time_zone_change, pattern='^' + str(Time_zone_menu) + '$'),

                CallbackQueryHandler(opening_hours, pattern='^' + str(Open) + '$|' + str(Turn_notification_on) + '$|' + str(Turn_notification_off) + '$|'
                + str(Opening_hours_menu) + '$|' + '0' + '$|' + '1' + '$|' + '2' + '$|' + '3' + '$|' + '4' + '$|' + '5' + '$|' + '6' + '$|' + '7' + '$|'
                + '8' + '$|' + '9' + '$|' + '10' + '$|'+ '11' + '$|' + '12' + '$|' + '13' + '$|' + '14' + '$|' + '15' + '$|' + '16' + '$|'+ '17' + '$|'
                + '18' + '$|' + '19' + '$|' + '20' + '$|'+ '21' + '$|' + '22' + '$|' + '23' + '$'),
                CallbackQueryHandler(opening_hours_permanently_closed, pattern='^' + str(Closed) + '$'),
                CallbackQueryHandler(opening_hours_set_time, pattern='^' + str(Set_time) + '$'),
                CallbackQueryHandler(opening_hours_set_week_days, pattern='^' + str(Set_days) + '$'), 

                CallbackQueryHandler(settings, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(close_setings, pattern='^' + str(Close) + '$'), 
            ],           
            SET_DAYS_AND_OPEN_CLOSE_TIME:[
                MessageHandler(~Filters.command & ~Filters.voice, opening_hours_delete_message),
                MessageHandler(Filters.voice, voice_delete_message),

                CallbackQueryHandler(opening_hours, pattern='^' + str(Back) + '$|' + '24h' + '$|' + 'Everyday' + '$|' + 'Weekdays' + '$|' + 'Weekends' + '$'),

                CallbackQueryHandler(opening_hours_set_open_time, pattern='^' + str(Activate) + '$'),
                CallbackQueryHandler(opening_hours_set_closed_time, pattern='^' + '0' + '$|' + '1' + '$|' + '2' + '$|' + '3' + '$|' + '4' + '$|' + '5' + '$|'
                 + '6' + '$|' + '7' + '$|' + '8' + '$|' + '9' + '$|' + '10' + '$|' + '11' + '$|' + '12' + '$|' + '13' + '$|' + '14' + '$|' + '15' + '$|'
                  + '16' + '$|' + '17' + '$|' + '18' + '$|' + '19' + '$|' + '20' + '$|' + '21' + '$|' + '22' + '$|' + '23' + '$'),       
            ], 
            VOICE_MENU:[
                MessageHandler(~Filters.command & ~Filters.voice, opening_hours_delete_message),
                MessageHandler(Filters.voice, voice_delete_message),

                CallbackQueryHandler(time_zone_change, pattern='^' + str(Time_zone_menu) + '$'),

                CallbackQueryHandler(voice_delete, pattern='^' + str(Voice_message_menu) + '$|' + str(Turn_notification_on) + '$|'
                 + str(Turn_notification_off) + '$|' + str(Activate) + '$|' + str(Inactivate) + '$'),

                CallbackQueryHandler(settings, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(close_setings, pattern='^' + str(Close) + '$'),
            ],               
            TIME_ZONE_MENU:[
                MessageHandler(~Filters.command & ~Filters.voice, opening_hours_delete_message),
                MessageHandler(Filters.voice, voice_delete_message),
                
                CallbackQueryHandler(settings, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(time_zone_send_location, pattern='^' + str(Change_time_zone) + '$'),
            ],
            SET_TIME_ZONE:[
                MessageHandler(~Filters.command & ~Filters.voice, opening_hours_delete_message),
                MessageHandler(Filters.voice, voice_delete_message),

                CallbackQueryHandler(time_zone_change, pattern='^' + str(Back) + '$'),
                CallbackQueryHandler(time_zone_change_in_private, pattern='^' + str(Go_private) + '$'),
            ],
            CHANGE_TIME_ZONE_IN_PRIVATE:[
                MessageHandler(Filters.regex('^' + 'Cancel' + '$'), time_zone_change_canceled),
                MessageHandler(Filters.location, time_zone_set_new_location),
                MessageHandler(Filters.text, time_zone_set_new),
            ],        
        },
        fallbacks= [  ],
        per_user=False,
        allow_reentry=True,
        name='my_conversation',
        persistent = True,
    )
  
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()




# AI module using Intellivoid's Coffeehouse API by @TheRealPhoenix
from time import time, sleep

from coffeehouse.lydia import LydiaAI
from coffeehouse.api import API
from coffeehouse.exception import CoffeeHouseError as CFError

from telegram import Message, Chat, User, Update, Bot
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async
from telegram.error import BadRequest, Unauthorized, RetryAfter

from tg_bot import dispatcher, AI_API_KEY, OWNER_ID, SUPPORT_CHAT
import tg_bot.modules.sql.chatbot_sql as sql
from tg_bot.modules.helper_funcs.filters import CustomFilters


CoffeeHouseAPI = API(AI_API_KEY)
api_client = LydiaAI(CoffeeHouseAPI)


@run_async
def add_chat(bot: Bot, update: Update):
    global api_client
    chat_id = update.effective_chat.id
    msg = update.effective_message
    is_chat = sql.is_chat(chat_id)
    if not is_chat:
        ses = api_client.create_session()
        ses_id = str(ses.id)
        expires = str(ses.expires)
        sql.set_ses(chat_id, ses_id, expires)
        msg.reply_text("AI successfully enabled for this chat!")
    else:
        msg.reply_text("AI is already enabled for this chat!")
        
        
@run_async
def remove_chat(bot: Bot, update: Update):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    is_chat = sql.is_chat(chat_id)
    if not is_chat:
        msg.reply_text("AI isn't enabled here in the first place!")
    else:
        sql.rem_chat(chat_id)
        msg.reply_text("AI disabled successfully!")
        
        
def check_message(bot: Bot, message):
    reply_msg = message.reply_to_message
    if message.text.lower() == "saitama":
        return True
    if reply_msg:
        if reply_msg.from_user.id == bot.get_me().id:
            return True
    else:
        return False
                
        
@run_async
def chatbot(bot: Bot, update: Update):
    global api_client
    msg = update.effective_message
    chat_id = update.effective_chat.id
    is_chat = sql.is_chat(chat_id)
    if not is_chat:
        return
    if msg.text and not msg.document:
        if not check_message(bot, msg):
            return
        sesh, exp = sql.get_ses(chat_id)
        query = msg.text
        try:
            if int(exp) < time():
                ses = api_client.create_session()
                ses_id = str(ses.id)
                expires = str(ses.expires)
                sql.set_ses(chat_id, ses_id, expires)
                sesh, exp = sql.get_ses(chat_id)
        except ValueError:
            pass
        try:
            bot.send_chat_action(chat_id, action='typing')
            rep = api_client.think_thought(sesh, query)
            sleep(0.3)
            msg.reply_text(rep, timeout=60)
        except CFError as e:
            bot.send_message(OWNER_ID, f"Chatbot error: {e} occurred in {chat_id}!")
                    
@run_async
def list_chatbot_chats(bot: Bot, update: Update):
    chats = sql.get_all_chats()
    text = "<b>AI-Enabled Chats</b>\n"
    for chat in chats:
        try:
            x = bot.get_chat(int(*chat))
            name = x.title if x.title else x.first_name
            text += f"• <code>{name}</code>\n"
        except BadRequest:
            sql.rem_chat(*chat)
        except Unauthorized:
            sql.rem_chat(*chat)
        except RetryAfter as e:
            sleep(e.retry_after)
    update.effective_message.reply_text(text, parse_mode="HTML")

__mod_name__ = "Chatbot"

__help__ = f"""
Chatbot utilizes the CoffeeHouse API and allows Bot to talk back making your chat more interactive.
This is an ongoing upgrade and is only available in your chats if you reach out to {SUPPORT_CHAT} and ask for it. 
In future we might make it open for any chat and controllable by group admins later .
As Now , We Had Only 100 free sessions Lydia Coffeehouse , so this is Owner Restricted Command
Powered by Lydia 
Commands: These only work My Owner (He can enable auto chat in a group ) 
 - /addchat     : Enables Chatbot mode in the chat.
 - /rmchat      : Disables Chatbot mode in the chat.
 - /listaichats : Lists the chats the chatmode is enabled in.
"""         
                    
                    
ADD_CHAT_HANDLER = CommandHandler("addchat", add_chat, filters=CustomFilters.dev_filter)
REMOVE_CHAT_HANDLER = CommandHandler("rmchat", remove_chat, filters=CustomFilters.dev_filter)
CHATBOT_HANDLER = MessageHandler(Filters.text & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!")
                                  & ~Filters.regex(r"^s\/")), chatbot)
LIST_CB_CHATS_HANDLER = CommandHandler("listaichats", list_chatbot_chats, filters=CustomFilters.dev_filter)
# Filters for ignoring #note messages, !commands and sed.

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(REMOVE_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)
dispatcher.add_handler(LIST_CB_CHATS_HANDLER)
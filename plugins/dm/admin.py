# fileName : plugins/dm/admin.py
# copyright Β©οΈ 2021 nabilanavab

import asyncio
import time, datetime
from pdf import PROCESS
from logger import logger
from configs.config import dm
from configs.db import dataBASE
from pyrogram import filters, enums
from pyrogram import Client as ILovePDF
from pyrogram.errors import (InputUserDeactivated, UserNotParticipant,
                             FloodWait, UserIsBlocked, PeerIdInvalid)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

if dataBASE.MONGODB_URI:
    from database import db

# =======================================> ADMIN MESSAGES <============================================================================================================
@ILovePDF.on_message(filters.command("send") & filters.user(dm.ADMINS) & filters.private & filters.incoming)
async def sand(bot, message):
    try:
        await message.reply_chat_action(enums.ChatAction.TYPING)
        if not message.reply_to_message:
            error = await message.reply("βοΈ `Processing..`", quote=True)
            await asyncio.sleep(1)
            return await error.edit("__please, reply to A messge__ π₯²")
        
        msg = await message.reply_to_message.reply("βοΈ `Processing..`", quote=True)
        await message.delete()
        return await msg.edit(
               text = "βοΈSEND MESSAGE: \n\n`Now, Select any Option Below.. `",
               reply_markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("π’ β BROADCAST β π’", callback_data="nabilanavab")],
                     [InlineKeyboardButton("πΈ COPY πΈ", callback_data="send|copy|broad"),
                      InlineKeyboardButton("πΈ FORWARD πΈ", callback_data="send|forw|broad")],
                     [InlineKeyboardButton("π€ β PM β π€", callback_data="nabilanavab")],
                     [InlineKeyboardButton("πΈ COPY πΈ", callback_data="send|copy|pm"),
                      InlineKeyboardButton("πΈ FORWARD πΈ", callback_data="send|forw|pm")
                    ]]
                ))
    except Exception as error:
        logger.exception("plugins/dm/admin/sand: %s" %(error),exc_info=True)

# =======================================================================================> ADMIN SEMD CALLBACK <=======================================================
send = filters.create(lambda _, __, query: query.data.startswith("send"))
# β MESSAGE BROADCAST β
async def broadcast_messages(user_id, message, info):
    try:
        if info == "copy":
            await message.copy(chat_id=user_id)
            return True, "Success"
        else:
            await message.forward(chat_id=user_id)
            return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message, info)
    except InputUserDeactivated:
        # await db.delete_user(int(user_id))
        return False, "Deleted"
    except UserIsBlocked:
        return False, "Blocked"
    except PeerIdInvalid:
        # await db.delete_user(int(user_id))
        return False, "Error"
    except Exception as e:
        logger.exception("plugins/dm/admin/broadcast_messages: %s" %(e), exc_info=True)
        return False, "Error"
@ILovePDF.on_callback_query(send)
async def _send(bot, callbackQuery):
    try:
        data = callbackQuery.data
        _, __, ___ = callbackQuery.data.split("|")
        
        if ___ == "broad" and not dataBASE.MONGODB_URI:
            return await callbackQuery.answer("Can't Use this feature ={")
        
        await callbackQuery.answer("βοΈ Processing.. ")
        if ___ == "broad":
            users = await db.get_all_users()
            broadcast_msg = callbackQuery.message.reply_to_message
            total_users = await db.total_users_count()
            await callbackQuery.message.edit(
                text = f"βοΈ Started Broadcasting..\nTOTAL {total_users} USERS π\n\nβ MESSAGE β"
                       f"\n`{broadcast_msg.text if broadcast_msg.text else 'π Media π'}`",
                reply_markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(
                        "πΈ asForward πΈ" if __=="forw" else "πΈ asCopy πΈ", callback_data="nabilanavab")
                    ]] 
                ))
            start_time = time.time()
            done = 0; blocked = 0; deleted = 0; failed = 0; success = 0
            
            async for user in users:
                iSuccess, feed = await broadcast_messages(int(user['id']), broadcast_msg, __)
                if iSuccess:
                    success += 1
                elif iSuccess == False:
                    if feed == "Blocked":
                        blocked+=1
                    elif feed == "Deleted":
                        deleted += 1
                    elif feed == "Error":
                        failed += 1
                done += 1
                await asyncio.sleep(1)
                if done % 20 == 0:
                    try:
                        await callbackQuery.message.edit_reply_markup(
                            InlineKeyboardMarkup(
                                [[InlineKeyboardButton(
                                    f"πΈ asForward({done*100}/{total_users}) πΈ" if __=="forw" else f"πΈ asCopy({done*100/total_users}) πΈ",
                                    callback_data = "nabilanavab")
                                ]]
                            ))
                    except: logger.debug("edit error - broadcast")
            time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
            return await callbackQuery.message.edit(
                text = f"`Broadcast Completed:`\n__Completed in__ {time_taken} __seconds β°__\n\n"
                       f"__Total Users:__ {total_users} π\n__Completed:__   {done} / {total_users} π\n"
                       f"__Success:__     {success} β\n__Blocked:__     {blocked} β\n"
                       f"__Deleted:__     {deleted} β°οΈ\n\n",
                reply_markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("πΈ asForward πΈ" if __=="forw" else "πΈ asCopy πΈ",
                        callback_data = "nabilanavab")
                    ]]
                ))
        elif ___ == "pm":
            userID_msg = await bot.ask(
                text = "__Now Send me the traget ID/Username__ π\n\n"
                       "/exit for cancelling current process π€",
                chat_id = callbackQuery.from_user.id,
                reply_to_message_id = callbackQuery.message.id,
                reply_markup = ForceReply(True)
            )
            if not (userID_msg.text) or (userID_msg.text == "/exit"):
                await userID_msg.reply_to_message.delete()
                return await userID_msg.delete()
            
            chat = userID_msg.text
            try:
                chat = int(userID_msg.text)
            except Exception: # if username [Exception]
                pass
            try:
                userINFO = await bot.get_users(chat)
            except Exception as e:
                return await userID_msg.reply(
                    f"__Can't forward message__\n__REASON:__ `{e}`", quote=True
                )
            forward_msg = callbackQuery.message.reply_to_message
            try:
                if __ == "copy":
                    await forward_msg.copy(userINFO.id)
                else:
                    await forward_msg.forward(userINFO.id)
            except Exception:
                return await userID_msg.reply(f"__Can't forward message__\n__REASON:__ `{e}`")
            else:
                return await userID_msg.reply("Successfully forwarded")
        else:
            return
    except Exception as e:
        logger.exception("plugins/dm/admin/_send: %s" %(e), exc_info=True)

# ===================================================================================================================================[NABIL A NAVAB -> TG: nabilanavab]

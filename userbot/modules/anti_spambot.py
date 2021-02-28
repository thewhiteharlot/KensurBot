# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
"""A module for helping ban group join spammers."""

from asyncio import sleep

from requests import get
from telethon.events import ChatAction
from telethon.tl.types import ChannelParticipantsAdmins, Message

from userbot import (
    ANTI_SPAMBOT,
    ANTI_SPAMBOT_SHOUT,
    BOTLOG,
    BOTLOG_CHATID,
    CMD_HELP,
    bot,
)


@bot.on(ChatAction)
async def ANTI_SPAMBOTS(welcm):
    """Ban a recently joined user if it matches the spammer checking algorithm."""
    try:
        if not ANTI_SPAMBOT:
            return
        if welcm.user_joined or welcm.user_added:
            adder = None
            ignore = False
            users = None

            if welcm.user_added:
                ignore = False
                try:
                    adder = welcm.action_message.from_id
                except AttributeError:
                    return

            async for admin in bot.iter_participants(
                welcm.chat_id, filter=ChannelParticipantsAdmins
            ):
                if admin.id == adder:
                    ignore = True
                    break

            if ignore:
                return

            elif welcm.user_joined:
                users_list = hasattr(welcm.action_message.action, "users")
                if users_list:
                    users = welcm.action_message.action.users
                else:
                    users = [welcm.action_message.from_id]

            await sleep(5)
            spambot = False

            if not users:
                return

            for user_id in users:
                async for message in bot.iter_messages(
                    welcm.chat_id, from_user=user_id
                ):

                    correct_type = isinstance(message, Message)
                    if not message or not correct_type:
                        break

                    join_time = welcm.action_message.date
                    message_date = message.date

                    if message_date < join_time:
                        continue  # The message was sent before the user joined, thus ignore it

                    check_user = await welcm.client.get_entity(user_id)

                    # DEBUGGING. LEAVING IT HERE FOR SOME TIME ###
                    print(
                        f"Usuário registrado: {check_user.first_name} [ID: {check_user.id}]"
                    )
                    print(f"Chat: {welcm.chat.title}")
                    print(f"Horário: {join_time}")
                    print(
                        f"Mensagem enviada: {message.text}\n\n[Horário: {message_date}]"
                    )
                    ##############################################

                    try:
                        # https://t.me/combotnews/283
                        cas_url = f"https://api.cas.chat/check?user_id={check_user.id}"
                        r = get(cas_url, timeout=3)
                        data = r.json()
                    except BaseException:
                        print(
                            "Falha na verificação de CAS, voltando ao comportamento anti_spambot legado."
                        )
                        data = None

                    if data and data["ok"]:
                        reason = f"[Banido por Combot Anti Spam](https://cas.chat/query?u={check_user.id})"
                        spambot = True
                    elif "t.cn/" in message.text:
                        reason = "Corresponde em `t.cn` URLs"
                        spambot = True
                    elif "t.me/joinchat" in message.text:
                        reason = "Mensagem de promoção em potencial"
                        spambot = True
                    elif message.fwd_from:
                        reason = "Mensagem encaminhada"
                        spambot = True
                    elif "?start=" in message.text:
                        reason = "Telegram bot `start` link"
                        spambot = True
                    elif "bit.ly/" in message.text:
                        reason = "Corresponde em `bit.ly` URLs"
                        spambot = True
                    else:
                        if check_user.first_name in (
                            "Bitmex",
                            "Promotion",
                            "Information",
                            "Dex",
                            "Announcements",
                            "Info",
                        ):
                            if users.last_name == "Bot":
                                reason = "Spambot conhecido"
                                spambot = True

                    if spambot:
                        print(f"Possível mensagem de spam: {message.text}")
                        await message.delete()
                        break

                    continue  # Check the next messsage

            if spambot:
                chat = await welcm.get_chat()
                admin = chat.admin_rights
                creator = chat.creator
                if not admin and not creator:
                    if ANTI_SPAMBOT_SHOUT:
                        await welcm.reply(
                            "@admins\n"
                            "`ANTI SPAMBOT DETECTOR!\n"
                            "ESTE USUÁRIO CORRESPONDE A MEUS ALGORITMOS COMO UM SPAMBOT!`"
                            f"RAZÃO: {reason}"
                        )
                        kicked = False
                        reported = True
                else:
                    try:

                        await welcm.reply(
                            "`Potencial Spambot Detectado !!`\n"
                            f"`RAZÃO:` {reason}\n"
                            "Expulsando por agora, registrarei a ID caso necessário.\n"
                            f"`USUÁRIO:` [{check_user.first_name}](tg://user?id={check_user.id})"
                        )

                        await welcm.client.kick_participant(
                            welcm.chat_id, check_user.id
                        )
                        kicked = True
                        reported = False

                    except BaseException:
                        if ANTI_SPAMBOT_SHOUT:
                            await welcm.reply(
                                "@admins\n"
                                "`ANTI SPAMBOT DETECTOR!\n"
                                "ESTE USUÁRIO CORRESPONDE A MEUS ALGORITMOS COMO UM SPAMBOT!`"
                                f"RAZÃO: {reason}"
                            )
                            kicked = False
                            reported = True

                if BOTLOG:
                    if kicked or reported:
                        await welcm.client.send_message(
                            BOTLOG_CHATID,
                            "#ANTI_SPAMBOT REPORT\n"
                            f"USUÁRIO: [{check_user.first_name}](tg://user?id={check_user.id})\n"
                            f"USUÁRIO ID: `{check_user.id}`\n"
                            f"CHAT: {welcm.chat.title}\n"
                            f"CHAT ID: `{welcm.chat_id}`\n"
                            f"RAZÃO: {reason}\n"
                            f"MENSAGEM:\n\n{message.text}",
                        )
    except ValueError:
        pass


CMD_HELP.update(
    {
        "anti_spambot": "Se habilitado em config.env ou env var,\
        \neste módulo irá banir (ou informar os administradores do grupo sobre) o\
        \nspammer(s) se eles corresponderem ao algoritmo anti-spam do userbot."
    }
)

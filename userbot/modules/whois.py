# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
# The entire source code is OSSRPL except 'whois' which is MPL
# License: MPL and OSSRPL
""" Userbot module for getiing info about any user on Telegram(including you!). """

import os

from telethon.tl.functions.photos import GetUserPhotosRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityMentionName
from telethon.utils import get_input_location

from userbot import CMD_HELP, TEMP_DOWNLOAD_DIRECTORY
from userbot.events import register


@register(pattern=".whois(?: |$)(.*)", outgoing=True)
async def who(event):

    await event.edit(
        "`Espere enquanto eu roubo alguns dados da *Zona de Rede Global*...`"
    )

    if not os.path.isdir(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)

    replied_user = await get_user(event)
    if replied_user is None:
        await event.edit(
            "`Este é um administrador anônimo neste grupo.\nNão consigo obter a informação`"
        )
        return

    try:
        photo, caption = await fetch_info(replied_user, event)
    except AttributeError:
        await event.edit("`Não foi possível buscar as informações desse usuário.`")
        return

    message_id_to_reply = event.message.reply_to_msg_id

    if not message_id_to_reply:
        message_id_to_reply = None

    try:
        await event.client.send_file(
            event.chat_id,
            photo,
            caption=caption,
            link_preview=False,
            force_document=False,
            reply_to=message_id_to_reply,
            parse_mode="html",
        )

        if not photo.startswith("http"):
            os.remove(photo)
        await event.delete()

    except TypeError:
        await event.edit(caption, parse_mode="html")


async def get_user(event):
    """ Get the user from argument or replied message. """
    if event.reply_to_msg_id and not event.pattern_match.group(1):
        previous_message = await event.get_reply_message()
        if previous_message.from_id is None:  # Anonymous admin seems don't have id attr
            return None
        replied_user = await event.client(GetFullUserRequest(previous_message.from_id))
    else:
        user = event.pattern_match.group(1)

        if user.isnumeric():
            user = int(user)

        if not user:
            self_user = await event.client.get_me()
            user = self_user.id

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                replied_user = await event.client(GetFullUserRequest(user_id))
                return replied_user
        try:
            user_object = await event.client.get_entity(user)
            replied_user = await event.client(GetFullUserRequest(user_object.id))
        except (TypeError, ValueError) as err:
            await event.edit(str(err))
            return None

    return replied_user


async def fetch_info(replied_user, event):
    """ Get details from the User object. """
    replied_user_profile_photos = await event.client(
        GetUserPhotosRequest(
            user_id=replied_user.user.id, offset=42, max_id=0, limit=80
        )
    )
    replied_user_profile_photos_count = (
        "A pessoa precisa de ajuda para enviar a foto do perfil."
    )
    try:
        replied_user_profile_photos_count = replied_user_profile_photos.count
    except AttributeError:
        pass
    user_id = replied_user.user.id
    first_name = replied_user.user.first_name
    last_name = replied_user.user.last_name
    try:
        dc_id, location = get_input_location(replied_user.profile_photo)
    except Exception as e:
        dc_id = "Não foi possível buscar DC ID!"
        str(e)
    common_chat = replied_user.common_chats_count
    username = replied_user.user.username
    user_bio = replied_user.about
    is_bot = replied_user.user.bot
    restricted = replied_user.user.restricted
    verified = replied_user.user.verified
    photo = await event.client.download_profile_photo(
        user_id, TEMP_DOWNLOAD_DIRECTORY + str(user_id) + ".jpg", download_big=True
    )
    first_name = (
        first_name.replace("\u2060", "")
        if first_name
        else ("Este usuário não tem primeiro nome")
    )
    last_name = (
        last_name.replace("\u2060", "")
        if last_name
        else ("Este usuário não tem sobrenome")
    )
    username = (
        "@{}".format(username) if username else ("Este usuário não tem nome de usuário")
    )
    user_bio = "Este usuário não tem Sobre" if not user_bio else user_bio

    caption = "<b>INFORMAÇÃO DE USUÁRIO:</b>\n\n"
    caption += f"🗣 Primeiro nome: {first_name}\n"
    caption += f"🗣 Último nome: {last_name}\n"
    caption += f"👤 Nome do usuário: {username}\n"
    caption += f"🏢 Data Centre ID: {dc_id}\n"
    caption += f"🖼 Número de fotos do perfil: {replied_user_profile_photos_count}\n"
    caption += f"🤖 É bot: {is_bot}\n"
    caption += f"🚫 É restrito: {restricted}\n"
    caption += f"✅ É verificado pelo Telegram: {verified}\n"
    caption += f"🕵 ID: <code>{user_id}</code>\n\n"
    caption += f"📝 Bio: \n<code>{user_bio}</code>\n\n"
    caption += f"👥 Bate-papos comuns com este usuário: {common_chat}\n"
    caption += f"🔗 Link permanente de perfil: "
    caption += f'<a href="tg://user?id={user_id}">{first_name}</a>'

    return photo, caption


CMD_HELP.update(
    {
        "whois": ".whois <nome de usuário> ou responda ao texto de alguém com .whois\
         \nUso: Obtém informações de um usuário."
    }
)

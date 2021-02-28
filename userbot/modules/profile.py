# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for changing your Telegram profile details. """

import os

from telethon.errors import ImageProcessFailedError, PhotoCropSizeSmallError
from telethon.errors.rpcerrorlist import PhotoExtInvalidError, UsernameOccupiedError
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.functions.channels import GetAdminedPublicChannelsRequest
from telethon.tl.functions.photos import (
    DeletePhotosRequest,
    GetUserPhotosRequest,
    UploadProfilePhotoRequest,
)
from telethon.tl.types import Channel, Chat, InputPhoto, MessageMediaPhoto, User

from userbot import CMD_HELP, bot
from userbot.events import register

# ====================== CONSTANT ===============================
INVALID_MEDIA = "```A extensão da mídia é inválida.```"
PP_CHANGED = "```Foto de perfil atualizada com sucesso.```"
PP_TOO_SMOL = "```Essa imagem é muito pequena, use uma imagem maior.```"
PP_ERROR = "```Uma falha ocorreu enquanto a imagem era processada.```"

BIO_SUCCESS = "```Bio editada com sucesso.```"

NAME_OK = "```Seu nome foi trocado com sucesso.```"
USERNAME_SUCCESS = "```Seu nome de usuário foi trocado com sucesso.```"
USERNAME_TAKEN = "```Esse nome de usuário já existe.```"
# ===============================================================


@register(outgoing=True, pattern="^.reserved$")
async def mine(event):
    """ Para o comando .reserved , gera uma lista de seus nomes de usuário reservados. """
    result = await bot(GetAdminedPublicChannelsRequest())
    output_str = ""
    for channel_obj in result.chats:
        output_str += f"{channel_obj.title}\n@{channel_obj.username}\n\n"
    await event.edit(output_str)


@register(outgoing=True, pattern="^.name")
async def update_name(name):
    """ Para o comando .name , muda seu nome no Telegram. """
    newname = name.text[6:]
    if " " not in newname:
        firstname = newname
        lastname = ""
    else:
        namesplit = newname.split(" ", 1)
        firstname = namesplit[0]
        lastname = namesplit[1]

    await name.client(UpdateProfileRequest(first_name=firstname, last_name=lastname))
    await name.edit(NAME_OK)


@register(outgoing=True, pattern="^.setpfp$")
async def set_profilepic(propic):
    """ Parao comando .profilepic , muda sua foto de perfil no Telegram. """
    await propic.edit("`Processando...`")
    replymsg = await propic.get_reply_message()
    photo = None
    if replymsg.media:
        if isinstance(replymsg.media, MessageMediaPhoto):
            photo = await propic.client.download_media(message=replymsg.photo)
        elif "image" in replymsg.media.document.mime_type.split("/"):
            photo = await propic.client.download_file(replymsg.media.document)
        else:
            await propic.edit(INVALID_MEDIA)

    if photo:
        try:
            await propic.client(
                UploadProfilePhotoRequest(await propic.client.upload_file(photo))
            )
            os.remove(photo)
            await propic.edit(PP_CHANGED)
        except PhotoCropSizeSmallError:
            await propic.edit(PP_TOO_SMOL)
        except ImageProcessFailedError:
            await propic.edit(PP_ERROR)
        except PhotoExtInvalidError:
            await propic.edit(INVALID_MEDIA)


@register(outgoing=True, pattern="^.setbio (.*)")
async def set_biograph(setbio):
    """ Para o comando .setbio , define sua bio no Telegram. """
    await setbio.edit("`Processando...`")
    newbio = setbio.pattern_match.group(1)
    await setbio.client(UpdateProfileRequest(about=newbio))
    await setbio.edit(BIO_SUCCESS)


@register(outgoing=True, pattern="^.username (.*)")
async def update_username(username):
    """ Para o comando .username , define um novo nome de usuário no Telegram. """
    await username.edit("`Processando...`")
    newusername = username.pattern_match.group(1)
    try:
        await username.client(UpdateUsernameRequest(newusername))
        await username.edit(USERNAME_SUCCESS)
    except UsernameOccupiedError:
        await username.edit(USERNAME_TAKEN)


@register(outgoing=True, pattern="^.count$")
async def count(event):
    """ Para o comando .count , gera status do perfil. """
    u = 0
    g = 0
    c = 0
    bc = 0
    b = 0
    result = ""
    await event.edit("`Processando...`")
    dialogs = await bot.get_dialogs(limit=None, ignore_migrated=True)
    for d in dialogs:
        currrent_entity = d.entity
        if isinstance(currrent_entity, User):
            if currrent_entity.bot:
                b += 1
            else:
                u += 1
        elif isinstance(currrent_entity, Chat):
            g += 1
        elif isinstance(currrent_entity, Channel):
            if currrent_entity.broadcast:
                bc += 1
            else:
                c += 1
        else:
            print(d)

    result += f"`Users:`\t**{u}**\n"
    result += f"`Groups:`\t**{g}**\n"
    result += f"`Super Groups:`\t**{c}**\n"
    result += f"`Channels:`\t**{bc}**\n"
    result += f"`Bots:`\t**{b}**"

    await event.edit(result)


@register(outgoing=True, pattern=r"^.delpfp")
async def remove_profilepic(delpfp):
    """ Para o comando .delpfp , deleta sua foto atual de perfil no Telegram. """
    await delpfp.edit("`Processando...`")
    group = delpfp.text[8:]
    if group == "all":
        lim = 0
    elif group.isdigit():
        lim = int(group)
    else:
        lim = 1

    pfplist = await delpfp.client(
        GetUserPhotosRequest(user_id=delpfp.from_id, offset=0, max_id=0, limit=lim)
    )
    input_photos = []
    for sep in pfplist.photos:
        input_photos.append(
            InputPhoto(
                id=sep.id,
                access_hash=sep.access_hash,
                file_reference=sep.file_reference,
            )
        )
    await delpfp.client(DeletePhotosRequest(id=input_photos))
    await delpfp.edit(f"`Successfully deleted {len(input_photos)} profile picture(s).`")


CMD_HELP.update(
    {
        "profile": ".username <novo_nome_de_usuário>\
\nUso: Muda seu nome de usuário.\
\n\n.name <primeiro_nome> ou .name <primeironome> <últimonome>\
\nUso: Muda seu nome no Telegram.(Primeiro e último nome serão separados pelo espaço)\
\n\n.setpfp\
\nUso: Dê reply com .setpfp em uma imagem para definir como foto de perfil.\
\n\n.setbio <nova_bio>\
\nUso: Muda sua bio no Telegram.\
\n\n.delpfp or .delpfp <numero>/<all>\
\nUso: Deleta foto(s) de perfil no Telegram.\
\n\n.reserved\
\nUso: Mostra nomes de usuário reservados por você.\
\n\n.count\
\nUso: Conta seus grupos, chats, bots etc..."
    }
)

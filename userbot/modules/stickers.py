# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for kanging stickers or making new ones. Thanks @rupansh"""

import io
import math
import random
import urllib.request
from os import remove

from PIL import Image
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import (
    DocumentAttributeFilename,
    DocumentAttributeSticker,
    InputStickerSetID,
    MessageMediaPhoto,
)

from userbot import CMD_HELP, bot
from userbot.events import register

KANGING_STR = [
    "Usando alquimia para clonar esse sticker...",
    "Pegando isso aqui emprestado...",
    "Convidando esse sticker pro meu pack...",
    "Hey, lindo sticker!\nSe importa se eu roubar?!..",
    "hehe achado não é roubado\nquem perdeu foi relaxado.",
    "Ay olha aquilo ali (☉｡☉)!→\nEnquanto eu pego isso aqui...",
    "Enviando sticker para meu banco de dados.",
    "Simsalabim, passe esse sticker para mim.",
    "Sticker capturado com sucesso...",
    "Sr. RoubaSticker roubando seu sticker... ",
]


@register(outgoing=True, pattern="^.kang")
async def kang(args):
    """ For .kang command, kangs stickers or creates new ones. """
    user = await bot.get_me()
    if not user.username:
        user.username = user.first_name
    message = await args.get_reply_message()
    photo = None
    emojibypass = False
    is_anim = False
    emoji = None

    if message and message.media:
        if isinstance(message.media, MessageMediaPhoto):
            await args.edit(f"`{random.choice(KANGING_STR)}`")
            photo = io.BytesIO()
            photo = await bot.download_media(message.photo, photo)
        elif "image" in message.media.document.mime_type.split("/"):
            await args.edit(f"`{random.choice(KANGING_STR)}`")
            photo = io.BytesIO()
            await bot.download_file(message.media.document, photo)
            if (
                DocumentAttributeFilename(file_name="sticker.webp")
                in message.media.document.attributes
            ):
                emoji = message.media.document.attributes[1].alt
                if emoji != "":
                    emojibypass = True
        elif "tgsticker" in message.media.document.mime_type:
            await args.edit(f"`{random.choice(KANGING_STR)}`")
            await bot.download_file(message.media.document, "AnimatedSticker.tgs")

            attributes = message.media.document.attributes
            for attribute in attributes:
                if isinstance(attribute, DocumentAttributeSticker):
                    emoji = attribute.alt

            emojibypass = True
            is_anim = True
            photo = 1
        else:
            await args.edit("`Arquivo não suportado!`")
            return
    else:
        await args.edit("`Não posso roubar isso...`")
        return

    if photo:
        splat = args.text.split()
        if not emojibypass:
            emoji = "🤔"
        pack = 1
        if len(splat) == 3:
            pack = splat[2]  # User sent both
            emoji = splat[1]
        elif len(splat) == 2:
            if splat[1].isnumeric():
                # User wants to push into different pack, but is okay with
                # thonk as emote.
                pack = int(splat[1])
            else:
                # User sent just custom emote, wants to push to default
                # pack
                emoji = splat[1]

        packname = f"a{user.id}_by_{user.username}_{pack}"
        packnick = f"@{user.username} kang library Book.{pack}"
        cmd = "/newpack"
        file = io.BytesIO()

        if not is_anim:
            image = await resize_photo(photo)
            file.name = "sticker.png"
            image.save(file, "PNG")
        else:
            packname += "_anim"
            packnick += " (Animated)"
            cmd = "/newanimated"

        response = urllib.request.urlopen(
            urllib.request.Request(f"http://t.me/addstickers/{packname}")
        )
        htmlstr = response.read().decode("utf8").split("\n")

        if (
            "  A <strong>Telegram</strong> user has created the <strong>Sticker&nbsp;Set</strong>."
            not in htmlstr
        ):
            async with bot.conversation("Stickers") as conv:
                await conv.send_message("/addsticker")
                await conv.get_response()
                # Ensure user doesn't get spamming notifications
                await bot.send_read_acknowledge(conv.chat_id)
                await conv.send_message(packname)
                x = await conv.get_response()
                while "120" in x.text:
                    pack += 1
                    packname = f"a{user.id}_by_{user.username}_{pack}"
                    packnick = f"@{user.username} kang library Book.{pack}"
                    await args.edit(
                        "`Trocando para pacote "
                        + str(pack)
                        + " devido a espaço insuficiente`"
                    )
                    await conv.send_message(packname)
                    x = await conv.get_response()
                    if x.text == "Pack inválido selecionado.":
                        await conv.send_message(cmd)
                        await conv.get_response()
                        # Ensure user doesn't get spamming notifications
                        await bot.send_read_acknowledge(conv.chat_id)
                        await conv.send_message(packnick)
                        await conv.get_response()
                        # Ensure user doesn't get spamming notifications
                        await bot.send_read_acknowledge(conv.chat_id)
                        if is_anim:
                            await conv.send_file("AnimatedSticker.tgs")
                            remove("AnimatedSticker.tgs")
                        else:
                            file.seek(0)
                            await conv.send_file(file, force_document=True)
                        await conv.get_response()
                        await conv.send_message(emoji)
                        # Ensure user doesn't get spamming notifications
                        await bot.send_read_acknowledge(conv.chat_id)
                        await conv.get_response()
                        await conv.send_message("/publish")
                        if is_anim:
                            await conv.get_response()
                            await conv.send_message(f"<{packnick}>")
                        # Ensure user doesn't get spamming notifications
                        await conv.get_response()
                        await bot.send_read_acknowledge(conv.chat_id)
                        await conv.send_message("/skip")
                        # Ensure user doesn't get spamming notifications
                        await bot.send_read_acknowledge(conv.chat_id)
                        await conv.get_response()
                        await conv.send_message(packname)
                        # Ensure user doesn't get spamming notifications
                        await bot.send_read_acknowledge(conv.chat_id)
                        await conv.get_response()
                        # Ensure user doesn't get spamming notifications
                        await bot.send_read_acknowledge(conv.chat_id)
                        await args.edit(
                            f"`Sticker adicionado a um pacote diferente !\
                            \nEsse pacote foi criado recentemente!\
                            \nSeu pacote pode ser achado [aqui](t.me/addstickers/{packname})",
                            parse_mode="md",
                        )
                        return
                if is_anim:
                    await conv.send_file("AnimatedSticker.tgs")
                    remove("AnimatedSticker.tgs")
                else:
                    file.seek(0)
                    await conv.send_file(file, force_document=True)
                rsp = await conv.get_response()
                if "Desculpe, o tipo de arquivo é inválido." in rsp.text:
                    await args.edit(
                        "`Falha ao adicionar adesivo, use` @Stickers `bot para adicionar o adesivo manualmente.`"
                    )
                    return
                await conv.send_message(emoji)
                # Ensure user doesn't get spamming notifications
                await bot.send_read_acknowledge(conv.chat_id)
                await conv.get_response()
                await conv.send_message("/done")
                await conv.get_response()
                # Ensure user doesn't get spamming notifications
                await bot.send_read_acknowledge(conv.chat_id)
        else:
            await args.edit("`Preparando um novo pacote...`")
            async with bot.conversation("Stickers") as conv:
                await conv.send_message(cmd)
                await conv.get_response()
                # Ensure user doesn't get spamming notifications
                await bot.send_read_acknowledge(conv.chat_id)
                await conv.send_message(packnick)
                await conv.get_response()
                # Ensure user doesn't get spamming notifications
                await bot.send_read_acknowledge(conv.chat_id)
                if is_anim:
                    await conv.send_file("AnimatedSticker.tgs")
                    remove("AnimatedSticker.tgs")
                else:
                    file.seek(0)
                    await conv.send_file(file, force_document=True)
                rsp = await conv.get_response()
                if "Desculpe, o tipo de arquivo é inválido." in rsp.text:
                    await args.edit(
                        "`Falha ao adicionar adesivo, use` @Stickers `bot para adicionar o adesivo manualmente.`"
                    )
                    return
                await conv.send_message(emoji)
                # Ensure user doesn't get spamming notifications
                await bot.send_read_acknowledge(conv.chat_id)
                await conv.get_response()
                await conv.send_message("/publish")
                if is_anim:
                    await conv.get_response()
                    await conv.send_message(f"<{packnick}>")
                # Ensure user doesn't get spamming notifications
                await conv.get_response()
                await bot.send_read_acknowledge(conv.chat_id)
                await conv.send_message("/skip")
                # Ensure user doesn't get spamming notifications
                await bot.send_read_acknowledge(conv.chat_id)
                await conv.get_response()
                await conv.send_message(packname)
                # Ensure user doesn't get spamming notifications
                await bot.send_read_acknowledge(conv.chat_id)
                await conv.get_response()
                # Ensure user doesn't get spamming notifications
                await bot.send_read_acknowledge(conv.chat_id)

        await args.edit(
            f"`Sticker roubado com sucesso!`\
            \nPacote pode ser achado [aqui](t.me/addstickers/{packname})",
            parse_mode="md",
        )


async def resize_photo(photo):
    """ Resize the given photo to 512x512 """
    image = Image.open(photo)
    maxsize = (512, 512)
    if (image.width and image.height) < 512:
        size1 = image.width
        size2 = image.height
        if image.width > image.height:
            scale = 512 / size1
            size1new = 512
            size2new = size2 * scale
        else:
            scale = 512 / size2
            size1new = size1 * scale
            size2new = 512
        size1new = math.floor(size1new)
        size2new = math.floor(size2new)
        sizenew = (size1new, size2new)
        image = image.resize(sizenew)
    else:
        image.thumbnail(maxsize)

    return image


@register(outgoing=True, pattern="^.stkrinfo$")
async def get_pack_info(event):
    if not event.is_reply:
        await event.edit("`Não consigo obter informações do nada, posso ?!`")
        return

    rep_msg = await event.get_reply_message()
    if not rep_msg.document:
        await event.edit("`Responda a um adesivo para obter os detalhes do pacote`")
        return

    try:
        stickerset_attr = rep_msg.document.attributes[1]
        await event.edit("`Buscando detalhes do pacote de adesivos, aguarde..`")
    except BaseException:
        await event.edit("`Isso não é um sticker. Responda em um adesivo.`")
        return

    if not isinstance(stickerset_attr, DocumentAttributeSticker):
        await event.edit("`Isso não é um sticker. Responda em um adesivo.`")
        return

    get_stickerset = await bot(
        GetStickerSetRequest(
            InputStickerSetID(
                id=stickerset_attr.stickerset.id,
                access_hash=stickerset_attr.stickerset.access_hash,
            )
        )
    )
    pack_emojis = []
    for document_sticker in get_stickerset.packs:
        if document_sticker.emoticon not in pack_emojis:
            pack_emojis.append(document_sticker.emoticon)

    OUTPUT = (
        f"**Sticker Title:** `{get_stickerset.set.title}\n`"
        f"**Sticker Short Name:** `{get_stickerset.set.short_name}`\n"
        f"**Official:** `{get_stickerset.set.official}`\n"
        f"**Archived:** `{get_stickerset.set.archived}`\n"
        f"**Stickers In Pack:** `{len(get_stickerset.packs)}`\n"
        f"**Emojis In Pack:**\n{' '.join(pack_emojis)}"
    )

    await event.edit(OUTPUT)


@register(outgoing=True, pattern="^.getsticker$")
async def sticker_to_png(sticker):
    if not sticker.is_reply:
        await sticker.edit("`Sem informações para adquirir...`")
        return False

    img = await sticker.get_reply_message()
    if not img.document:
        await sticker.edit("`Responda em um adesivo...`")
        return False

    try:
        img.document.attributes[1]
    except Exception:
        await sticker.edit("`Isto não é um adesivo...`")
        return

    with io.BytesIO() as image:
        await sticker.client.download_media(img, image)
        image.name = "sticker.png"
        image.seek(0)
        try:
            await img.reply(file=image, force_document=True)
        except Exception:
            await sticker.edit("`Erro, não é possível enviar arquivo...`")
        else:
            await sticker.delete()
    return


CMD_HELP.update(
    {
        "stickers": ".kang\
\nUso: Responda .kang a um adesivo ou imagem para colocá-lo em seu pacote de userbot.\
\n\n.kang [emoji('s)]\
\nUso: Funciona como .kang, mas usa os emoji(s) que você escolheu.\
\n\n.kang [número]\
\nUso: Rouba o adesivo/imagem para o pacote especificado, mas usa 🤔 como emoji.\
\n\n.kang [emoji('s)] [número]\
\nUso: Rouba o adesivo/imagem para o pacote especificado e usa os emoji(s) que você escolheu.\
\n\n.stkrinfo\
\nUso: Obtém informações sobre o pacote de adesivos.\
\n\n.getsticker\
\nUso: Responda a um adesivo para obter o arquivo 'PNG' do adesivo."
    }
)

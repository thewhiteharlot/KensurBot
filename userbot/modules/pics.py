# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
# Copyright (C) 2020-2069 The authorship

from asyncio import sleep
from io import BytesIO

from telethon import types
from telethon.errors import PhotoInvalidDimensionsError
from telethon.tl.functions.messages import SendMediaRequest

from userbot import CMD_HELP
from userbot.events import register


@register(outgoing=True, pattern=r"^\.pic(?: |$)(.*)")
async def on_file_to_photo(pics):
    await pics.edit(
        "Convertendo a imagem do documento em imagem em tamanho real\nAguarde..."
    )
    await sleep(1.5)
    await pics.delete()
    target = await pics.get_reply_message()
    try:
        image = target.media.document
    except AttributeError:
        return
    if not image.mime_type.startswith("image/"):
        return  # This isn't an image
    if image.mime_type == "image/webp":
        return  # Telegram doesn't let you directly send stickers as photos
    if image.size > 10 * 2560 * 1440:
        return  # We'd get PhotoSaveFileInvalidError otherwise

    file = await pics.client.download_media(target, file=BytesIO())
    file.seek(0)
    img = await pics.client.upload_file(file)
    img.name = "image.png"

    try:
        await pics.client(
            SendMediaRequest(
                peer=await pics.get_input_chat(),
                media=types.InputMediaUploadedPhoto(img),
                message=target.message,
                entities=target.entities,
                reply_to_msg_id=target.id,
            )
        )
    except PhotoInvalidDimensionsError:
        return


CMD_HELP.update(
    {
        "pics": ".pic <resposta a qualquer imagem de documento> \
        \nUso: Converta qualquer imagem de documento em imagem em tamanho real."
    }
)

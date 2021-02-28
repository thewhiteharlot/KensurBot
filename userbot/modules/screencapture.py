# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
# The entire source code is OSSRPL except 'screencapture' which is MPL
# License: MPL and OSSRPL

import io
from asyncio import sleep
from re import match

from userbot import CMD_HELP
from userbot.events import register
from userbot.utils import chrome, options


@register(pattern=r"^\.ss (.*)", outgoing=True)
async def capture(url):
    """ For .ss command, capture a website's screenshot and send the photo. """
    await url.edit("**Processando...**")
    chrome_options = await options()
    chrome_options.add_argument("--test-type")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.arguments.remove("--window-size=1920x1080")
    driver = await chrome(chrome_options=chrome_options)
    input_str = url.pattern_match.group(1)
    link_match = match(r"\bhttps?://.*\.\S+", input_str)
    if link_match:
        link = link_match.group()
    else:
        return await url.edit("**Preciso de um link válido para capturar a tela.**")
    driver.get(link)
    height = driver.execute_script(
        "return Math.max(document.body.scrollHeight, document.body.offsetHeight, "
        "document.documentElement.clientHeight, document.documentElement.scrollHeight, "
        "document.documentElement.offsetHeight);"
    )
    width = driver.execute_script(
        "return Math.max(document.body.scrollWidth, document.body.offsetWidth, "
        "document.documentElement.clientWidth, document.documentElement.scrollWidth, "
        "document.documentElement.offsetWidth);"
    )
    driver.set_window_size(width + 125, height + 125)
    wait_for = height / 1000
    await url.edit(
        "**Gerando captura de tela da página...**"
        f"\nAltura da página = {height}px"
        f"\nLargura da página = {width}px"
        f"\nAguardando ({int(wait_for)}s) para a página carregar."
    )
    await sleep(int(wait_for))
    im_png = driver.get_screenshot_as_png()
    # saves screenshot of entire page
    driver.quit()
    message_id = url.message.id
    if url.reply_to_msg_id:
        message_id = url.reply_to_msg_id
    with io.BytesIO(im_png) as out_file:
        out_file.name = "screencapture.png"
        await url.edit("**Carregando a captura de tela como arquivo...**")
        await url.client.send_file(
            url.chat_id,
            out_file,
            caption=input_str,
            force_document=True,
            reply_to=message_id,
        )


CMD_HELP.update(
    {
        "ss": ">`.ss <url>`"
        "\nUso: Tira uma captura de tela de um site e a envia."
        "\nExemplo de um URL válido : `https://www.google.com`"
    }
)

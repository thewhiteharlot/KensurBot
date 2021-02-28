# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
# You can find misc modules, which dont fit in anything xD
""" Userbot module for other small commands. """

import io
import sys
from os import execl
from random import randint
from time import sleep

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP, bot
from userbot.events import register
from userbot.utils import time_formatter


@register(outgoing=True, pattern="^.random")
async def randomise(items):
    """ For .random command, get a random item from the list of items. """
    itemo = (items.text[8:]).split()
    if len(itemo) < 2:
        await items.edit(
            "`2 itens ou mais são necessários! Use .help random para mais informações.`"
        )
        return
    index = randint(1, len(itemo) - 1)
    await items.edit(
        "**Pesquisa: **\n`"
        + items.text[8:]
        + "`\n**Resultado: **\n`"
        + itemo[index]
        + "`"
    )


@register(outgoing=True, pattern="^.sleep ([0-9]+)$")
async def sleepybot(time):
    """ Para o comando .sleep, deixe o userbot dormir por alguns segundos. """
    counter = int(time.pattern_match.group(1))
    await time.edit("`Estou de mau humor e cochilando.....`")
    if BOTLOG:
        str_counter = time_formatter(counter)
        await time.client.send_message(
            BOTLOG_CHATID,
            f"Você colocou o bot para dormir por {str_counter}.",
        )
    sleep(counter)
    await time.edit("`OK, estou acordado agora.`")


@register(outgoing=True, pattern="^.shutdown$")
async def killbot(shut):
    """Para o comando .shutdown, desliga o bot."""
    await shut.edit("`Adeus *barulho de desligamento do Windows XP*....`")
    if BOTLOG:
        await shut.client.send_message(BOTLOG_CHATID, "#SHUTDOWN \n" "Bot desligado")
    await bot.disconnect()


@register(outgoing=True, pattern="^.restart$")
async def killdabot(reboot):
    await reboot.edit("`*eu estarei de volta em um momento*`")
    if BOTLOG:
        await reboot.client.send_message(BOTLOG_CHATID, "#RESTART \n" "Bot reiniciado")
    await bot.disconnect()
    # Spin a new instance of bot
    execl(sys.executable, sys.executable, *sys.argv)
    # Shut the existing one down
    exit()


@register(outgoing=True, pattern="^.readme$")
async def reedme(event):
    await event.edit(
        "Aqui estão alguns tutoriais interessantes:\n"
        "\n[Arquivo Readme do PurpleBot](https://github.com/thewhiteharlot/PurpleBot/blob/sql-extended/README.md)"
        "\n[Guia de configuração - Bot](https://www.youtube.com/watch?v=SBYjQ25ugZY&feature=emb_title&ab_channel=TUDOSEMCORTE) - Créditos: @mandaloriam"
        "\n[Guia de configuração - Google Drive](https://www.youtube.com/watch?v=Z0WFtwDMnes&ab_channel=TUDOSEMCORTE) - Créditos: @ramonazvd"
        "\n[Guia de configuração - LastFM](https://telegra.ph/Tutorial-LastFM-02-04-2)"
        "\n[Replit para gerar a String Session](https://repl.it/@kenhv/sessiongen)"
        "\n__*Após entrar no Replit, clique no botão verde para executar__"
    )


# Copyright (c) Gegham Zakaryan | 2019
@register(outgoing=True, pattern="^.repeat (.*)")
async def repeat(rep):
    cnt, txt = rep.pattern_match.group(1).split(" ", 1)
    replyCount = int(cnt)
    toBeRepeated = txt

    replyText = toBeRepeated + "\n"

    for i in range(0, replyCount - 1):
        replyText += toBeRepeated + "\n"

    await rep.edit(replyText)


@register(outgoing=True, pattern="^.repo$")
async def repo_is_here(wannasee):
    """ Para o comando .repo, apenas retorna o URL do repositório. """
    await wannasee.edit(
        "[Clique aqui](https://github.com/thewhiteharlot/PurpleBot) para abrir o repositório do PurpleBot."
    )


@register(outgoing=True, pattern="^.raw$")
async def raw(rawtext):
    the_real_message = None
    reply_to_id = None
    if rawtext.reply_to_msg_id:
        previous_message = await rawtext.get_reply_message()
        the_real_message = previous_message.stringify()
        reply_to_id = rawtext.reply_to_msg_id
    else:
        the_real_message = rawtext.stringify()
        reply_to_id = rawtext.message.id
    with io.BytesIO(str.encode(the_real_message)) as out_file:
        out_file.name = "raw_message_data.txt"
        await rawtext.edit(
            "`Verifique o log do userbot para os dados da mensagem decodificada !!`"
        )
        await rawtext.client.send_file(
            BOTLOG_CHATID,
            out_file,
            force_document=True,
            allow_cache=False,
            reply_to=reply_to_id,
            caption="`Aqui estão os dados da mensagem decodificada !!`",
        )


CMD_HELP.update(
    {
        "random": ".random <item1> <item2> ... <itemN>\
\nUso: Pegue um item aleatório da lista de itens."
    }
)

CMD_HELP.update(
    {
        "sleep": ".sleep <seconds>\
\nUso: Os userbots também se cansam. Deixe o seu adormecer por alguns segundos."
    }
)

CMD_HELP.update(
    {
        "shutdown": ".shutdown\
\nUso: As vezes você só precisa desligar seu bot. As vezes só quer\
ouvir o som de desligamento do Windows XP... mas não ouve."
    }
)

CMD_HELP.update(
    {
        "repo": ".repo\
\nUso: Se está curioso com o que faz o bot funcionar, é disso que precisa."
    }
)

CMD_HELP.update(
    {
        "readme": ".readme\
\nUso: Links para configurar o userbot e seus módulos."
    }
)

CMD_HELP.update(
    {
        "repeat": ".repeat <no.> <text>\
\nUso: Repete o texto um número de vezes. Não confunda com spam."
    }
)

CMD_HELP.update(
    {
        "restart": ".restart\
\nUso: Reinicia o bot !!"
    }
)

CMD_HELP.update(
    {
        "raw": ".raw\
\nUso: Dados detalhados da mensagem em reply, em formatação JSON."
    }
)

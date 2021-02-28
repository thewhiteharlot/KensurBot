# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for purging unneeded messages(usually spam or ot). """

from asyncio import sleep

from telethon.errors import rpcbaseerrors

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP
from userbot.events import register


@register(outgoing=True, pattern="^.purge$")
async def fastpurger(purg):
    """ For .purge command, purge all messages starting from the reply. """
    chat = await purg.get_input_chat()
    msgs = []
    itermsg = purg.client.iter_messages(chat, min_id=purg.reply_to_msg_id)
    count = 0

    if purg.reply_to_msg_id is not None:
        async for msg in itermsg:
            msgs.append(msg)
            count = count + 1
            msgs.append(purg.reply_to_msg_id)
            if len(msgs) == 100:
                await purg.client.delete_messages(chat, msgs)
                msgs = []
    else:
        await purg.edit("`Eu preciso de uma mensagem para começar a limpar.`")
        return

    if msgs:
        await purg.client.delete_messages(chat, msgs)
    done = await purg.client.send_message(
        purg.chat_id,
        f"`Limpeza rápida completa!`\
        \nForam limpadas {str(count)} mensagens",
    )

    if BOTLOG:
        await purg.client.send_message(
            BOTLOG_CHATID, "Foram limpadas " + str(count) + " mensagens com sucesso."
        )
    await sleep(2)
    await done.delete()


@register(outgoing=True, pattern="^.purgeme")
async def purgeme(delme):
    """ For .purgeme, delete x count of your latest message."""
    message = delme.text
    count = int(message[9:])
    i = 1

    async for message in delme.client.iter_messages(delme.chat_id, from_user="me"):
        if i > count + 1:
            break
        i = i + 1
        await message.delete()

    smsg = await delme.client.send_message(
        delme.chat_id,
        "`Limpeza completa!` Foram limpadas " + str(count) + " mensagens.",
    )
    if BOTLOG:
        await delme.client.send_message(
            BOTLOG_CHATID, "Foram limpadas " + str(count) + " mensagens com sucesso."
        )
    await sleep(2)
    i = 1
    await smsg.delete()


@register(outgoing=True, pattern="^.del$")
async def delete_it(delme):
    """ For .del command, delete the replied message. """
    msg_src = await delme.get_reply_message()
    if delme.reply_to_msg_id:
        try:
            await msg_src.delete()
            await delme.delete()
            if BOTLOG:
                await delme.client.send_message(
                    BOTLOG_CHATID, "Mensagem deletada com sucesso"
                )
        except rpcbaseerrors.BadRequestError:
            if BOTLOG:
                await delme.client.send_message(
                    BOTLOG_CHATID, "Não posso deletar essa mensagem"
                )


@register(outgoing=True, pattern="^.edit")
async def editer(edit):
    """ For .editme command, edit your last message. """
    message = edit.text
    chat = await edit.get_input_chat()
    self_id = await edit.client.get_peer_id("me")
    string = str(message[6:])
    i = 1
    async for message in edit.client.iter_messages(chat, self_id):
        if i == 2:
            await message.edit(string)
            await edit.delete()
            break
        i = i + 1
    if BOTLOG:
        await edit.client.send_message(BOTLOG_CHATID, "Mensagem editada com sucesso")


@register(outgoing=True, pattern="^.sd")
async def selfdestruct(destroy):
    """ For .sd command, make self-destructable messages. """
    message = destroy.text
    counter = int(message[4:6])
    text = str(destroy.text[6:])
    await destroy.delete()
    smsg = await destroy.client.send_message(destroy.chat_id, text)
    await sleep(counter)
    await smsg.delete()
    if BOTLOG:
        await destroy.client.send_message(
            BOTLOG_CHATID, "Mensagem auto-destruída com sucesso"
        )


CMD_HELP.update(
    {
        "purge": ".purge\
        \nUso: Limpa todas as mensagens a partir da resposta."
    }
)

CMD_HELP.update(
    {
        "purgeme": ".purgeme <x>\
        \nUso: Exclui x quantidade de suas mensagens mais recentes."
    }
)

CMD_HELP.update(
    {
        "del": ".del\
\nUso: Exclui a mensagem que você respondeu."
    }
)

CMD_HELP.update(
    {
        "edit": ".edit <nova mensagem>\
\nUso: Substitui sua última mensagem por <nova mensagem>."
    }
)

CMD_HELP.update(
    {
        "sd": ".sd <x> <mensagem>\
\nUso: Cria uma mensagem que se autodestrói em x segundos.\
\nMantenha os segundos abaixo de 100, pois isso coloca seu bot para dormir."
    }
)

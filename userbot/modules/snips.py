# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module containing commands for keeping global notes. """

from userbot import BOTLOG_CHATID, CMD_HELP
from userbot.events import register


@register(outgoing=True, pattern=r"\$\w*", ignore_unsafe=True, disable_errors=True)
async def on_snip(event):
    """ Snips logic. """
    try:
        from userbot.modules.sql_helper.snips_sql import get_snip
    except AttributeError:
        return
    name = event.text[1:]
    snip = get_snip(name)
    message_id_to_reply = event.message.reply_to_msg_id
    if not message_id_to_reply:
        message_id_to_reply = None
    if snip and snip.f_mesg_id:
        msg_o = await event.client.get_messages(
            entity=BOTLOG_CHATID, ids=int(snip.f_mesg_id)
        )
        await event.client.send_message(
            event.chat_id, msg_o.message, reply_to=message_id_to_reply, file=msg_o.media
        )
    elif snip and snip.reply:
        await event.client.send_message(
            event.chat_id, snip.reply, reply_to=message_id_to_reply
        )


@register(outgoing=True, pattern=r"^.snip (\w*)")
async def on_snip_save(event):
    """ For .snip command, saves snips for future use. """
    try:
        from userbot.modules.sql_helper.snips_sql import add_snip
    except AtrributeError:
        await event.edit("`Executando em modo não-SQL!`")
        return
    keyword = event.pattern_match.group(1)
    string = event.text.partition(keyword)[2]
    msg = await event.get_reply_message()
    msg_id = None
    if msg and msg.media and not string:
        if BOTLOG_CHATID:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"#SNIP\
            \nPALAVRA CHAVE: {keyword}\
            \n\nA mensagem a seguir é salva como os dados do recorte, NÃO a exclua !!",
            )
            msg_o = await event.client.forward_messages(
                entity=BOTLOG_CHATID, messages=msg, from_peer=event.chat_id, silent=True
            )
            msg_id = msg_o.id
        else:
            await event.edit(
                "`Salvar recortes com mídia requer que BOTLOG_CHATID seja definido.`"
            )
            return
    elif event.reply_to_msg_id and not string:
        rep_msg = await event.get_reply_message()
        string = rep_msg.text
    success = "`Recorte {} com sucesso. Use` **${}** `em qualquer lugar para obtê-lo`"
    if add_snip(keyword, string, msg_id) is False:
        await event.edit(success.format("atualizado", keyword))
    else:
        await event.edit(success.format("salvo", keyword))


@register(outgoing=True, pattern="^.snips$")
async def on_snip_list(event):
    """ For .snips command, lists snips saved by you. """
    try:
        from userbot.modules.sql_helper.snips_sql import get_snips
    except AttributeError:
        await event.edit("`Executando em modo não-SQL!`")
        return

    message = "`Nenhum recorte disponível no momento.`"
    all_snips = get_snips()
    for a_snip in all_snips:
        if message == "`Nenhum recorte disponível no momento.`":
            message = "Recortes disponíveis:\n"
            message += f"`${a_snip.snip}`\n"
        else:
            message += f"`${a_snip.snip}`\n"

    await event.edit(message)


@register(outgoing=True, pattern=r"^.remsnip (\w*)")
async def on_snip_delete(event):
    """ For .remsnip command, deletes a snip. """
    try:
        from userbot.modules.sql_helper.snips_sql import remove_snip
    except AttributeError:
        await event.edit("`Executando em modo não-SQL!`")
        return
    name = event.pattern_match.group(1)
    if remove_snip(name) is True:
        await event.edit(f"`Recorte excluído com sucesso:` **{name}**")
    else:
        await event.edit(f"`Não foi possível encontrar recorte:` **{name}**")


CMD_HELP.update(
    {
        "snips": "\
$<nome_do_recorte>\
\nUso: Obtém o recorte especificado, em qualquer lugar.\
\n\n.snip <nome> <dados> ou responda a uma mensagem com .snip <nome>\
\nUso: Salva a mensagem como um recorte (nota global) com o nome. (Funciona com fotos, documentos e stickers também!)\
\n\n.snips\
\nUso: Obtém todos os recortes salvos.\
\n\n.remsnip <nome_do_recorte>\
\nUso: Exclui o recorte especificado.\
"
    }
)

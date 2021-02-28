# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for keeping control who PM you. """

from sqlalchemy.exc import IntegrityError
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.messages import ReportSpamRequest
from telethon.tl.types import User

from userbot import (
    BOTLOG,
    BOTLOG_CHATID,
    CMD_HELP,
    COUNT_PM,
    LASTMSG,
    LOGS,
    PM_AUTO_BAN,
)
from userbot.events import register

# ========================= CONSTANTS ============================
DEF_UNAPPROVED_MSG = (
    "Ei! Desculpe, eu não aprovei você para mensagens privadas ainda.\n"
    "Por favor espere que eu permita.\n"
    "Até lá, não spamme meu PM...\n"
    "Obrigado pela paciência.\n\n"
    "*Está é uma mensagem automática."
)
# =================================================================


@register(incoming=True, disable_edited=True, disable_errors=True)
async def permitpm(event):
    """ Prohibits people from PMing you without approval. \
        Will block retarded nibbas automatically. """
    if not PM_AUTO_BAN:
        return
    self_user = await event.client.get_me()
    if (
        event.is_private
        and event.chat_id != 777000
        and event.chat_id != self_user.id
        and not (await event.get_sender()).bot
    ):
        try:
            from userbot.modules.sql_helper.globals import gvarstatus
            from userbot.modules.sql_helper.pm_permit_sql import is_approved
        except AttributeError:
            return
        apprv = is_approved(event.chat_id)
        notifsoff = gvarstatus("NOTIF_OFF")

        # Use user custom unapproved message
        getmsg = gvarstatus("unapproved_msg")
        UNAPPROVED_MSG = getmsg if getmsg is not None else DEF_UNAPPROVED_MSG
        # This part basically is a sanity check
        # If the message that sent before is Unapproved Message
        # then stop sending it again to prevent FloodHit
        if not apprv and event.text != UNAPPROVED_MSG:
            if event.chat_id in LASTMSG:
                prevmsg = LASTMSG[event.chat_id]
                # If the message doesn't same as previous one
                # Send the Unapproved Message again
                if event.text != prevmsg:
                    async for message in event.client.iter_messages(
                        event.chat_id, from_user="me", search=UNAPPROVED_MSG
                    ):
                        await message.delete()
                    await event.reply(f"`{UNAPPROVED_MSG}`")
            else:
                await event.reply(f"`{UNAPPROVED_MSG}`")
            LASTMSG.update({event.chat_id: event.text})
            if notifsoff:
                await event.client.send_read_acknowledge(event.chat_id)
            if event.chat_id not in COUNT_PM:
                COUNT_PM.update({event.chat_id: 1})
            else:
                COUNT_PM[event.chat_id] = COUNT_PM[event.chat_id] + 1

            if COUNT_PM[event.chat_id] > 3:
                await event.respond(
                    "`Você está spammando meu PM, o que não é permitido.`\n"
                    "`Não permitirei que mande mensagens novamente até aviso prévio `\n"
                    "`Cya`"
                )

                try:
                    del COUNT_PM[event.chat_id]
                    del LASTMSG[event.chat_id]
                except KeyError:
                    if BOTLOG:
                        await event.client.send_message(
                            BOTLOG_CHATID,
                            "Contador de PM está aparentemente ficando lento, plis reinicie o bot!",
                        )
                    LOGS.info("Erro no contador de PMs!")
                    return

                await event.client(BlockRequest(event.chat_id))
                await event.client(ReportSpamRequest(peer=event.chat_id))

                if BOTLOG:
                    name = await event.client.get_entity(event.chat_id)
                    name0 = str(name.first_name)
                    await event.client.send_message(
                        BOTLOG_CHATID,
                        "["
                        + name0
                        + "](tg://user?id="
                        + str(event.chat_id)
                        + ")"
                        + " era só mais um retardado",
                    )


@register(disable_edited=True, outgoing=True, disable_errors=True)
async def auto_accept(event):
    """ Aprovará automaticamente se você enviar uma mensagem de texto a eles primeiro. """
    if not PM_AUTO_BAN:
        return
    self_user = await event.client.get_me()
    if (
        event.is_private
        and event.chat_id != 777000
        and event.chat_id != self_user.id
        and not (await event.get_sender()).bot
    ):
        try:
            from userbot.modules.sql_helper.globals import gvarstatus
            from userbot.modules.sql_helper.pm_permit_sql import approve, is_approved
        except AttributeError:
            return

        # Use user custom unapproved message
        get_message = gvarstatus("unapproved_msg")
        if get_message is not None:
            UNAPPROVED_MSG = get_message
        else:
            UNAPPROVED_MSG = DEF_UNAPPROVED_MSG

        chat = await event.get_chat()
        if isinstance(chat, User):
            if is_approved(event.chat_id) or chat.bot:
                return
            async for message in event.client.iter_messages(
                event.chat_id, reverse=True, limit=1
            ):
                if (
                    message.text is not UNAPPROVED_MSG
                    and message.from_id == self_user.id
                ):
                    try:
                        approve(event.chat_id)
                    except IntegrityError:
                        return

                if is_approved(event.chat_id) and BOTLOG:
                    await event.client.send_message(
                        BOTLOG_CHATID,
                        "#AUTO-APPROVED\n"
                        + "User: "
                        + f"[{chat.first_name}](tg://user?id={chat.id})",
                    )


@register(outgoing=True, pattern=r"^.notifoff$")
async def notifoff(noff_event):
    """ Para o comando .notifoff, pare de receber notificações de PMs não aprovados. """
    try:
        from userbot.modules.sql_helper.globals import addgvar
    except AttributeError:
        await noff_event.edit("`Executando em modo não-SQL!`")
        return
    addgvar("NOTIF_OFF", True)
    await noff_event.edit("`Notificações de PMs não aprovados estão silenciadas!`")


@register(outgoing=True, pattern=r"^.notifon$")
async def notifon(non_event):
    """ Para o comando .notifoff, obtenha notificações de PMs não aprovados. """
    try:
        from userbot.modules.sql_helper.globals import delgvar
    except AttributeError:
        await non_event.edit("`Executando em modo não-SQL!`")
        return
    delgvar("NOTIF_OFF")
    await non_event.edit(
        "`Notificações de PMs não-aprovados não estão mais silenciadas!`"
    )


@register(outgoing=True, pattern=r"^\.approve(?:$| )(.*)")
async def approvepm(apprvpm):
    """ For .approve command, give someone the permissions to PM you. """
    try:
        from userbot.modules.sql_helper.globals import gvarstatus
        from userbot.modules.sql_helper.pm_permit_sql import approve
    except AttributeError:
        return await apprvpm.edit("**Executando em modo Não-SQL!**")

    if apprvpm.reply_to_msg_id:
        reply = await apprvpm.get_reply_message()
        replied_user = await apprvpm.client.get_entity(reply.sender_id)
        uid = replied_user.id
        name0 = str(replied_user.first_name)

    elif apprvpm.pattern_match.group(1):
        inputArgs = apprvpm.pattern_match.group(1)

        try:
            inputArgs = int(inputArgs)
        except ValueError:
            pass

        try:
            user = await apprvpm.client.get_entity(inputArgs)
        except:
            return await apprvpm.edit("**Nome de usuário/ID inválido.**")

        if not isinstance(user, User):
            return await apprvpm.edit("**Isso pode ser feito apenas com usuários.**")

        uid = user.id
        name0 = str(user.first_name)

    else:
        aname = await apprvpm.client.get_entity(apprvpm.chat_id)
        if not isinstance(aname, User):
            return await apprvpm.edit("**Isso pode ser feito apenas com usuários.**")
        name0 = str(aname.first_name)
        uid = apprvpm.chat_id

    # Get user custom msg
    getmsg = gvarstatus("unapproved_msg")
    UNAPPROVED_MSG = getmsg if getmsg is not None else DEF_UNAPPROVED_MSG
    async for message in apprvpm.client.iter_messages(
        apprvpm.chat_id, from_user="me", search=UNAPPROVED_MSG
    ):
        await message.delete()

    try:
        approve(uid)
    except IntegrityError:
        return await apprvpm.edit("**O usuário já está aprovado.**")

    await apprvpm.edit(f"[{name0}](tg://user?id={uid}) **aprovado para PV!**")

    if BOTLOG:
        await apprvpm.client.send_message(
            BOTLOG_CHATID,
            "#APROVADO\n" + "Usuário: " + f"[{name0}](tg://user?id={uid})",
        )


@register(outgoing=True, pattern=r"^\.disapprove(?:$| )(.*)")
async def disapprovepm(disapprvpm):
    try:
        from userbot.modules.sql_helper.pm_permit_sql import dissprove
    except BaseException:
        return await disapprvpm.edit("**Executando em modo não-SQL!**")

    if disapprvpm.reply_to_msg_id:
        reply = await disapprvpm.get_reply_message()
        replied_user = await disapprvpm.client.get_entity(reply.sender_id)
        aname = replied_user.id
        name0 = str(replied_user.first_name)
        dissprove(aname)

    elif disapprvpm.pattern_match.group(1):
        inputArgs = disapprvpm.pattern_match.group(1)

        try:
            inputArgs = int(inputArgs)
        except ValueError:
            pass

        try:
            user = await disapprvpm.client.get_entity(inputArgs)
        except:
            return await disapprvpm.edit("**ID/Nome de usuário inválido.**")

        if not isinstance(user, User):
            return await disapprvpm.edit("**Isso pode ser feito apenas com usuários.**")

        aname = user.id
        dissprove(aname)
        name0 = str(user.first_name)

    else:
        dissprove(disapprvpm.chat_id)
        aname = await disapprvpm.client.get_entity(disapprvpm.chat_id)
        if not isinstance(aname, User):

            return await disapprvpm.edit("**Isso pode ser feito apenas com usuários.**")
        name0 = str(aname.first_name)
        aname = aname.id

    await disapprvpm.edit(
        f"[{name0}](tg://user?id={aname}) **Proibido de enviar PMs!**"
    )

    if BOTLOG:
        await disapprvpm.client.send_message(
            BOTLOG_CHATID,
            f"[{name0}](tg://user?id={aname})" " foi proibido de mandar PMs para você.",
        )


@register(outgoing=True, pattern=r"^.block$")
async def blockpm(block):
    """ Para o comando .block, bloqueia as pessoas de enviarem PMs para você! """
    if block.reply_to_msg_id:
        reply = await block.get_reply_message()
        replied_user = await block.client.get_entity(reply.from_id)
        aname = replied_user.id
        name0 = str(replied_user.first_name)
        await block.client(BlockRequest(aname))
        await block.edit("`Você foi bloqueado!`")
        uid = replied_user.id
    else:
        await block.client(BlockRequest(block.chat_id))
        aname = await block.client.get_entity(block.chat_id)
        await block.edit("`Você foi bloqueado!`")
        name0 = str(aname.first_name)
        uid = block.chat_id

    try:
        from userbot.modules.sql_helper.pm_permit_sql import dissprove

        dissprove(uid)
    except AttributeError:
        pass

    if BOTLOG:
        await block.client.send_message(
            BOTLOG_CHATID,
            "#BLOQUEADO\n" + "Usuário: " + f"[{name0}](tg://user?id={uid})",
        )


@register(outgoing=True, pattern=r"^.unblock$")
async def unblockpm(unblock):
    """ Para o comando .unblock, deixe as pessoas enviarem PMs para você novamente! """
    if unblock.reply_to_msg_id:
        reply = await unblock.get_reply_message()
        replied_user = await unblock.client.get_entity(reply.from_id)
        name0 = str(replied_user.first_name)
        await unblock.client(UnblockRequest(replied_user.id))
        await unblock.edit("`Você foi desbloqueado!`")

    if BOTLOG:
        await unblock.client.send_message(
            BOTLOG_CHATID,
            f"[{name0}](tg://user?id={replied_user.id})" " foi desbloqueado!.",
        )


@register(outgoing=True, pattern=r"^.(set|get|reset) pm_msg(?: |$)(\w*)")
async def add_pmsg(cust_msg):
    """ Defina sua própria Mensagem não aprovada automática. """
    if not PM_AUTO_BAN:
        return await cust_msg.edit(
            "Você precisa definir `PM_AUTO_BAN` nas ConfigVars do Heroku para `True`"
        )
    try:
        import userbot.modules.sql_helper.globals as sql
    except AttributeError:
        await cust_msg.edit("`Executando em modo não-SQL!`")
        return

    await cust_msg.edit("Processando...")
    conf = cust_msg.pattern_match.group(1)

    custom_message = sql.gvarstatus("unapproved_msg")

    if conf.lower() == "set":
        message = await cust_msg.get_reply_message()
        status = "Saved"

        # check and clear user unapproved message first
        if custom_message is not None:
            sql.delgvar("unapproved_msg")
            status = "Updated"

        if message:
            # TODO: allow user to have a custom text formatting
            # eg: bold, underline, striketrough, link
            # for now all text are in monoscape
            msg = message.message  # get the plain text
            sql.addgvar("unapproved_msg", msg)
        else:
            return await cust_msg.edit("`Responda a uma mensagem`")

        await cust_msg.edit("`Mensagem salva como Mensagem não aprovada automática`")

        if BOTLOG:
            await cust_msg.client.send_message(
                BOTLOG_CHATID,
                f"***{status} Mensagem não aprovada automática :*** \n\n{msg}",
            )

    if conf.lower() == "reset":
        if custom_message is not None:
            sql.delgvar("unapproved_msg")
            await cust_msg.edit(
                "`Mensagem não aprovada automática redefinida para o padrão`"
            )
        else:
            await cust_msg.edit("`Você ainda não definiu uma mensagem personalizada`")

    if conf.lower() == "get":
        if custom_message is not None:
            await cust_msg.edit(
                "***Esta é a sua Mensagem não aprovada automática atual:***"
                f"\n\n{custom_message}"
            )
        else:
            await cust_msg.edit(
                "*Você ainda não definiu Mensagem não aprovada automática*\n"
                f"Usando mensagem padrão: \n\n`{DEF_UNAPPROVED_MSG}`"
            )


CMD_HELP.update(
    {
        "pmpermit": "\
.approve\
\nUso: Aprova a pessoa mencionada/respondida a enviar PMs.\
\n\n.disapprove\
\nUso: Proibe a pessoa mencionada/respondida a enviar PMs.\
\n\n.block\
\nUso: Bloqueia a pessoa.\
\n\n.unblock\
\nUso: Desbloqueia a pessoa para que ela possa lhe enviar PMs.\
\n\n.notifoff\
\nUso: Limpa/desativa quaisquer notificações de PMs não aprovados.\
\n\n.notifon\
\nUso: Permite notificações para PMs não aprovados.\
\n\n.set pm_msg <reply to msg>\
\nUso: Define sua própria Mensagem não aprovada automática.\
\n\n.get pm_msg\
\nUso: Obtenha sua Mensagem não aprovada automática atual.\
\n\n.reset pm_msg\
\nUso: Redefine sua Mensagem não aprovada automática.\
\n\n*A mensagem não aprovada personalizada atualmente não pode ser definida\
\ntexto formatado como negrito, sublinhado, link, etc..\
\nA mensagem será enviada apenas em monoscape"
    }
)

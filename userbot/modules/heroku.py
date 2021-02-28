# Copyright (C) 2020 Adek Maulana.
# All rights reserved.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#

"""
   Heroku manager for your userbot
"""

import codecs
import math
import os

import aiohttp
import heroku3
import requests

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP, HEROKU_API_KEY, HEROKU_APP_NAME
from userbot.events import register

heroku_api = "https://api.heroku.com"
if HEROKU_APP_NAME is not None and HEROKU_API_KEY is not None:
    Heroku = heroku3.from_key(HEROKU_API_KEY)
    app = Heroku.app(HEROKU_APP_NAME)
    heroku_var = app.config()
else:
    app = None


"""
   ConfigVars setting, get current var, set var or delete var...
"""


@register(outgoing=True, pattern=r"^.(get|del) var(?: |$)(\w*)")
async def variable(var):
    exe = var.pattern_match.group(1)
    if app is None:
        await var.edit("`Por favor configure o seu`  **HEROKU_APP_NAME**.")
        return False
    if exe == "get":
        await var.edit("`Obtendo informações...`")
        variable = var.pattern_match.group(2)
        if variable != "":
            if variable in heroku_var:
                if BOTLOG:
                    await var.client.send_message(
                        BOTLOG_CHATID,
                        "#CONFIGVAR\n\n"
                        "**ConfigVar**:\n"
                        f"`{variable}` = `{heroku_var[variable]}`\n",
                    )
                    await var.edit("`Recebido para BOTLOG_CHATID...`")
                    return True
                else:
                    await var.edit("`Por favor defina BOTLOG para True...`")
                    return False
            else:
                await var.edit("`Informação não existe...`")
                return True
        else:
            configvars = heroku_var.to_dict()
            msg = ""
            if BOTLOG:
                for item in configvars:
                    msg += f"`{item}` = `{configvars[item]}`\n"
                await var.client.send_message(
                    BOTLOG_CHATID, "#CONFIGVARS\n\n" "**ConfigVars**:\n" f"{msg}"
                )
                await var.edit("`Recebido para BOTLOG_CHATID...`")
                return True
            else:
                await var.edit("`Por favor defina BOTLOG para True...`")
                return False
    elif exe == "del":
        await var.edit("`Excluindo informações...`")
        variable = var.pattern_match.group(2)
        if variable == "":
            await var.edit("`Especifique o ConfigVars que você deseja deletar...`")
            return False
        if variable in heroku_var:
            if BOTLOG:
                await var.client.send_message(
                    BOTLOG_CHATID,
                    "#DELCONFIGVAR\n\n" "**Delete ConfigVar**:\n" f"`{variable}`",
                )
            await var.edit("`Informação excluída...`")
            del heroku_var[variable]
        else:
            await var.edit("`Informação não existe...`")
            return True


@register(outgoing=True, pattern=r"^.set var (\w*) ([\s\S]*)")
async def set_var(var):
    await var.edit("`Configurando informações...`")
    variable = var.pattern_match.group(1)
    value = var.pattern_match.group(2)
    if variable in heroku_var:
        if BOTLOG:
            await var.client.send_message(
                BOTLOG_CHATID,
                "#SETCONFIGVAR\n\n"
                "**Change ConfigVar**:\n"
                f"`{variable}` = `{value}`",
            )
        await var.edit("`Informação configurada...`")
    else:
        if BOTLOG:
            await var.client.send_message(
                BOTLOG_CHATID,
                "#ADDCONFIGVAR\n\n" "**Add ConfigVar**:\n" f"`{variable}` = `{value}`",
            )
        await var.edit("`Informação adicionada...`")
    heroku_var[variable] = value


"""
    Check account quota, remaining quota, used quota, used app quota
"""


@register(outgoing=True, pattern=r"^.usage(?: |$)")
async def dyno_usage(dyno):
    """
    Get your account Dyno Usage
    """
    await dyno.edit("`Obtendo informações...`")
    useragent = (
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/81.0.4044.117 Mobile Safari/537.36"
    )
    user_id = Heroku.account().id
    headers = {
        "User-Agent": useragent,
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3.account-quotas",
    }
    path = "/accounts/" + user_id + "/actions/get-quota"
    async with aiohttp.ClientSession() as session:
        async with session.get(heroku_api + path, headers=headers) as r:
            if r.status != 200:
                await dyno.client.send_message(
                    dyno.chat_id, f"`{r.reason}`", reply_to=dyno.id
                )
                await dyno.edit("`Não consigo obter informações...`")
                return False
            result = await r.json()
            quota = result["account_quota"]
            quota_used = result["quota_used"]

            """ - User Quota Limit and Used - """
            remaining_quota = quota - quota_used
            percentage = math.floor(remaining_quota / quota * 100)
            minutes_remaining = remaining_quota / 60
            hours = math.floor(minutes_remaining / 60)
            minutes = math.floor(minutes_remaining % 60)

            """ - User App Used Quota - """
            Apps = result["apps"]
            for apps in Apps:
                if apps.get("app_uuid") == app.id:
                    AppQuotaUsed = apps.get("quota_used") / 60
                    AppPercentage = math.floor(apps.get("quota_used") * 100 / quota)
                    break
            else:
                AppQuotaUsed = 0
                AppPercentage = 0

            AppHours = math.floor(AppQuotaUsed / 60)
            AppMinutes = math.floor(AppQuotaUsed % 60)

            await dyno.edit(
                "**Uso dos Dynos**:\n\n"
                f" -> `Uso do Dynos para`  **{app.name}**:\n"
                f"     •  **{AppHours} horas(s), "
                f"{AppMinutes} minuto(s)  -  {AppPercentage}%**"
                "\n-------------------------------------------------------------\n"
                " -> `Horas de Dyno restantes para esse mês`:\n"
                f"     •  **{hours} hora(s), {minutes} minuto(s)  "
                f"-  {percentage}%**"
            )
            return True


@register(outgoing=True, pattern=r"^\.logs")
async def _(dyno):
    try:
        Heroku = heroku3.from_key(HEROKU_API_KEY)
        app = Heroku.app(HEROKU_APP_NAME)
    except BaseException:
        return await dyno.reply(
            "`Certifique-se de que sua chave de API do Heroku e o nome do seu aplicativo estejam configurados corretamente no heroku var.`"
        )
    await dyno.edit("`Obtendo registros....`")
    with open("logs.txt", "w") as log:
        log.write(app.get_log())
    fd = codecs.open("logs.txt", "r", encoding="utf-8")
    data = fd.read()
    key = (
        requests.post("https://nekobin.com/api/documents", json={"content": data})
        .json()
        .get("result")
        .get("key")
    )
    url = f"https://nekobin.com/raw/{key}"
    await dyno.edit(f"`Registros do Heroku:`\n\nEnviado para: [Nekobin]({url})")
    return os.remove("logs.txt")


CMD_HELP.update(
    {
        "heroku": ".usage"
        "\nUso: Verifique as horas restantes dos dynos do Heroku"
        "\n\n.set var <NEW VAR> <VALUE>"
        "\nUso: adiciona uma nova variável ou atualiza a variável de valor existente"
        "\n!!! AVISO !!!, depois de definir uma variável, o bot será reiniciado"
        "\n\n.get var or .get var <VAR>"
        "\nUso: pegue suas variáveis ​​existentes, use-as apenas em seu grupo privado!"
        "\nIsso retorna todas as suas informações privadas, tenha cuidado..."
        "\n\n.del var <VAR>"
        "\nUso: deleta a variável existente"
        "\n!!! AVISO !!!, depois de deletar uma variável, o bot será reiniciado"
        "\n\n`.logs`"
        "\nUso: Obtém os logs das dynos do Heroku"
    }
)

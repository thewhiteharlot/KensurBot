# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
# credits to @AvinashReddy3108
#
"""
This module updates the userbot based on upstream revision
"""

import asyncio
import sys
from os import environ, execle, path, remove

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from userbot import (
    BOTLOG,
    BOTLOG_CHATID,
    CMD_HELP,
    HEROKU_API_KEY,
    HEROKU_APP_NAME,
    UPDATER_ALIAS,
    UPSTREAM_REPO_BRANCH,
    UPSTREAM_REPO_URL,
)
from userbot.events import register

requirements_path = path.join(
    path.dirname(path.dirname(path.dirname(__file__))), "requirements.txt"
)


async def gen_chlog(repo, diff):
    ch_log = ""
    d_form = "%d/%m/%y"
    for c in repo.iter_commits(diff):
        ch_log += (
            f"•[{c.committed_datetime.strftime(d_form)}]: {c.summary} <{c.author}>\n"
        )
    return ch_log


async def update_requirements():
    reqs = str(requirements_path)
    try:
        process = await asyncio.create_subprocess_shell(
            " ".join([sys.executable, "-m", "pip", "install", "-r", reqs]),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        return process.returncode
    except Exception as e:
        return repr(e)


async def deploy(event, repo, ups_rem, ac_br, txt):
    if HEROKU_API_KEY is not None:
        import heroku3

        heroku = heroku3.from_key(HEROKU_API_KEY)
        heroku_app = None
        heroku_applications = heroku.apps()
        if HEROKU_APP_NAME is None:
            await event.edit(
                "`Configure a variável HEROKU_APP_NAME"
                " para poder atualizar o userbot.`"
            )
            repo.__del__()
            return
        for app in heroku_applications:
            if app.name == HEROKU_APP_NAME:
                heroku_app = app
                break
        if heroku_app is None:
            await event.edit(
                f"{txt}\n`Credenciais inválidos do Heroku para atualizar os dynos do userbot.`"
            )
            return repo.__del__()
        await event.edit("`Userbot Dynos sendo atualizados, por favor aguarde...`")
        ups_rem.fetch(ac_br)
        repo.git.reset("--hard", "FETCH_HEAD")
        heroku_git_url = heroku_app.git_url.replace(
            "https://", "https://api:" + HEROKU_API_KEY + "@"
        )
        if "heroku" in repo.remotes:
            remote = repo.remote("heroku")
            remote.set_url(heroku_git_url)
        else:
            remote = repo.create_remote("heroku", heroku_git_url)
        try:
            remote.push(refspec="HEAD:refs/heads/master", force=True)
        except GitCommandError as error:
            await event.edit(f"{txt}\n`Aqui está o log de erros:\n{error}`")
            return repo.__del__()
        await event.edit(
            "`Atualizado com sucesso!\n" "Reiniciando, por favor aguarde...`"
        )

        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID, "#UPDATE \n" "Seu PurpleBot foi atualizado com sucesso."
            )

    else:
        await event.edit("`Por favor configure a variável HEROKU_API_KEY.`")
    return


async def update(event, repo, ups_rem, ac_br):
    try:
        ups_rem.pull(ac_br)
    except GitCommandError:
        repo.git.reset("--hard", "FETCH_HEAD")
    await update_requirements()
    await event.edit("`Atualizado com sucesso!\n" "Reiniciando, por favor aguarde...`")

    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID, "#UPDATE \n" "Seu PurpleBot foi atualizado com sucesso."
        )

    # Spin a new instance of bot
    args = [sys.executable, "-m", "userbot"]
    execle(sys.executable, *args, environ)
    return


@register(outgoing=True, pattern=r"^.update(?: |$)(now|deploy)?")
async def upstream(event):
    "Para o comando .update, checa se o bot está atualizado, atualiza se especificado"
    await event.edit("`Checando por atualizações, aguarde....`")
    conf = event.pattern_match.group(1)
    off_repo = UPSTREAM_REPO_URL
    force_update = False
    try:
        txt = "`Oops.. Atualizador não obteve êxito devido a "
        txt += "um problema ocorreu`\n\n**LOGTRACE:**\n"
        repo = Repo()
    except NoSuchPathError as error:
        await event.edit(f"{txt}\n`diretório {error} não encontrado`")
        return repo.__del__()
    except GitCommandError as error:
        await event.edit(f"{txt}\n`Falha ao inicializar! {error}`")
        return repo.__del__()
    except InvalidGitRepositoryError as error:
        if conf is None:
            return await event.edit(
                f"`Infelizmente, o diretório {error} não parece ser um repositório GitHub."
                "\nMas podemos consertar isso forçando a atualização do userbot usando .update now.`"
            )
        repo = Repo.init()
        origin = repo.create_remote("upstream", off_repo)
        origin.fetch()
        force_update = True
        repo.create_head("master", origin.refs.master)
        repo.heads.master.set_tracking_branch(origin.refs.master)
        repo.heads.master.checkout(True)

    ac_br = repo.active_branch.name
    if ac_br != UPSTREAM_REPO_BRANCH:
        await event.edit(
            "**[UPDATER]:**\n"
            f"`Parece que você está tentando usar uma branch personalizada ({ac_br}). "
            "nesse caso, o atualizador não pode verificar "
            "qual branch deve ser atualizada. "
            "por favor, mude para a branch principal`"
        )
        return repo.__del__()
    try:
        repo.create_remote("upstream", off_repo)
    except BaseException:
        pass

    ups_rem = repo.remote("upstream")
    ups_rem.fetch(ac_br)

    changelog = await gen_chlog(repo, f"HEAD..upstream/{ac_br}")

    if changelog == "" and force_update is False:
        await event.edit(f"\n`{UPDATER_ALIAS} está`  **atualizado**\n")
        return repo.__del__()

    if conf is None and force_update is False:
        changelog_str = (
            f"**Nova ATUALIZAÇÃO disponível\n\nLISTA DE MUDANÇAS:**\n`{changelog}`"
        )
        if len(changelog_str) > 4096:
            await event.edit("`Lista de mudanças muito grande, enviando como arquivo.`")
            file = open("output.txt", "w+")
            file.write(changelog_str)
            file.close()
            await event.client.send_file(
                event.chat_id,
                "output.txt",
                reply_to=event.id,
            )
            remove("output.txt")
        else:
            await event.edit(changelog_str)
        return await event.respond(
            "Digite **.update deploy** ou `.update now` para atualizar"
        )

    if force_update:
        await event.edit(
            "`Sincronizando com o último código estável do userbot, aguarde...`"
        )
    else:
        await event.edit("`Atualizando PurpleBot...`")
    if conf == "now":
        await update(event, repo, ups_rem, ac_br)
    elif conf == "deploy":
        await deploy(event, repo, ups_rem, ac_br, txt)
    return


CMD_HELP.update(
    {
        "update": ".update"
        "\nUso: Checa se o repositório tem atualizações e mostra lista de mudanças."
        "\n\n.update now"
        "\nUso: Atualiza seu userbot, caso hajam alterações no repositório.\n(As mudanças serão revertidas no próximo update, dê preferência ao Deploy)"
        "\n\n.update deploy"
        "\nUso: Atualiza seu userbot no heroku, caso hajam alterações no repositório\n(Recomendado)."
    }
)

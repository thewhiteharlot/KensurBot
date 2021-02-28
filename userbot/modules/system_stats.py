# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for getting information about the server. """

import platform
import shutil
import sys
import time
from asyncio import create_subprocess_exec as asyncrunapp
from asyncio.subprocess import PIPE as asyncPIPE
from datetime import datetime
from os import remove
from platform import python_version, uname
from shutil import which

import psutil
from git import Repo
from telethon import __version__, version

from userbot import ALIVE_LOGO, ALIVE_NAME, CMD_HELP, USERBOT_VERSION, StartTime, bot
from userbot.events import register

# ================= CONSTANT =================
DEFAULTUSER = (
    ALIVE_NAME
    or "Defina um `ALIVE_NAME` ConfigVar no Heroku (.set var ALIVE_NAME [Nome])!"
)
repo = Repo()
modules = CMD_HELP
# ============================================


async def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "dias"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += time_list.pop() + ", "

    time_list.reverse()
    up_time += ":".join(time_list)

    return up_time


@register(outgoing=True, pattern=r"^\.spc")
async def psu(event):
    uname = platform.uname()
    softw = "**Informação de Sistema**\n"
    softw += f"`Sistema   : {uname.system}`\n"
    softw += f"`Lançamento  : {uname.release}`\n"
    softw += f"`Versão  : {uname.version}`\n"
    softw += f"`Máquina  : {uname.machine}`\n"
    # Boot Time
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    softw += f"`Tempo de Boot: {bt.day}/{bt.month}/{bt.year}  {bt.hour}:{bt.minute}:{bt.second}`\n"
    # CPU Cores
    cpuu = "**CPU Info**\n"
    cpuu += "`Núcleos físicos   : " + str(psutil.cpu_count(logical=False)) + "`\n"
    cpuu += "`Núcleos totais      : " + str(psutil.cpu_count(logical=True)) + "`\n"
    # CPU frequencies
    cpufreq = psutil.cpu_freq()
    cpuu += f"`Frequência máxima    : {cpufreq.max:.2f}Mhz`\n"
    cpuu += f"`Frequência mínima    : {cpufreq.min:.2f}Mhz`\n"
    cpuu += f"`Frequência atual: {cpufreq.current:.2f}Mhz`\n\n"
    # CPU usage
    cpuu += "**Uso de CPU por núcleo**\n"
    for i, percentage in enumerate(psutil.cpu_percent(percpu=True)):
        cpuu += f"`Núcleo {i}  : {percentage}%`\n"
    cpuu += "\n**Uso de CPU total**\n"
    cpuu += f"`Todos núcleos: {psutil.cpu_percent()}%`\n"
    # RAM Usage
    svmem = psutil.virtual_memory()
    memm = "**Uso de memória**\n"
    memm += f"`Total     : {get_size(svmem.total)}`\n"
    memm += f"`Disponível : {get_size(svmem.available)}`\n"
    memm += f"`Usado      : {get_size(svmem.used)} ({svmem.percent}%)`\n"
    # Disk Usage
    dtotal, dused, dfree = shutil.disk_usage(".")
    disk = "**Uso de disco**\n"
    disk += f"`Total     : {get_size(dtotal)}`\n"
    disk += f"`Livre      : {get_size(dused)}`\n"
    disk += f"`Usado      : {get_size(dfree)}`\n"
    # Bandwidth Usage
    bw = "**Uso de banda**\n"
    bw += f"`Upload  : {get_size(psutil.net_io_counters().bytes_sent)}`\n"
    bw += f"`Download: {get_size(psutil.net_io_counters().bytes_recv)}`\n"
    help_string = f"{str(softw)}\n"
    help_string += f"{str(cpuu)}\n"
    help_string += f"{str(memm)}\n"
    help_string += f"{str(disk)}\n"
    help_string += f"{str(bw)}\n"
    help_string += "**Informação de Engine**\n"
    help_string += f"`Python {sys.version}`\n"
    help_string += f"`Telethon {__version__}`"
    await event.edit(help_string)


def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


@register(outgoing=True, pattern=r"^\.sysd$")
async def sysdetails(sysd):
    """ For .sysd command, get system info using neofetch. """
    if not sysd.text[0].isalpha() and sysd.text[0] not in ("/", "#", "@", "!"):
        try:
            fetch = await asyncrunapp(
                "neofetch",
                "--stdout",
                stdout=asyncPIPE,
                stderr=asyncPIPE,
            )

            stdout, stderr = await fetch.communicate()
            result = str(stdout.decode().strip()) + str(stderr.decode().strip())

            await sysd.edit("`" + result + "`")
        except FileNotFoundError:
            await sysd.edit("**Instale o neofetch primeiro !!**")


@register(outgoing=True, pattern="^.botver$")
async def bot_ver(event):
    """ For .botver command, get the bot version. """
    if not event.text[0].isalpha() and event.text[0] not in ("/", "#", "@", "!"):
        if which("git") is not None:
            ver = await asyncrunapp(
                "git",
                "describe",
                "--all",
                "--long",
                stdout=asyncPIPE,
                stderr=asyncPIPE,
            )
            stdout, stderr = await ver.communicate()
            verout = str(stdout.decode().strip()) + str(stderr.decode().strip())

            rev = await asyncrunapp(
                "git",
                "rev-list",
                "--all",
                "--count",
                stdout=asyncPIPE,
                stderr=asyncPIPE,
            )
            stdout, stderr = await rev.communicate()
            revout = str(stdout.decode().strip()) + str(stderr.decode().strip())

            await event.edit(
                "`Versão do Userbot: " f"{verout}" "` \n" "`Revisão: " f"{revout}" "`"
            )
        else:
            await event.edit(
                "Pena que você não tem git, você está executando - 'v2.5' de qualquer jeito!"
            )


@register(outgoing=True, pattern="^.pip(?: |$)(.*)")
async def pipcheck(pip):
    """ For .pip command, do a pip search. """
    if not pip.text[0].isalpha() and pip.text[0] not in ("/", "#", "@", "!"):
        pipmodule = pip.pattern_match.group(1)
        if pipmodule:
            await pip.edit("**Procurando...**")
            pipc = await asyncrunapp(
                "pip3",
                "search",
                pipmodule,
                stdout=asyncPIPE,
                stderr=asyncPIPE,
            )

            stdout, stderr = await pipc.communicate()
            pipout = str(stdout.decode().strip()) + str(stderr.decode().strip())

            if pipout:
                if len(pipout) > 4096:
                    await pip.edit("**Resultado muito grande, enviando como arquivo**")
                    file = open("output.txt", "w+")
                    file.write(pipout)
                    file.close()
                    await pip.client.send_file(
                        pip.chat_id,
                        "output.txt",
                        reply_to=pip.id,
                    )
                    remove("output.txt")
                    return
                await pip.edit(
                    "**Consulta: **\n`"
                    f"pip3 search {pipmodule}"
                    "`\n**Resultado: **\n`"
                    f"{pipout}"
                    "`"
                )
            else:
                await pip.edit(
                    "**Consulta: **\n`"
                    f"pip3 search {pipmodule}"
                    "`\n**Resultado: **\n`Nenhum resultado encontrado/falso`"
                )
        else:
            await pip.edit("**Use .help pip para ver um exemplo**")


@register(outgoing=True, pattern=r"^.(alive|on)$")
async def amireallyalive(alive):
    """ For .alive command, check if the bot is running.  """
    uptime = await get_readable_time((time.time() - StartTime))
    output = (
        "`Tudo funcionando como deveria...`\n"
        "`⊷⊷⊷⊷⊷⊷⊷⊷⊷⊷⊶⊷⊶⊶⊶⊶⊶⊶⊶`\n"
        f"•  ⚙️ `Telethon   : v{version.__version__} `\n"
        f"•  🐍 `Python     : v{python_version()} `\n"
        f"•  👤 `Usuário    :`  {DEFAULTUSER} \n"
        "`-----------------------------`\n"
        f"•  💻 `Rodando em : SQL+ `\n"
        f"•  🗃 `Módulos    : {len(modules)} `\n"
        f"•  👾 `PurpleBot  : v{USERBOT_VERSION} `\n"
        f"•  🕒 `Bot Uptime : {uptime} `\n"
        "`⊷⊷⊷⊷⊷⊷⊷⊷⊷⊷⊶⊷⊶⊶⊶⊶⊶⊶⊶`"
    )
    if ALIVE_LOGO:
        try:
            logo = ALIVE_LOGO
            await bot.send_file(alive.chat_id, logo, caption=output)
            await alive.delete()
        except BaseException:
            await alive.edit(
                output + "\n\n *`O logotipo fornecido é inválido."
                "\nCertifique-se de que o link seja direcionado para a imagem do logotipo`"
            )
    else:
        await alive.edit(output)


@register(outgoing=True, pattern="^.aliveu")
async def amireallyaliveuser(username):
    """ For .aliveu command, change the username in the .alive command. """
    message = username.text
    if not (message == ".aliveu" or message[7:8] != " "):
        newuser = message[8:]
        global DEFAULTUSER
        DEFAULTUSER = newuser
    await username.edit(f"**Usuário alterado com sucesso para** `{newuser}` **!**")


@register(outgoing=True, pattern="^.resetalive$")
async def amireallyalivereset(ureset):
    """ For .resetalive command, reset the username in the .alive command. """
    global DEFAULTUSER
    DEFAULTUSER = str(ALIVE_NAME) if ALIVE_NAME else uname().node
    await ureset.edit("**" "Usuário redefinido com sucesso para .alive/on!" "**")


CMD_HELP.update(
    {
        "sysd": ".sysd\
    \nUso: Mostra informações do sistema usando neofetch.\
    \n\n.spc\
    \nUso: Mostrar especificação do sistema."
    }
)
CMD_HELP.update(
    {
        "botver": ".botver\
    \nUso: Mostra a versão do userbot."
    }
)
CMD_HELP.update(
    {
        "pip": ".pip <módulo(s)>\
    \nUso: Faz uma pesquisa de módulos pip."
    }
)
CMD_HELP.update(
    {
        "alive": ".alive | .on\
    \nUso: Digite .alive/.on para ver se seu bot está funcionando ou não.\
    \n\n.aliveu <texto>\
    \nUso: Muda o 'usuário' do .alive/.on para o texto que você deseja.\
    \n\n.resetalive\
    \nUso: Redefine o usuário para o padrãoUso."
    }
)

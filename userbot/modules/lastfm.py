# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#

from asyncio import sleep
from os import environ
from re import sub
from sys import setrecursionlimit
from urllib import parse

from pylast import User, WSError
from telethon.errors import AboutTooLongError
from telethon.errors.rpcerrorlist import FloodWaitError
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.users import GetFullUserRequest

from userbot import (
    BIO_PREFIX,
    BOTLOG,
    BOTLOG_CHATID,
    CMD_HELP,
    DEFAULT_BIO,
    LASTFM_USERNAME,
    bot,
    lastfm,
)
from userbot.events import register

# =================== CONSTANT ===================
LFM_BIO_ENABLED = "```A música atual do last.fm para a bio está agora habilitada.```"
LFM_BIO_DISABLED = "```A música atual do last.fm para a bio está agora desativada. Bio revertido para o padrão.```"
LFM_BIO_RUNNING = "```Música atual do last.fm para bio já está em execução.```"
LFM_BIO_ERR = "```Nenhuma opção especificada.```"
LFM_LOG_ENABLED = "```O registro do last.fm no log do bot agora está habilitado.```"
LFM_LOG_DISABLED = "```O registro do last.fm no log do bot agora está desabilitado.```"
LFM_LOG_ERR = "```Nenhuma opção especificada.```"
ERROR_MSG = "```Módulo last.fm interrompido, ocorreu um erro inesperado.```"

ARTIST = 0
SONG = 0
USER_ID = 0

if BIO_PREFIX:
    BIOPREFIX = BIO_PREFIX
else:
    BIOPREFIX = None

LASTFMCHECK = False
RUNNING = False
LastLog = False
# ================================================


@register(outgoing=True, pattern="^.lastfm$")
async def last_fm(lastFM):
    """ For .lastfm command, fetch scrobble data from last.fm. """
    await lastFM.edit("Processando...")
    preview = None
    playing = User(LASTFM_USERNAME, lastfm).get_now_playing()
    username = f"https://www.last.fm/user/{LASTFM_USERNAME}"
    if playing is not None:
        try:
            image = User(LASTFM_USERNAME, lastfm).get_now_playing().get_cover_image()
        except IndexError:
            image = None
        tags = await gettags(isNowPlaying=True, playing=playing)
        rectrack = parse.quote(f"{playing}")
        rectrack = sub("^", "https://open.spotify.com/search/", rectrack)
        if image:
            output = f"[‎]({image})[{LASTFM_USERNAME}]({username}) __agora está ouvindo:__\n\n• [{playing}]({rectrack})\n`{tags}`"
            preview = True
        else:
            output = f"[{LASTFM_USERNAME}]({username}) __agora está ouvindo:__\n\n• [{playing}]({rectrack})\n`{tags}`"
    else:
        recent = User(LASTFM_USERNAME, lastfm).get_recent_tracks(limit=3)
        playing = User(LASTFM_USERNAME, lastfm).get_now_playing()
        output = (
            f"[{LASTFM_USERNAME}]({username}) __estava ouvindo pela última vez:__\n\n"
        )
        for i, track in enumerate(recent):
            print(i)
            printable = await artist_and_song(track)
            try:
                tags = await gettags(track)
            except WSError as err:
                return await lastFM.edit(err)
            rectrack = parse.quote(str(printable))
            rectrack = sub("^", "https://open.spotify.com/search/", rectrack)
            output += f"• [{printable}]({rectrack})\n"
            if tags:
                output += f"`{tags}`\n\n"
    if preview is not None:
        await lastFM.edit(f"{output}", parse_mode="md", link_preview=True)
    else:
        await lastFM.edit(f"{output}", parse_mode="md")


async def gettags(track=None, isNowPlaying=None, playing=None):
    if isNowPlaying:
        tags = playing.get_top_tags()
        arg = playing
        if not tags:
            tags = playing.artist.get_top_tags()
    else:
        tags = track.track.get_top_tags()
        arg = track.track
    if not tags:
        tags = arg.artist.get_top_tags()
    tags = "".join([" #" + t.item.__str__() for t in tags[:5]])
    tags = sub("^ ", "", tags)
    tags = sub(" ", "_", tags)
    tags = sub("_#", " #", tags)
    return tags


async def artist_and_song(track):
    return f"{track.track}"


async def get_curr_track(lfmbio):
    global ARTIST
    global SONG
    global LASTFMCHECK
    global RUNNING
    global USER_ID
    oldartist = ""
    oldsong = ""
    while LASTFMCHECK:
        try:
            if USER_ID == 0:
                USER_ID = (await lfmbio.client.get_me()).id
            user_info = await bot(GetFullUserRequest(USER_ID))
            RUNNING = True
            playing = User(LASTFM_USERNAME, lastfm).get_now_playing()
            SONG = playing.get_title()
            ARTIST = playing.get_artist()
            oldsong = environ.get("oldsong", None)
            oldartist = environ.get("oldartist", None)
            if playing is not None and SONG != oldsong and ARTIST != oldartist:
                environ["oldsong"] = str(SONG)
                environ["oldartist"] = str(ARTIST)
                if BIOPREFIX:
                    lfmbio = f"{BIOPREFIX} 🎧: {ARTIST} - {SONG}"
                else:
                    lfmbio = f"🎧: {ARTIST} - {SONG}"
                try:
                    if BOTLOG and LastLog:
                        await bot.send_message(
                            BOTLOG_CHATID,
                            f"Tentativa de mudar a biografia para\n{lfmbio}",
                        )
                    await bot(UpdateProfileRequest(about=lfmbio))
                except AboutTooLongError:
                    short_bio = f"🎧: {SONG}"
                    await bot(UpdateProfileRequest(about=short_bio))
            else:
                if playing is None and user_info.about != DEFAULT_BIO:
                    await sleep(6)
                    await bot(UpdateProfileRequest(about=DEFAULT_BIO))
                    if BOTLOG and LastLog:
                        await bot.send_message(
                            BOTLOG_CHATID,
                            f"Biografia redefinida de volta para\n{DEFAULT_BIO}",
                        )
        except AttributeError:
            try:
                if user_info.about != DEFAULT_BIO:
                    await sleep(6)
                    await bot(UpdateProfileRequest(about=DEFAULT_BIO))
                    if BOTLOG and LastLog:
                        await bot.send_message(
                            BOTLOG_CHATID,
                            f"Biografia redefinida de volta para\n{DEFAULT_BIO}",
                        )
            except FloodWaitError as err:
                if BOTLOG and LastLog:
                    await bot.send_message(
                        BOTLOG_CHATID, f"Erro ao alterar bio:\n{err}"
                    )
        except FloodWaitError as err:
            if BOTLOG and LastLog:
                await bot.send_message(BOTLOG_CHATID, f"Erro ao alterar bio:\n{err}")
        except WSError as err:
            if BOTLOG and LastLog:
                await bot.send_message(BOTLOG_CHATID, f"Erro ao alterar bio:\n{err}")
        await sleep(2)
    RUNNING = False


@register(outgoing=True, pattern=r"^.lastbio (on|off)")
async def lastbio(lfmbio):
    arg = lfmbio.pattern_match.group(1).lower()
    global LASTFMCHECK
    global RUNNING
    if arg == "on":
        setrecursionlimit(700000)
        if not LASTFMCHECK:
            LASTFMCHECK = True
            environ["errorcheck"] = "0"
            await lfmbio.edit(LFM_BIO_ENABLED)
            await sleep(4)
            await get_curr_track(lfmbio)
        else:
            await lfmbio.edit(LFM_BIO_RUNNING)
    elif arg == "off":
        LASTFMCHECK = False
        RUNNING = False
        await bot(UpdateProfileRequest(about=DEFAULT_BIO))
        await lfmbio.edit(LFM_BIO_DISABLED)
    else:
        await lfmbio.edit(LFM_BIO_ERR)


@register(outgoing=True, pattern=r"^.lastlog (on|off)")
async def lastlog(lstlog):
    arg = lstlog.pattern_match.group(1).lower()
    global LastLog
    LastLog = False
    if arg == "on":
        LastLog = True
        await lstlog.edit(LFM_LOG_ENABLED)
    elif arg == "off":
        LastLog = False
        await lstlog.edit(LFM_LOG_DISABLED)
    else:
        await lstlog.edit(LFM_LOG_ERR)


CMD_HELP.update(
    {
        "lastfm": ".lastfm\
    \nUso: Mostra a faixa de scrobbling atual ou scrobbles mais recentes se nada estiver sendo reproduzido.\
    \n\nlastbio: .lastbio <on/off>\
    \nUso: Ativa/desativa a reprodução atual do last.fm em bio.\
    \n\nlastlog: .lastlog <on/off>\
    \nUso: Ativa/desativa o registro bio do last.fm no grupo bot-log."
    }
)

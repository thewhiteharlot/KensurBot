# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#

import os

import lyricsgenius
from pylast import User

from userbot import CMD_HELP, GENIUS, LASTFM_USERNAME, lastfm
from userbot.events import register

if GENIUS is not None:
    genius = lyricsgenius.Genius(GENIUS)


@register(outgoing=True, pattern="^.lyrics (?:(now)|(.*) - (.*))")
async def lyrics(lyric):
    await lyric.edit("`Obtendo informações...`")
    if GENIUS is None:
        await lyric.edit(
            "`Forneça o token de acesso genius nas ConfigVars do Heroku...`"
        )
        return False
    if lyric.pattern_match.group(1) == "now":
        playing = User(LASTFM_USERNAME, lastfm).get_now_playing()
        if playing is None:
            await lyric.edit("`Sem informações do scrobble atual do lastfm...`")
            return False
        artist = playing.get_artist()
        song = playing.get_title()
    else:
        artist = lyric.pattern_match.group(2)
        song = lyric.pattern_match.group(3)
    await lyric.edit(f"`Procurando letras por {artist} - {song}...`")
    songs = genius.search_song(song, artist)
    if songs is None:
        await lyric.edit(f"`Música`  **{artist} - {song}**  `não encontrada...`")
        return False
    if len(songs.lyrics) > 4096:
        await lyric.edit("`A letra é muito grande, visualize o arquivo para vê-la.`")
        with open("lyrics.txt", "w+") as f:
            f.write(f"Search query: \n{artist} - {song}\n\n{songs.lyrics}")
        await lyric.client.send_file(
            lyric.chat_id,
            "lyrics.txt",
            reply_to=lyric.id,
        )
        os.remove("lyrics.txt")
        return True
    else:
        await lyric.edit(
            f"**Consulta de pesquisa**:\n`{artist}` - `{song}`"
            f"\n\n```{songs.lyrics}```"
        )
        return True


CMD_HELP.update(
    {
        "lyrics": ".lyrics **<nome do artista> - <nome da música>**"
        "\nUso: Obtenha as letras do artista e da música correspondentes."
        "\n\n.lyrics now"
        "\nUso: Obtenha as letras do artista e música atuais do scrobble do lastfm."
    }
)

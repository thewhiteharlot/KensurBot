# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module containing various scrapers. """

import asyncio
import json
import os
import re
import shutil
import time
from asyncio import sleep
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from emoji import get_emoji_regexp
from google_trans_new import LANGUAGES, google_translator
from gtts import gTTS
from gtts.lang import tts_langs
from requests import get
from search_engine_parser import GoogleSearch
from telethon.tl.types import DocumentAttributeAudio
from wikipedia import summary
from wikipedia.exceptions import DisambiguationError, PageError
from youtube_dl import YoutubeDL
from youtube_dl.utils import (
    ContentTooShortError,
    DownloadError,
    ExtractorError,
    GeoRestrictedError,
    MaxDownloadsReached,
    PostProcessingError,
    UnavailableVideoError,
    XAttrMetadataError,
)
from youtube_search import YoutubeSearch

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP
from userbot.events import register
from userbot.utils import chrome, googleimagesdownload, progress

CARBONLANG = "auto"
TTS_LANG = "pt"
TRT_LANG = "pt"


@register(outgoing=True, pattern="^.crblang (.*)")
async def setlang(prog):
    global CARBONLANG
    CARBONLANG = prog.pattern_match.group(1)
    await prog.edit(f"Idioma para carbon.now.sh definido como {CARBONLANG}")


@register(outgoing=True, pattern=r"^\.carbon")
async def carbon_api(e):
    """ A Wrapper for carbon.now.sh """
    await e.edit("**Processing...**")
    CARBON = "https://carbon.now.sh/?l={lang}&code={code}"
    global CARBONLANG
    textx = await e.get_reply_message()
    pcode = e.text
    if pcode[8:]:
        pcode = str(pcode[8:])
    elif textx:
        pcode = str(textx.message)  # Importing message to module
    code = quote_plus(pcode)  # Converting to urlencoded
    await e.edit("**Processando...\n25%**")
    dl_path = "./.carbon/"
    file_path = dl_path + "carbon.png"
    if os.path.isfile(file_path):
        os.remove(file_path)
    url = CARBON.format(code=code, lang=CARBONLANG)
    driver = await chrome()
    driver.get(url)
    await e.edit("**Processando...\n50%**")
    driver.command_executor._commands["send_command"] = (
        "POST",
        "/session/$sessionId/chromium/send_command",
    )
    params = {
        "cmd": "Page.setDownloadBehavior",
        "params": {"behavior": "allow", "downloadPath": dl_path},
    }
    driver.execute("send_command", params)
    driver.find_element_by_xpath("//button[@id='export-menu']").click()
    driver.find_element_by_xpath("//button[contains(text(),'4x')]").click()
    driver.find_element_by_xpath("//button[contains(text(),'PNG')]").click()
    await e.edit("**Processando...\n75%**")
    # Waiting for downloading
    while not os.path.isfile(file_path):
        await sleep(0.5)
    await e.edit("**Processando...\n100%**")
    await e.edit("**Enviando...**")
    await e.client.send_file(
        e.chat_id,
        file_path,
        caption=(
            "Feito com [Carbon](https://carbon.now.sh/about/),"
            "\num projeto por [Dawn Labs](https://dawnlabs.io/)"
        ),
        force_document=True,
        reply_to=e.message.reply_to_msg_id,
    )

    os.remove(file_path)
    driver.quit()
    # Removing carbon.png after uploading
    await e.delete()  # Deleting msg


@register(outgoing=True, pattern=r"^\.img(?: |$)(\d*)? ?(.*)")
async def img_sampler(event):
    """ For .img command, search and return images matching the query. """

    if event.is_reply and not event.pattern_match.group(2):
        query = await event.get_reply_message()
        query = str(query.message)
    else:
        query = str(event.pattern_match.group(2))

    if not query:
        return await event.edit(
            "**Responda a uma mensagem ou passe uma consulta para pesquisar!**"
        )

    await event.edit("**Processando...**")

    if event.pattern_match.group(1) != "":
        counter = int(event.pattern_match.group(1))
        if counter > 10:
            counter = int(10)
        if counter <= 0:
            counter = int(1)
    else:
        counter = int(3)

    response = googleimagesdownload()

    # creating list of arguments
    arguments = {
        "keywords": query,
        "limit": counter,
        "format": "png",
        "no_directory": "no_directory",
    }

    # if the query contains some special characters, googleimagesdownload errors out
    # this is a temporary workaround for it (maybe permanent)
    try:
        paths = response.download(arguments)
    except Exception as e:
        return await event.edit(f"**Erro:** `{e}`")

    lst = paths[0][query]
    await event.client.send_file(
        await event.client.get_input_entity(event.chat_id), lst
    )
    shutil.rmtree(os.path.dirname(os.path.abspath(lst[0])))
    await event.delete()


@register(outgoing=True, pattern="^.currency (.*)")
async def moni(event):
    input_str = event.pattern_match.group(1)
    input_sgra = input_str.split(" ")
    if len(input_sgra) == 3:
        try:
            number = float(input_sgra[0])
            currency_from = input_sgra[1].upper()
            currency_to = input_sgra[2].upper()
            request_url = "https://api.exchangeratesapi.io/latest?base={}".format(
                currency_from
            )
            current_response = get(request_url).json()
            if currency_to in current_response["rates"]:
                current_rate = float(current_response["rates"][currency_to])
                rebmun = round(number * current_rate, 2)
                await event.edit(
                    "{} {} = {} {}".format(number, currency_from, rebmun, currency_to)
                )
            else:
                await event.edit(
                    "`Esta parece ser uma moeda estrangeira, que não posso converter agora.`"
                )
        except Exception as e:
            await event.edit(str(e))
    else:
        await event.edit("`Invalid syntax.`")
        return


@register(outgoing=True, pattern=r"^\.google(?: |$)(\d*)? ?(.*)")
async def gsearch(event):
    """ For .google command, do a Google search. """

    if event.is_reply and not event.pattern_match.group(2):
        match = await event.get_reply_message()
        match = str(match.message)
    else:
        match = str(event.pattern_match.group(2))

    if not match:
        return await event.edit(
            "**Responda a uma mensagem ou passe uma consulta para pesquisar!**"
        )

    await event.edit("**Processando...**")

    if event.pattern_match.group(1) != "":
        counter = int(event.pattern_match.group(1))
        if counter > 10:
            counter = int(10)
        if counter <= 0:
            counter = int(1)
    else:
        counter = int(3)

    search_args = (str(match), int(1))
    gsearch = GoogleSearch()

    try:
        gresults = await gsearch.async_search(*search_args)
    except Exception:
        return await event.edit(
            "**Erro: sua consulta não foi encontrada ou foi sinalizada como tráfego incomum.**"
        )
    msg = ""

    for i in range(counter):
        try:
            title = gresults["titles"][i]
            link = gresults["links"][i]
            desc = gresults["descriptions"][i]
            msg += f"[{title}]({link})\n`{desc}`\n\n"
        except IndexError:
            break

    await event.edit(
        "**Consulta de pesquisa:**\n`" + match + "`\n\n**Resultados:**\n" + msg,
        link_preview=False,
    )

    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            "Consulta de pesquisa do Google` " + match + " `foi executado com sucesso",
        )


@register(outgoing=True, pattern=r"^.wiki (.*)")
async def wiki(wiki_q):
    """ Para o comando .wiki, busca o conteúdo da Wikipedia. """
    match = wiki_q.pattern_match.group(1)
    try:
        summary(match)
    except DisambiguationError as error:
        await wiki_q.edit(f"Página desambigada encontrada.\n\n{error}")
        return
    except PageError as pageerror:
        await wiki_q.edit(f"Página não encontrada.\n\n{pageerror}")
        return
    result = summary(match)
    if len(result) >= 4096:
        with open("output.txt", "w+") as file:
            file.write(result)
        await wiki_q.client.send_file(
            wiki_q.chat_id,
            "output.txt",
            reply_to=wiki_q.id,
            caption="`Resultado muito grande, enviando como arquivo`",
        )
        if os.path.exists("output.txt"):
            os.remove("output.txt")
        return
    await wiki_q.edit("**Pesquisa:**\n`" + match + "`\n\n**Resultado:**\n" + result)
    if BOTLOG:
        await wiki_q.client.send_message(
            BOTLOG_CHATID, f"Consulta Wiki `{match}` foi executada com sucesso"
        )


@register(outgoing=True, pattern="^.ud (.*)")
async def urban_dict(ud_e):
    """ Para o comando .ud, busca o conteúdo no Urban Dictionary. """
    await ud_e.edit("Processando...")
    query = ud_e.pattern_match.group(1)
    try:
        define(query)
    except HTTPError:
        await ud_e.edit(
            f"Desculpe, não foi possível encontrar nenhum resultado para: {query}"
        )
        return
    mean = define(query)
    deflen = sum(len(i) for i in mean[0]["def"])
    exalen = sum(len(i) for i in mean[0]["example"])
    meanlen = deflen + exalen
    if int(meanlen) >= 0:
        if int(meanlen) >= 4096:
            await ud_e.edit("`Resultado muito grande, enviando como arquivo.`")
            with open("output.txt", "w+") as file:
                file.write(
                    "Texto: "
                    + query
                    + "\n\nSignificado: "
                    + mean[0]["def"]
                    + "\n\n"
                    + "Exemplo: \n"
                    + mean[0]["example"]
                )
            await ud_e.client.send_file(
                ud_e.chat_id,
                "output.txt",
                caption="`Resultado muito grande, enviado como arquivo.`",
            )
            if os.path.exists("output.txt"):
                os.remove("output.txt")
            await ud_e.delete()
            return
        await ud_e.edit(
            "Texto: **"
            + query
            + "**\n\nSignificado: **"
            + mean[0]["def"]
            + "**\n\n"
            + "Exemplo: \n__"
            + mean[0]["example"]
            + "__"
        )
        if BOTLOG:
            await ud_e.client.send_message(
                BOTLOG_CHATID,
                "Consulta UrbanDictionary `" + query + "` executada com sucesso.",
            )
    else:
        await ud_e.edit("Nenhum resultado encontrado para **" + query + "**")


@register(outgoing=True, pattern=r"^.tts(?: |$)([\s\S]*)")
async def text_to_speech(query):
    """ Para o comando .tts, usa o Google Text-to-Speech para transformar texto em áudio. """
    textx = await query.get_reply_message()
    message = query.pattern_match.group(1)
    if message:
        pass
    elif textx:
        message = textx.text
    else:
        await query.edit(
            "`Envie uma mensagem de texto ou responda a uma mensagem para transformar em áudio!`"
        )
        return

    try:
        gTTS(message, lang=TTS_LANG)
    except AssertionError:
        await query.edit(
            "O texto está vazio.\n"
            "Não sobrou nada para falar após a pré-precessão, tokenização e limpeza."
        )
        return
    except ValueError:
        await query.edit("Idioma não é suportado.")
        return
    except RuntimeError:
        await query.edit("Erro ao carregar o dicionário de idiomas.")
        return
    tts = gTTS(message, lang=TTS_LANG)
    tts.save("k.mp3")
    with open("k.mp3", "rb") as audio:
        linelist = list(audio)
        linecount = len(linelist)
    if linecount == 1:
        tts = gTTS(message, lang=TTS_LANG)
        tts.save("k.mp3")
    with open("k.mp3", "r"):
        await query.client.send_file(query.chat_id, "k.mp3", voice_note=True)
        os.remove("k.mp3")
        if BOTLOG:
            await query.client.send_message(
                BOTLOG_CHATID, "Text to Speech executado com sucesso !"
            )
        await query.delete()


# kanged from Blank-x ;---;
@register(outgoing=True, pattern="^.imdb (.*)")
async def imdb(e):
    try:
        movie_name = e.pattern_match.group(1)
        remove_space = movie_name.split(" ")
        final_name = "+".join(remove_space)
        page = get("https://www.imdb.com/find?ref_=nv_sr_fn&q=" + final_name + "&s=all")
        str(page.status_code)
        soup = BeautifulSoup(page.content, "lxml")
        odds = soup.findAll("tr", "odd")
        mov_title = odds[0].findNext("td").findNext("td").text
        mov_link = (
            "http://www.imdb.com/" + odds[0].findNext("td").findNext("td").a["href"]
        )
        page1 = get(mov_link)
        soup = BeautifulSoup(page1.content, "lxml")
        if soup.find("div", "poster"):
            poster = soup.find("div", "poster").img["src"]
        else:
            poster = ""
        if soup.find("div", "title_wrapper"):
            pg = soup.find("div", "title_wrapper").findNext("div").text
            mov_details = re.sub(r"\s+", " ", pg)
        else:
            mov_details = ""
        credits = soup.findAll("div", "credit_summary_item")
        director = credits[0].a.text
        if len(credits) == 1:
            writer = "Não disponível"
            stars = "Não disponível"
        elif len(credits) > 2:
            writer = credits[1].a.text
            actors = [x.text for x in credits[2].findAll("a")]
            actors.pop()
            stars = actors[0] + "," + actors[1] + "," + actors[2]
        else:
            writer = "Não disponível"
            actors = [x.text for x in credits[1].findAll("a")]
            actors.pop()
            stars = actors[0] + "," + actors[1] + "," + actors[2]
        if soup.find("div", "inline canwrap"):
            story_line = soup.find("div", "inline canwrap").findAll("p")[0].text
        else:
            story_line = "Não disponível"
        info = soup.findAll("div", "txt-block")
        if info:
            mov_country = []
            mov_language = []
            for node in info:
                a = node.findAll("a")
                for i in a:
                    if "country_of_origin" in i["href"]:
                        mov_country.append(i.text)
                    elif "primary_language" in i["href"]:
                        mov_language.append(i.text)
        if soup.findAll("div", "ratingValue"):
            for r in soup.findAll("div", "ratingValue"):
                mov_rating = r.strong["title"]
        else:
            mov_rating = "Não disponível"
        await e.edit(
            "<a href=" + poster + ">&#8203;</a>"
            "<b>Title : </b><code>"
            + mov_title
            + "</code>\n<code>"
            + mov_details
            + "</code>\n<b>Rating : </b><code>"
            + mov_rating
            + "</code>\n<b>Country : </b><code>"
            + mov_country[0]
            + "</code>\n<b>Language : </b><code>"
            + mov_language[0]
            + "</code>\n<b>Director : </b><code>"
            + director
            + "</code>\n<b>Writer : </b><code>"
            + writer
            + "</code>\n<b>Stars : </b><code>"
            + stars
            + "</code>\n<b>IMDB Url : </b>"
            + mov_link
            + "\n<b>Story Line : </b>"
            + story_line,
            link_preview=True,
            parse_mode="HTML",
        )
    except IndexError:
        await e.edit("Insira um **nome de filme válido** k obgd")


@register(outgoing=True, pattern=r"^\.trt(?: |$)([\s\S]*)")
async def translateme(trans):
    """ For .trt command, translate the given text using Google Translate. """

    if trans.is_reply and not trans.pattern_match.group(1):
        message = await trans.get_reply_message()
        message = str(message.message)
    else:
        message = str(trans.pattern_match.group(1))

    if not message:
        return await trans.edit(
            "**Envie algum texto ou responda a uma mensagem para traduzir!**"
        )

    translator = google_translator()

    try:
        reply_text = translator.translate(deEmojify(message), lang_tgt=TRT_LANG)
    except ValueError:
        return await trans.edit(
            "**Idioma inválido selecionado, use **`.lang tts <código do idioma>`**.**"
        )

    try:
        source_lan = translator.detect(deEmojify(message))[1].title()
    except:
        source_lan = "(O Google não forneceu esta informação)"

    reply_text = f"De: **{source_lan}**\nPara: **{LANGUAGES.get(TRT_LANG).title()}**\n\n{reply_text}"

    await trans.edit(reply_text)


@register(pattern=".lang (trt|tts) (.*)", outgoing=True)
async def lang(value):
    """ Para o comando .lang, altera o idioma padrão dos scrapers do userbot. """
    util = value.pattern_match.group(1).lower()
    if util == "trt":
        scraper = "Translator"
        global TRT_LANG
        arg = value.pattern_match.group(2).lower()
        if arg in LANGUAGES:
            TRT_LANG = arg
            LANG = LANGUAGES[arg]
        else:
            await value.edit(
                f"`Código de idioma inválido !!`\n`Códigos de idioma disponíveis para TRT`:\n\n`{LANGUAGES}`"
            )
            return
    elif util == "tts":
        scraper = "Text to Speech"
        global TTS_LANG
        arg = value.pattern_match.group(2).lower()
        if arg in tts_langs():
            TTS_LANG = arg
            LANG = tts_langs()[arg]
        else:
            await value.edit(
                f"`Código de idioma inválido !!`\n`Códigos de idioma disponíveis para TTS`:\n\n`{tts_langs()}`"
            )
            return
    await value.edit(f"`Idioma para {scraper} mudou para {LANG.title()}.`")
    if BOTLOG:
        await value.client.send_message(
            BOTLOG_CHATID, f"`Idioma para {scraper} mudou para {LANG.title()}.`"
        )


@register(outgoing=True, pattern=r"^\.yt (\d*) *(.*)")
async def yt_search(video_q):
    """For .yt command, do a YouTube search from Telegram."""
    if video_q.pattern_match.group(1) != "":
        counter = int(video_q.pattern_match.group(1))
        if counter > 10:
            counter = int(10)
        if counter <= 0:
            counter = int(1)
    else:
        counter = int(3)

    query = video_q.pattern_match.group(2)
    if not query:
        await video_q.edit("`Digite algo para pesquisar`")
    await video_q.edit("`Processando...`")

    try:
        results = json.loads(YoutubeSearch(query, max_results=counter).to_json())
    except KeyError:
        return await video_q.edit(
            "`Pesquisa do Youtube falhou.\nNão consigo pesquisar isso!`"
        )

    output = f"**Resultado de Pesquisa:**\n`{query}`\n\n**Resultados:**\n\n"

    for i in results["videos"]:
        try:
            title = i["title"]
            link = "https://youtube.com" + i["url_suffix"]
            channel = i["channel"]
            duration = i["duration"]
            views = i["views"]
            output += f"[{title}]({link})\nCanal: `{channel}`\nDuração: {duration} | {views}\n\n"
        except IndexError:
            break

    await video_q.edit(output, link_preview=False)


@register(outgoing=True, pattern=r".rip(audio|video) (.*)")
async def download_video(v_url):
    """ Para o comando .rip, baixa mídia do YouTube e de muitos outros sites. """
    url = v_url.pattern_match.group(2)
    type = v_url.pattern_match.group(1).lower()

    await v_url.edit("`Preparando para baixar...`")

    if type == "audio":
        opts = {
            "format": "bestaudio",
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "writethumbnail": True,
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
            "outtmpl": "%(id)s.mp3",
            "quiet": True,
            "logtostderr": False,
        }
        video = False
        song = True

    elif type == "video":
        opts = {
            "format": "best",
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "postprocessors": [
                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}
            ],
            "outtmpl": "%(id)s.mp4",
            "logtostderr": False,
            "quiet": True,
        }
        song = False
        video = True

    try:
        await v_url.edit("`Buscando dados, por favor aguarde..`")
        with YoutubeDL(opts) as rip:
            rip_data = rip.extract_info(url)
    except DownloadError as DE:
        return await v_url.edit(f"`{str(DE)}`")
    except ContentTooShortError:
        return await v_url.edit("`O conteúdo do download era muito curto.`")
    except GeoRestrictedError:
        return await v_url.edit(
            "`O vídeo não está disponível em sua localização geográfica "
            "devido a restrições geográficas impostas pelo site.`"
        )
    except MaxDownloadsReached:
        return await v_url.edit("`O limite máximo de downloads foi atingido.`")
    except PostProcessingError:
        return await v_url.edit("`Ocorreu um erro durante o pós-processamento.`")
    except UnavailableVideoError:
        return await v_url.edit("`A mídia não está disponível no formato solicitado.`")
    except XAttrMetadataError as XAME:
        return await v_url.edit(f"`{XAME.code}: {XAME.msg}\n{XAME.reason}`")
    except ExtractorError:
        return await v_url.edit("`Ocorreu um erro durante a extração de informações.`")
    except Exception as e:
        return await v_url.edit(f"{str(type(e)): {str(e)}}")
    c_time = time.time()
    if song:
        await v_url.edit(
            f"`Preparando para fazer upload da música:`\n**{rip_data['title']}**"
        )
        await v_url.client.send_file(
            v_url.chat_id,
            f"{rip_data['id']}.mp3",
            supports_streaming=True,
            attributes=[
                DocumentAttributeAudio(
                    duration=int(rip_data["duration"]),
                    title=str(rip_data["title"]),
                    performer=str(rip_data["uploader"]),
                )
            ],
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(d, t, v_url, c_time, "Enviando..", f"{rip_data['title']}.mp3")
            ),
        )
        os.remove(f"{rip_data['id']}.mp3")
        await v_url.delete()
    elif video:
        await v_url.edit(f"`Preparando para enviar vídeo:`\n**{rip_data['title']}**")
        await v_url.client.send_file(
            v_url.chat_id,
            f"{rip_data['id']}.mp4",
            supports_streaming=True,
            caption=rip_data["title"],
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(d, t, v_url, c_time, "Enviando..", f"{rip_data['title']}.mp4")
            ),
        )
        os.remove(f"{rip_data['id']}.mp4")
        await v_url.delete()


def deEmojify(inputString):
    """ Remova emojis e outros caracteres não seguros da string """
    return get_emoji_regexp().sub("", inputString)


@register(outgoing=True, pattern=r"^.wolfram (.*)")
async def wolfram(wvent):
    """ Wolfram Alpha API """
    if WOLFRAM_ID is None:
        await wvent.edit(
            "Defina o seu WOLFRAM_ID primeiro !\n"
            "Obtenha sua API KEY [aqui](https://"
            "products.wolframalpha.com/api/)",
            parse_mode="Markdown",
        )
        return
    i = wvent.pattern_match.group(1)
    appid = WOLFRAM_ID
    server = f"https://api.wolframalpha.com/v1/spoken?appid={appid}&i={i}"
    res = get(server)
    await wvent.edit(f"**{i}**\n\n" + res.text, parse_mode="Markdown")
    if BOTLOG:
        await wvent.client.send_message(
            BOTLOG_CHATID, f".wolfram {i} was executed successfully"
        )


CMD_HELP.update(
    {
        "img": ".img <consulta>\
        \nUso: Faz uma pesquisa de imagens no Google e mostra 5 imagens."
    }
)
CMD_HELP.update(
    {
        "currency": ".currency <valor> <de> <para>\
        \nUso: Converte várias moedas para você."
    }
)
CMD_HELP.update(
    {
        "carbon": ".carbon <texto> [ou reply]\
        \nUso: Capriche seu código usando carbon.now.sh\nUse .crblang <texto> para definir o idioma do seu código."
    }
)
CMD_HELP.update(
    {
        "google": ".google <consulta>\
        \nUso: Faz uma pesquisa no Google."
    }
)
CMD_HELP.update(
    {
        "wiki": ".wiki <consulta>\
        \nUso: Faz uma pesquisa na Wikipedia."
    }
)
CMD_HELP.update(
    {
        "ud": ".ud <consulta>\
        \nUso: Faz uma pesquisa no Urban Dictionary."
    }
)
CMD_HELP.update(
    {
        "tts": ".tts <texto> [ou reply]\
        \nUso: Traduz text-to-speech para o idioma que está definido.\nUse .lang tts <código do idioma> para definir o idioma para tts. (Padrão é [English])"
    }
)
CMD_HELP.update(
    {
        "trt": ".trt <texto> [ou reply]\
        \nUso: Traduz o texto para o idioma definido.\nUse .lang trt <código do idioma> para definir idioma para trt. (Padrão é [English])"
    }
)
CMD_HELP.update(
    {
        "yt": ".yt <número> <pesquisa>"
        "\nUso: Faz uma pesquisa no YouTube."
        "\nÉ possível especificar o número de resultados mostrados (padrão é 3)."
    }
)
CMD_HELP.update(
    {"imdb": ".imdb <nome-do-filme>\nMostra informações do filme e outras coisas."}
)
CMD_HELP.update(
    {
        "rip": ".ripaudio <url> ou ripvideo <url>\
        \nUso: Baixe vídeos e músicas do YouTube (e [muitos outros sites](https://ytdl-org.github.io/youtube-dl/supportedsites.html))."
    }
)
CMD_HELP.update(
    {
        "wolfram": ".wolfram <consulta>\
        \nUso: Obtenha respostas para perguntas usando WolframAlpha Spoken Results API."
    }
)

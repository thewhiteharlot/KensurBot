# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
# Port to UserBot by @MoveAngel

from covid import Covid

from userbot import CMD_HELP
from userbot.events import register


@register(outgoing=True, pattern="^.covid (.*)")
async def corona(event):
    await event.edit("`Processando...`")
    country = event.pattern_match.group(1)
    covid = Covid(source="worldometers")
    try:
        country_data = covid.get_status_by_country_name(country)
        output_text = (
            f"`Confirmado   : {format_integer(country_data['confirmed'])}`\n"
            + f"`Ativo      : {format_integer(country_data['active'])}`\n"
            + f"`Mortes      : {format_integer(country_data['deaths'])}`\n"
            + f"`Recuperados   : {format_integer(country_data['recovered'])}`\n\n"
            + f"`Novos Casos   : {format_integer(country_data['new_cases'])}`\n"
            + f"`Novas Mortes  : {format_integer(country_data['new_deaths'])}`\n"
            + f"`Crítico    : {format_integer(country_data['critical'])}`\n"
            + f"`Total de testes : {format_integer(country_data['total_tests'])}`\n\n"
            + f"Dados fornecidos por [Worldometer](https://www.worldometers.info/coronavirus/country/{country})"
        )
        await event.edit(f"Informações do covid-19 {country}:\n\n{output_text}")
    except ValueError:
        await event.edit(
            f"Nenhuma informação encontrada para: {country}!\nVerifique a ortografia e tente novamente."
        )


def format_integer(number, thousand_separator="."):
    def reverse(string):
        string = "".join(reversed(string))
        return string

    s = reverse(str(number))
    count = 0
    result = ""
    for char in s:
        count = count + 1
        if count % 3 == 0:
            if len(s) == count:
                result = char + result
            else:
                result = thousand_separator + char + result
        else:
            result = char + result
    return result


CMD_HELP.update(
    {
        "covid": ".covid <país>"
        "\nUso: Obtenha informações sobre os dados do covid-19 em seu país.\n"
    }
)

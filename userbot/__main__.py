# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot start point """

from importlib import import_module
from sys import argv

from telethon.errors.rpcerrorlist import PhoneNumberInvalidError
from userbot import LOGS, bot
from userbot.modules import ALL_MODULES


INVALID_PH = '\nERRO: O número de telefone é INVÁLIDO' \
             '\n Dica: Use o código do país junto com o número.' \
             '\n ou verifique o seu número de telefone e tente novamente !'

try:
    bot.start()
except PhoneNumberInvalidError:
    print(INVALID_PH)
    exit(1)

for module_name in ALL_MODULES:
    imported_module = import_module("userbot.modules." + module_name)

LOGS.info("Você está executando PurpleBot [v4.8]")

LOGS.info(
    "Parabéns, seu userbot agora está rodando !! Teste-o digitando .on/.alive em qualquer chat."
)

if len(argv) not in (1, 3, 4):
    bot.disconnect()
else:
    bot.run_until_disconnected()

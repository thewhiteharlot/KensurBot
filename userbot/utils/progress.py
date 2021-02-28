# Copyright (C) 2020 Adek Maulana
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#

import math
import time

from .exceptions import CancelProcess
from .tools import humanbytes, time_formatter


async def progress(
    current, total, gdrive, start, prog_type, file_name=None, is_cancelled=False
):
    now = time.time()
    diff = now - start
    if is_cancelled is True:
        raise CancelProcess

    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff)
        eta = round((total - current) / speed)
        if "upload" in prog_type.lower():
            status = "Enviando"
        elif "download" in prog_type.lower():
            status = "Baixando"
        else:
            status = "Desconhecido"
        progress_str = "`{0}` | [{1}{2}] `{3}%`".format(
            status,
            "".join(["■" for i in range(math.floor(percentage / 10))]),
            "".join(["▨" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2),
        )
        tmp = (
            f"{progress_str}\n"
            f"`{humanbytes(current)} de {humanbytes(total)}"
            f" @ {humanbytes(speed)}`\n"
            f"`Tempo estimado` -> {time_formatter(eta)}\n"
            f"`Duração` -> {time_formatter(elapsed_time)}"
        )
        await gdrive.edit(f"`{prog_type}`\n\n" f"`Status`\n{tmp}")

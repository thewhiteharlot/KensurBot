from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import DeletePhotosRequest, UploadProfilePhotoRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import InputPhoto

from userbot import CMD_HELP, LOGS, STORAGE, bot
from userbot.events import register

if not hasattr(STORAGE, "userObj"):
    STORAGE.userObj = False


@register(outgoing=True, pattern=r"^\.clone ?(.*)")
async def impostor(event):
    inputArgs = event.pattern_match.group(1)

    if "restore" in inputArgs:
        await event.edit("**Voltando à minha verdadeira identidade...**")
        if not STORAGE.userObj:
            return await event.edit(
                "**Você precisa se passar por um perfil antes de reverter!**"
            )
        await updateProfile(STORAGE.userObj, restore=True)
        return await event.edit("**Revertido com sucesso!**")
    elif inputArgs:
        try:
            user = await event.client.get_entity(inputArgs)
        except:
            return await event.edit("**Nome de usuário/ID inválido.")
        userObj = await event.client(GetFullUserRequest(user))
    elif event.reply_to_msg_id:
        replyMessage = await event.get_reply_message()
        if replyMessage.sender_id is None:
            return await event.edit(
                "**Não é possível se passar por administradores anônimos, RIP.**"
            )
        userObj = await event.client(GetFullUserRequest(replyMessage.sender_id))
    else:
        return await event.edit(
            "**Digite** `.help clone` **para aprender como usá-lo.**"
        )

    if not STORAGE.userObj:
        STORAGE.userObj = await event.client(GetFullUserRequest(event.sender_id))

    LOGS.info(STORAGE.userObj)

    await event.edit("**Roubando a identidade dessa pessoa aleatória...**")
    await updateProfile(userObj)
    await event.edit("**Eu sou você e você sou eu.**")


async def updateProfile(userObj, restore=False):
    firstName = (
        "Deleted Account"
        if userObj.user.first_name is None
        else userObj.user.first_name
    )
    lastName = "" if userObj.user.last_name is None else userObj.user.last_name
    userAbout = userObj.about if userObj.about is not None else ""
    userAbout = "" if len(userAbout) > 70 else userAbout
    if restore:
        userPfps = await bot.get_profile_photos("me")
        userPfp = userPfps[0]
        await bot(
            DeletePhotosRequest(
                id=[
                    InputPhoto(
                        id=userPfp.id,
                        access_hash=userPfp.access_hash,
                        file_reference=userPfp.file_reference,
                    )
                ]
            )
        )
    else:
        try:
            userPfp = userObj.profile_photo
            pfpImage = await bot.download_media(userPfp)
            await bot(UploadProfilePhotoRequest(await bot.upload_file(pfpImage)))
        except BaseException:
            pass
    await bot(
        UpdateProfileRequest(about=userAbout, first_name=firstName, last_name=lastName)
    )


CMD_HELP.update(
    {
        "clone": ">`.clone` (como uma resposta a uma mensagem de um usuário)\
    \nUso: Rouba a identidade do usuário.\
    \n\n>`.clone <nome do usuário/ID>`\
    \nUso: Rouba o nome de usuário/id fornecida.\
    \n\n>`.clone restore`\
    \nUso: Reverta para sua verdadeira identidade.\
    \n\n**Sempre restaure antes de executá-lo novamente.**\
"
    }
)

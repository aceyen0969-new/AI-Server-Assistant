import discord


async def send_long_message(
    channel: discord.abc.Messageable,
    text: str
):

    MAX_LENGTH = 1900


    while len(text) > MAX_LENGTH:

        chunk = text[:MAX_LENGTH]


        # Try paragraph break
        split_position = chunk.rfind(
            "\n\n"
        )


        # Try line break
        if split_position < 500:

            split_position = chunk.rfind(
                "\n"
            )


        # Try space
        if split_position < 500:

            split_position = chunk.rfind(
                " "
            )


        # Last resort
        if split_position < 1:

            split_position = MAX_LENGTH


        await channel.send(
            text[:split_position].strip()
        )


        text = text[
            split_position:
        ].strip()


    if text:

        await channel.send(text)
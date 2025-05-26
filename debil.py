import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import yt_dlp
import asyncio

load_dotenv()

TOKEN = os.getenv("TOKEN")

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    "options": "-vn",
}


ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("debilu"):
        params = message.content.split(" ")
        print(message.author)
        for czanel in client.get_all_channels():
            if type(czanel) is discord.channel.VoiceChannel:
                if (
                    message.author.voice
                    and czanel.id == message.author.voice.channel.id
                    and len(params) > 1
                ):
                    print("playing", params[1])
                    if not client.voice_clients:
                        await czanel.connect()

                    loop = asyncio.get_event_loop()
                    data = await loop.run_in_executor(
                        None, lambda: ytdl.extract_info(params[1], download=True)
                    )
                    filename = ytdl.prepare_filename(data)
                    client.voice_clients[0].play(
                        discord.FFmpegPCMAudio(filename, **ffmpeg_options),
                        after=lambda e: print(f"Player error: {e}") if e else None,
                    )

        await message.channel.send("Przyjąłem")


client.run(TOKEN)

import discord
from dotenv import load_dotenv
import os
import yt_dlp
import asyncio
import re

load_dotenv()

TOKEN = os.getenv("TOKEN")

ytdl_format_options = {
    "format": "bestaudio/worstvideo",
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
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
}

prefix_return_message = "Przyjąłem"

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

playback_queue = asyncio.Queue()
players = []


async def player():
    while True:
        url, title, channel = await playback_queue.get()
        while client.voice_clients[0].is_playing():
            await asyncio.sleep(2)

        client.voice_clients[0].play(
            discord.FFmpegPCMAudio(url, **ffmpeg_options),
            after=lambda e: print(f"Player error: {e}") if e else None,
        )
        await channel.send(f"{prefix_return_message}, gramy {title}")


async def add_music(music, channel):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None,
        lambda: ytdl.extract_info(music, download=False),
    )
    if "entries" in data:
        await channel.send(
            f"{prefix_return_message}, dodaję {data['title']}, liczba tracków: {len(data['entries'])}"
        )
        for e in data["entries"]:
            url = e["url"]
            title = e["title"]
            playback_queue.put_nowait((url, title, channel))

        return False

    url = data["url"]
    title = data["title"]
    playback_queue.put_nowait((url, title, channel))
    return True


def recreate_players():
    for p in players:
        p.cancel()
    players.clear()
    new_player = asyncio.create_task(player())
    players.append(new_player)


def empty_queue():
    while not playback_queue.empty():
        playback_queue.get_nowait()
        playback_queue.task_done()


def stop_voice_clients():
    if client.voice_clients:
        client.voice_clients[0].stop()


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    start_player = asyncio.create_task(player())
    players.append(start_player)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("debilu"):
        params = re.sub(" +", " ", message.content).split(" ")
        return_message = prefix_return_message
        if len(params) > 2:
            if params[1] == "play":
                found_vc = False
                for czanel in client.get_all_channels():
                    if type(czanel) is discord.channel.VoiceChannel:
                        if (
                            message.author.voice
                            and czanel.id == message.author.voice.channel.id
                        ):
                            found_vc = True
                            if not client.voice_clients:
                                await czanel.connect()

                            await add_music(params[2], message.channel)

                if not found_vc:
                    return_message += (
                        ", odmawiam. Podłącz się wpierw do kanału głosowego."
                    )
                    await message.channel.send(return_message)
            else:
                return_message = "Nie przyjąłem, co ty do mnie mówisz człowieku."
                await message.channel.send(return_message)

        else:
            if len(params) > 1:
                if params[1] == "stop":
                    print("Stopping playback")
                    empty_queue()
                    recreate_players()
                    stop_voice_clients()
                    return_message += ", koniec zabawy."
                    await message.channel.send(return_message)

                elif params[1] == "next":
                    if playback_queue.empty():
                        return_message += ", to już koniec kolejki."
                        await message.channel.send(return_message)
                    stop_voice_clients()

                else:
                    return_message = "Nie przyjąłem, co ty do mnie mówisz człowieku."
                    await message.channel.send(return_message)

            else:
                return_message += ", tylko za mało argumentów masz."
                await message.channel.send(return_message)


client.run(TOKEN)

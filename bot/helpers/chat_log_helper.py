import logging
import os
import tarfile
import tempfile
from typing import Union

import discord
from discord import TextChannel, Thread
from discord.ext import commands


async def collect_chat_log_to_file(
    channel: Union[TextChannel, Thread],
    temp_dir: tempfile.TemporaryDirectory,
    limit: int = 10000,
    order: bool = True,
) -> str:
    """Writes chat log to in-memory file."""
    if (
        channel.type == discord.ChannelType.public_thread
        or channel.type == discord.ChannelType.private_thread
    ):
        prefix = "challenge-thread"
    else:
        prefix = "channel"
    file_path = f"{prefix}-{channel.name}.txt"
    chat_log = open(file_path, "w", encoding="utf-8")
    # TODO: Cover more cases.
    async for m in channel.history(limit=limit, oldest_first=order):
        # TODO: Replace it with case match in Python 3.10+
        if m.type == discord.MessageType.pins_add:
            chat_log.write(
                f"[{m.created_at} UTC] {m.author} pinned a message: {m.content}.\n"
            )
        elif m.type == discord.MessageType.call:
            chat_log.write(f"[{m.created_at} UTC] {m.author} started a call.\n")
        elif m.type == discord.MessageType.thread_created:
            chat_log.write(
                f"[{m.created_at} UTC] {m.author} created a thread: {m.content}.\n"
            )
        elif m.type == discord.MessageType.thread_starter_message:
            chat_log.write(
                f"[{m.created_at} UTC] {m.author} started thread with message: {m.clean_content}.\n"
            )
        elif m.type == discord.MessageType.reply:
            chat_log.write(
                f"[{m.created_at} UTC] {m.author} replied: {m.clean_content}.\n"
            )
        elif m.type == discord.MessageType.default:
            if "" != m.clean_content:
                chat_log.write(f"[{m.created_at} UTC] {m.author}: {m.clean_content}\n")
        else:
            chat_log.write(
                f"[{m.created_at} UTC] {m.author} did something I didn't catch yet: {m}\n"
            )

        for file in m.attachments:
            chat_log.write(
                f"[{m.created_at} UTC] {m.author} uploaded a file/image: {file.url}\n"
            )

    chat_log.flush()
    return os.path.basename(chat_log.name)


async def archive_and_gzip_chat_log(ctx: commands.Context):
    """Archive a channel with all its threads and gzip its chat log."""
    temp_dir = tempfile.TemporaryDirectory()
    pwd = os.getcwd()
    os.chdir(temp_dir.name)

    archive_file = tempfile.NamedTemporaryFile(
        prefix=f"chatlog-{ctx.channel.name}-", suffix=".tar.gz", delete=False
    )
    chat_log_tarball = tarfile.open(archive_file.name, mode="w:gz")

    # Archive channel/thread where the message was sent
    chat_log_file = await collect_chat_log_to_file(ctx.channel, temp_dir)
    chat_log_tarball.add(chat_log_file)

    # Archive its threads if there is any
    if ctx.channel.type == discord.ChannelType.text:
        for thread in ctx.channel.threads:
            chat_log_file = await collect_chat_log_to_file(thread, temp_dir)
            chat_log_tarball.add(chat_log_file)

    chat_log_tarball.close()

    os.chdir(pwd)
    return archive_file

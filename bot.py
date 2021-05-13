#!/usr/bin/env python3

import discord
import datetime
import enum
import os

class LogLevel(enum.Enum):
    def __str__(self):
        return self.name

    DEBUG = 0,
    INFO = 1,
    WARNING = 2,
    ERROR = 3,
    FATAL = 4

class Logger(object):
    def __init__(self):
        self.log_level = LogLevel.DEBUG

    @property
    def log_level(self):
        return self._log_level

    @log_level.setter
    def log_level(self, new_log_level):
        self._log_level = new_log_level

    def log(self, level, message):
        print(f"{datetime.datetime.now()} | {level} | {message}")

class SanghaBotClient(discord.Client):
    def __init__(self, logger):
        self.logger = logger
        self.prefix = "!stp"
        super().__init__()

    def is_from_self(self, message):
        return message.author == self.user

    def is_message_for_us(self, message):
        return message.content.startswith(self.prefix)

    def normalise_message(self, message):
        self.logger.log(LogLevel.DEBUG, f"Normalising message: {message}")
        message.content = message.content.lower().lstrip(self.prefix).strip()
        return message

    async def process_message(self, normalised_message):
        self.logger.log(LogLevel.INFO, f"Processing message content: {normalised_message.content}")
        await normalised_message.channel.send(normalised_message.content)

    async def on_ready(self):
        self.logger.log(LogLevel.INFO, "Bot ready to go!")

    async def on_message(self, message):
        self.logger.log(LogLevel.DEBUG, f"Got message: {message}")
        if self.is_message_for_us(message):
            if self.is_from_self(message):
                await message.channel.send("Nice try :wink:")
            else:
                await self.process_message(self.normalise_message(message))

def start_bot(logger, discord_token):
    logger.log(LogLevel.DEBUG, f"Starting bot: __name__ == {__name__}")
    client = SanghaBotClient(logger)
    client.run(discord_token)

if __name__ == "__main__":
    logger = Logger()

    logger.log(LogLevel.DEBUG, "Looking for discord token in environment")
    discord_token = os.getenv("DISCORD_TOKEN", None)

    if discord_token:
        logger.log(LogLevel.DEBUG, "Discord token found!")
    else:
        logger.log(LogLevel.DEBUG, "Discord token not found, bailing!")
        exit(-1)

    start_bot(logger, discord_token)

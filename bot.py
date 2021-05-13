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
        super().__init__()

    async def on_ready(self):
        self.logger.log(LogLevel.INFO, "Bot ready to go!")

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

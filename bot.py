#!/usr/bin/env python3

import discord
import datetime
import enum
import os
import sqlite3

class PromptStore(object):
    def __init__(self, logger):
        self.logger = logger
        self.logger.log(LogLevel.DEBUG, "Creating database")
        self.connection = sqlite3.connect("prompt_store.sqlite3")
        self.prompt_table_name = "table_prompts"
        self.insert_datetime_field_name = "insert_datetime"

        self.connection.execute(f"CREATE TABLE IF NOT EXISTS {self.prompt_table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {self.insert_datetime_field_name} DATETIME, message TEXT, content TEXT, prompt TEXT)")

    def get_timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def add(self, message, prompt):
        self.logger.log(LogLevel.DEBUG, f"Adding prompt:\n{message}\n{prompt}")
        cursor = self.connection.cursor()
        cursor.execute(f"INSERT INTO {self.prompt_table_name} VALUES (NULL, ?, ?, ?, ?)", [self.get_timestamp(), str(message), str(message.content), str(prompt)])
        self.connection.commit()

    def remove(self, id):
        self.logger.log(LogLevel.DEBUG, f"Removing prompt ID: {id}")
        cursor = self.connection.cursor()
        cursor.execute(f"DELETE FROM {self.prompt_table_name} WHERE id = (?)", [id])
        self.connection.commit()

    def list(self, n):
        self.logger.log(LogLevel.DEBUG, f"Listing {n} prompts")
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {self.prompt_table_name} ORDER BY {self.insert_datetime_field_name} DESC LIMIT {n}")
        return cursor.fetchall()

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
    def __init__(self, logger, prompt_store):
        self.logger = logger
        self.prompt_store = prompt_store
        self.prefix = "!stp"

        self.command_handlers = {
            "add": self.on_command_add,
            "list": self.on_command_list,
            "remove": self.on_command_remove
        }

        super().__init__()

    async def on_command_add(self, normalised_message, tokenised_content):
        if len(tokenised_content) == 0:
            return await self.handle_misunderstood_message(normalised_message, f"You didn't say what to add!")

        prompt = " ".join(tokenised_content)

        self.prompt_store.add(normalised_message, prompt)

        await normalised_message.channel.send(f"Added prompt: {prompt}")

    async def on_command_remove(self, normalised_message, tokenised_content):
        if len(tokenised_content) != 1:
            return await self.handle_misunderstood_message(normalised_message, f"Remove expects 1 parameter (the prompt ID, see list)")

        try:
            id = int(tokenised_content[0])
        except:
            return await self.handle_misunderstood_message(normalised_message, f"Couldn't convert {tokenised_content[0]} into ID")

        self.prompt_store.remove(id)
        await normalised_message.channel.send(f"Removed prompt with ID: {id}")

    async def on_command_list(self, normalised_message, tokenised_content):
        if len(tokenised_content) != 1:
            return await self.handle_misunderstood_message(normalised_message, f"List expects 1 parameter (the number of prompts to list)")

        try:
            n = int(tokenised_content[0])
        except:
            return await self.handle_misunderstood_message(normalised_message, f"Couldn't convert {tokenised_content[0]} into number")

        min_messages = 1
        max_messages = 20

        if min_messages > n or max_messages < n:
            return await self.handle_misunderstood_message(normalised_message, f"Can't list {n} messages (min = {min_messages}, max = {max_messages})")

        prompts = self.prompt_store.list(n)

        formatted_prompts = '\n'.join([f"ID: {prompt[0]}, prompt: {prompt[-1]}" for prompt in prompts])
        quoted_prompts = f"```\n{formatted_prompts}\n```"
        prompts_with_header = f"Listing {n} prompts:\n{quoted_prompts}"
        await normalised_message.channel.send(prompts_with_header)

    def is_from_self(self, message):
        return message.author == self.user

    def is_message_for_us(self, message):
        return message.content.startswith(self.prefix)

    def normalise_message(self, message):
        self.logger.log(LogLevel.DEBUG, f"Normalising message: {message}")
        message.content = message.content.lower().lstrip(self.prefix).strip()
        return message

    def tokenise_message_content(self, content):
        return content.split()

    async def handle_misunderstood_message(self, message, reason):
        self.logger.log(LogLevel.INFO, f"Couldn't handle message:\n{message}\n{message.content}\n{reason}")
        await message.channel.send(f"Sorry, I didn't understand that!\n"
                                 + f"Reason: {reason}")

    async def process_message(self, normalised_message):
        self.logger.log(LogLevel.INFO, f"Processing message content: {normalised_message.content}")
        tokenised_content = self.tokenise_message_content(normalised_message.content)
        if len(tokenised_content) < 1:
           return await self.handle_misunderstood_message(normalised_message, "No command specified")

        command = tokenised_content[0]
        if command in self.command_handlers:
            self.logger.log(LogLevel.DEBUG, f"Command '{command}' received")
            return await self.command_handlers[command](normalised_message, tokenised_content[1:])

        return await self.handle_misunderstood_message(normalised_message, "Unknown command")

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

    prompt_store = PromptStore(logger)

    client = SanghaBotClient(logger, prompt_store) 
    client.run(discord_token)

if __name__ == "__main__":
    logger = Logger()

    logger.log(LogLevel.DEBUG, "Looking for discord token in environment")
    discord_token = os.getenv("DISCORD_TOKEN", None)

    if discord_token:
        logger.log(LogLevel.DEBUG, "Discord token found!")
    else:
        logger.log(LogLevel.FATAL, "Discord token not found, bailing!")
        exit(-1)

    start_bot(logger, discord_token)

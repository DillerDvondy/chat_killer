import discord
from discord.ext import commands
import logging

import json
import datetime
import time

import pprint

import config

class JsonF:
    json_path = "data/"

    def __init__(self, guild):
        self.guild = guild

    def json_load(self):
        with open(f"{json_path}{self.guild.id}.json", 'r') as f:
            return json.load(f)

    def json_update(self, data):
        with open(f"{json_path}{self.guild.id}.json", 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

class Goy:
    def __init__(self, member: discord.Member):
        self.member = member

    currentDayTime = 0
    lastADayRegTime = 0

    record_template = {
        "id" : 0,
        "name" : "",
        "time" : "",
        "time_raw" : 0
    }

    def gen_record(self):
        record = self.record_template
        record["id"] = self.member.id
        record["name"] = self.member.nick
        record["time_raw"] = self.currentDayTime
        record["time"] = config.time_convert(self.currentDayTime)
        return record


active_guilds = {}

# Logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Intents + bot innit
intents = discord.Intents.all()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user} ({client.user.id})')

    # Guild + member registration
    for i in client.guilds:
        active_guilds[i.id] = {}
        active_guilds[i.id]['guild'] = i
        for j in i.members:
            if not j.bot:
                active_guilds[i.id][j.id] = Goy(j)

    print(f'Currently running on guilds \n{pprint.pformat(active_guilds)}')

    # Innitial user time check
    for i in active_guilds:
        for j in active_guilds[i]:
            if j != 'guild':
                if active_guilds[i][j].member.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd):
                    active_guilds[i][j].lastADayRegTime = time.time()
                else:
                    active_guilds[i][j].lastADayRegTime = 0


@client.event
async def on_presence_update(before, after):
    if before.bot:
        return

    print(f'User {before.name} changed their status: from {before.status} to {after.status}')

    if after.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd) and before.status not in (discord.Status.online, discord.Status.idle, discord.Status.dnd):
        active_guilds[after.guild.id][after.id].lastADayRegTime = time.time()
    elif before.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd) and after.status not in (discord.Status.online, discord.Status.idle, discord.Status.dnd):
        active_guilds[after.guild.id][after.id].currentDayTime += time.time() - active_guilds[after.guild.id][after.id].lastADayRegTime
        active_guilds[after.guild.id][after.id].lastADayRegTime = 0

    print(f'Current active time for {before.name} is {config.time_convert(active_guilds[after.guild.id][after.id].currentDayTime)}')


@client.command()
async def upload(ctx):
    for guild in active_guilds:
        for user in active_guilds[guild]:
            if user == 'guild':
                continue
            record = active_guilds[guild][user].gen_record()
            print(record)

client.run(config.TOKEN, log_handler=handler, log_level=logging.DEBUG)
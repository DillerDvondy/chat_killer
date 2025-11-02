import discord
from discord.ext import commands, tasks
import logging

import json

from datetime import time as dt_time, datetime
from zoneinfo import ZoneInfo
import time

import pprint

import config

class JsonF:
    json_path = "data/"

    def __init__(self, guild):
        self.guild = guild

    def json_load(self):
        with open(f"{self.json_path}{self.guild.id}.json", 'r') as f:
            return json.load(f)

    def json_update(self, data):
        with open(f"{self.json_path}{self.guild.id}.json", 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

class Goy:
    def __init__(self, member: discord.Member):
        self.member = member

    currentDayOTime = 0
    lastADayRegTime = 0

    currentDayVTime = 0
    lastVRegTime = 0

    """ record_template = {
        "id" : 0,
        "name" : "",
        "time online" : "",
        "time_raw online" : 0,
        "time voice" : "",
        "time_raw voice" : 0
    } """

    def gen_record(self):
        return {
            "id" : self.member.id,
            "name" : self.member.nick,
            "time_raw online" : self.currentDayOTime,
            "time online" : config.time_convert(self.currentDayOTime),
            "time_raw voice" : self.currentDayVTime,
            "time voice" : config.time_convert(self.currentDayVTime)
        }

    def force_save(self):
        if self.member.status in dis_status_online:
            self.currentDayOTime += time.time() - self.lastADayRegTime
            self.lastADayRegTime = time.time()
        if self.member.voice and self.member.voice.channel:
            self.currentDayVTime += time.time() - self.lastVRegTime

    def reset(self):
        currentDayOTime = 0
        if self.member.status in dis_status_online:
            self.lastADayRegTime = time.time()
        else:
            self.lastADayRegTime = 0

        currentDayVTime = 0
        if self.member.voice and self.member.voice.channel:
            self.lastVRegTime = time.time()
        else:
            self.lastVRegTime = 0


active_guilds = {}
dis_status_online = [discord.Status.online, discord.Status.idle, discord.Status.dnd]

# Logging
handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w')

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
                if active_guilds[i][j].member.status in dis_status_online:
                    active_guilds[i][j].lastADayRegTime = time.time()

                if active_guilds[i][j].member.voice and active_guilds[i][j].member.voice.channel:
                    active_guilds[i][j].lastVRegTime = time.time()


    save_stats.start()


@client.event
async def on_presence_update(before, after):
    if before.bot:
        return
    if before.status == after.status:
        return
    print(f'User {before.name} changed their status: from {before.status} to {after.status}')

    goy = active_guilds[before.guild.id][before.id]

    if after.status in dis_status_online and before.status not in dis_status_online:
        goy.lastADayRegTime = time.time()
    elif before.status in dis_status_online and after.status not in dis_status_online:
        goy.currentDayOTime += time.time() - goy.lastADayRegTime
        goy.lastADayRegTime = 0


@client.command()
async def upload(ctx):
    for guild in active_guilds:
        for user in active_guilds[guild]:
            if user == 'guild':
                continue
            record = active_guilds[guild][user].gen_record()
            print(record)

@client.event
async def on_voice_state_update(member: discord.Member, before, after):
    if member.bot:
        return
    if before.channel == after.channel:
        return

    goy = active_guilds[member.guild.id][member.id]

    if not before.channel and after.channel:
        print(f'User {member.display_name} joined voice channel. Starting voicetimer...')
        goy.lastVRegTime = time.time()
    if before.channel and not after.channel:
        print(f'User {member.display_name} left voice channel. Resetting reg time...')
        goy.currentDayVTime += time.time() - goy.lastVRegTime
        goy.lastVRegTime = 0

@client.command()
async def stats(ctx):
    goy = active_guilds[ctx.author.guild.id][ctx.author.id]
    print(goy.gen_record())

@tasks.loop(time=dt_time(hour=23, minute=0, tzinfo=ZoneInfo("Europe/Berlin")))
async def save_stats():
    print('Saving goy stats in json...')

    today_date = str(datetime.now()).split(" ")[0]
    guild_json = []

    for guildID in active_guilds:
        guild_json_obj = JsonF(active_guilds[guildID]['guild'])
        guild_json.append(guild_json_obj)

        data = guild_json_obj.json_load()

        if data['dates'][-1]['date'] != today_date:
                data['dates'].append({'date' : today_date, 'records' : []})

        for goyID in active_guilds[guildID]:
            if goyID == 'guild':
                continue

            goy_obj = active_guilds[guildID][goyID]

            goy_obj.force_save()

            record = goy_obj.gen_record()
            data['dates'][-1]['records'].append(record)
            goy_obj.reset()
            print(f'Goy {goy_obj.member.display_name} was added to temp data')

        guild_json_obj.json_update(data)

    print("Finished loading json files.")

client.run(config.TOKEN, log_handler=handler, log_level=logging.DEBUG)
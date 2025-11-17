import discord
from discord.ext import commands, tasks
import logging

import datetime
from time import time

import pprint
import random

import os
import os.path
from dotenv import load_dotenv

from src import JsonF, Goy
from src import time_convert, day_stats_gen

load_dotenv()
TOKEN = os.getenv("TOKEN")

active_guilds = {}

# Logging
handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w')

# Intents + bot innit
intents = discord.Intents.all()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

# On startup call
@client.event
async def on_ready():
    print(f'We have logged in as {client.user} ({client.user.id})')

    # Guild + member registration
    for guild in client.guilds:
        active_guilds[guild.id] = {}
        active_guilds[guild.id]['guild'] = guild
        active_guilds[guild.id]['bot_channel'] = client.get_channel(int(input(f'Input bot channel for guild {guild.name}:  ')))
        for member in guild.members:
            if not member.bot:
                active_guilds[guild.id][member.id] = Goy(member)

    print(f'Currently running on guilds \n{pprint.pformat(active_guilds)}')

    # Innitial user time check
    for guildID in active_guilds:
        for goyID in active_guilds[guildID]:
            if goyID != 'guild' and goyID != 'bot_channel':
                goyID = goyID
                if active_guilds[guildID][goyID].member.status in Goy.dis_status_online:
                    active_guilds[guildID][goyID].lastADayRegTime = time()

                if active_guilds[guildID][goyID].member.voice and active_guilds[guildID][goyID].member.voice.channel:
                    active_guilds[guildID][goyID].lastVRegTime = time()


    save_stats.start()
    day_stats.start()


@client.event
async def on_presence_update(before, after):
    if before.bot:
        return
    if before.status == after.status:
        return
    print(f'User {before.name} changed their status: from {before.status} to {after.status}')

    goy = active_guilds[before.guild.id][before.id]

    if after.status in Goy.dis_status_online and before.status not in Goy.dis_status_online:
        goy.lastADayRegTime = time()
    elif before.status in Goy.dis_status_online and after.status not in Goy.dis_status_online:
        goy.currentDayOTime += time() - goy.lastADayRegTime
        goy.lastADayRegTime = 0


@client.event
async def on_voice_state_update(member: discord.Member, before, after):
    if member.bot:
        return
    if before.channel == after.channel:
        return

    goy = active_guilds[member.guild.id][member.id]

    if not before.channel and after.channel:
        print(f'User {member.display_name} joined voice channel. Starting voicetimer...')
        goy.lastVRegTime = time()
    if before.channel and not after.channel:
        print(f'User {member.display_name} left voice channel. Resetting reg time...')
        goy.currentDayVTime += time() - goy.lastVRegTime
        goy.lastVRegTime = 0


utc_times = [
    datetime.time(hour=23, minute=0),  # 00:00 CET
    datetime.time(hour=7, minute=0),   # 08:00 CET
    datetime.time(hour=15, minute=0),   # 16:00 CET
]

@tasks.loop(time=utc_times)
async def save_stats():
    print('Saving goy stats in json...')

    today_date = str(datetime.datetime.now()).split(" ")[0]

    for guildID in active_guilds:
        guild_json_obj = JsonF(active_guilds[guildID]['guild'])
        data = guild_json_obj.json_load()

        if today_date not in data['dates']:
            data['dates'][today_date] = {'records' : {}}

        for goyID in active_guilds[guildID]:
            if goyID == 'guild' or goyID == 'bot_channel':
                continue

            goy_obj = active_guilds[guildID][goyID]
            goyID = str(goyID)
            goy_obj.force_save()
            record = goy_obj.gen_record()

            if goyID in data['dates'][today_date]['records']:
                record['time_raw online'] += data['dates'][today_date]['records'][goyID]['time_raw online']
                record['time_raw voice'] += data['dates'][today_date]['records'][goyID]['time_raw voice']
                record['time online'] = time_convert(record['time_raw online'])
                record['time voice'] = time_convert(record['time_raw voice'])
                data['dates'][today_date]['records'].pop(goyID)

            data['dates'][today_date]['records'][goyID] = record
            
            goy_obj.reset()
            print(f'Goy {goy_obj.member.display_name} was added to temp data')

        guild_json_obj.json_update(data)

    print("Finished loading json files.")


@tasks.loop(time=datetime.time(hour=23, minute=2))
async def day_stats():
    today_date = str(datetime.datetime.now()).split(" ")[0]
    
    print("Day stats:")

    for guildID in active_guilds:
        data = JsonF(active_guilds[guildID]['guild']).json_load()

        if today_date not in data['dates']:
            data['dates'][today_date] = {'records' : {}}
        
        killer = None
        killer_time = 0

        for goyID in active_guilds[guildID]:
            if goyID == 'guild' or goyID == 'bot_channel':
                continue
            
            goyID_o = data['dates'][today_date]['records'][str(goyID)]['time_raw online']
            goyID_v = data['dates'][today_date]['records'][str(goyID)]['time_raw voice']

            if killer == None:
                killer = active_guilds[guildID][goyID]
                killer_time = goyID_o - goyID_v
                continue

            if goyID_o - goyID_v > killer_time:
                killer = active_guilds[guildID][goyID]
                killer_time = goyID_o - goyID_v

        temp = day_stats_gen()
        template = temp[1]

        killer_online = data['dates'][today_date]['records'][str(goyID)]['time online']
        killer_voice = data['dates'][today_date]['records'][str(goyID)]['time voice']
        message = temp[0].format(random.choice(template['NICKNAMES'][killer.member.name]), killer.member.display_name, killer_online, killer_voice)

        await active_guilds[guildID]['bot_channel'].send(message)
    #await ctx.send(message)

client.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
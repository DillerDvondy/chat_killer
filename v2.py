import discord
from discord.ext import commands, tasks
import logging

import json
import os.path

from datetime import time as dt_time, datetime
from zoneinfo import ZoneInfo
import time

import pprint

import os
from dotenv import load_dotenv

class JsonF:
    json_path = "data/"

    def __init__(self, guild):
        self.guild = guild

        sample_data = ""
        with open(f"{self.json_path}sample.json", 'r') as f:
                sample_data = json.load(f)
        sample_data["name"] = guild.name
        sample_data["id"] = guild.id

        try:
            with open(f'{self.json_path}{guild.id}.json', 'x') as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=4)
            # print("Guild json file created and sample data written")
        except FileExistsError:
            # print("Guild json file already exists, no data written")
            return

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
            "time online" : time_conver(self.currentDayOTime),
            "time_raw voice" : self.currentDayVTime,
            "time voice" : time_conver(self.currentDayVTime)
        }

    def force_save(self):
        if self.member.status in dis_status_online:
            self.currentDayOTime += time.time() - self.lastADayRegTime
            self.lastADayRegTime = time.time()
        else:
            self.lastADayRegTime = 0

        if self.member.voice and self.member.voice.channel:
            self.currentDayVTime += time.time() - self.lastVRegTime
            self.lastVRegTime = time.time()
        else:
            self.lastVRegTime = 0

    def reset(self):
        self.currentDayOTime = 0
        self.currentDayVTime = 0

def time_convert(seconds):
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h}г {m}хв {s}с"

load_dotenv()
TOKEN = os.getenv("TOKEN")

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


#@tasks.loop(time=dt_time(hour=22, minute=20, tzinfo=ZoneInfo("Europe/Berlin")))
@tasks.loop(hours=8)
async def save_stats():
    print('Saving goy stats in json...')

    today_date = str(datetime.now()).split(" ")[0]

    for guildID in active_guilds:
        guild_json_obj = JsonF(active_guilds[guildID]['guild'])
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

# Govnokod
@client.command()
async def stats(ctx):
    data = JsonF(ctx.guild).json_load()
    return_data = ""
    for goyID in active_guilds[ctx.guild.id]:
        if goyID == 'guild':
            continue
        goy = active_guilds[ctx.guild.id][goyID]
        goy.force_save()
        temp_record = goy.gen_record()
        today_date = str(datetime.now()).split(" ")[0]
        if data['dates'][-1]['date'] != today_date:
                data['dates'].append({'date' : today_date, 'records' : []})
        data['dates'][-1]['records'].append(temp_record)
        online_time = 0
        voice_time = 0
        for entry in data['dates'][-1]['records']:
            if entry['id'] == goy.member.id:
                online_time += entry['time_raw online']
                voice_time += entry['time_raw voice']
        return_data += (f'{goy.member.display_name}\nOnline: {time_conver(online_time)}\nVoice: {time_conver(voice_time)}\n')
    await ctx.send(return_data)



client.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
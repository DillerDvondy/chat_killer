import discord
from discord.ext import commands
import logging

import json
import datetime
import time

import config

json_path = "data/"
local_time_log = {}

def time_format(seconds):
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h}г {m}хв {s}с"

def local_tracking(guild, member, stop=False):
    if not stop:
        local_time_log[str(guild.id)][member.name] = int(time.time())
    else:
        new_record = {
            "id" : f'{member.id}',
            "name" : f'{member.display_name}',
            "time" : time_format(int(time.time()) - local_time_log[str(guild.id)][member.name]),
            "time_raw" : int(time.time()) - local_time_log[str(guild.id)][member.name]
        }

        add_record(new_record=new_record, data=json_load(guild.id))

        local_time_log[str(guild.id)][member.name] = 0

def today_date():
    return str(datetime.datetime.now()).split(" ")[0]

def json_load(guildID):
    with open(f"{json_path}{guildID}.json", 'r') as f:
        return json.load(f)

def json_upload(data, guildID):
    with open(f"{json_path}{guildID}.json", 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def add_tdate(data):
    new_date = {
        "date" : today_date(),
        "records" : []
    }

    data['dates'].append(new_date)
    return data

def add_record(new_record, data, forced=False):
    userID = new_record["id"]
    user_found = False

    if today_date() != data['dates'][-1]['date']:
        data = add_tdate(data)

    for i in range(len(data['dates'][-1]['records'])):
        if str(data['dates'][-1]['records'][i]['id']) == userID:
            user_found = True
            if forced:
                data['dates'][-1]['records'][i] = new_record
            else:
                new_record['time_raw'] += data['dates'][-1]['records'][i]['time_raw']
                new_record['time'] = time_format(new_record['time_raw'])
                data['dates'][-1]['records'][i] = new_record
                break
    if not user_found:
        data['dates'][-1]['records'].append(new_record)
    json_upload(data, data["id"])

# Logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.all()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user} ({client.user.id})')
    active_guilds = []
    for i in client.guilds:
        active_guilds.append(i)

    print('Currently running on guilds: ')
    for i in active_guilds:
        print(f'{i.name}: {i.id}')
        local_time_log[f"{i.id}"] = {}
        for j in i.members:
            if not j.bot:
                if j.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd):
                    local_tracking(guild=i, member=j)

@client.event
async def on_presence_update(before, after):
    if not after.bot:
        if after.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd) and before.status not in (discord.Status.online, discord.Status.idle, discord.Status.dnd):
            local_tracking(guild=after.guild, member=after)
        else:
            local_tracking(guild=after.guild, member=after, stop=True)
    print(f"User {after.display_name} changed their status, new local_time_log: {local_time_log}")

@client.command()
async def me(user: discord.Member):
    data = json_load(user.guild.id)
    time_so_far = 0
    for i in data['dates'][-1]['records']:
        if i["id"] == str(user.author.id):
            time_so_far = int(time.time()) - local_time_log[str(user.guild.id)][user.author.name] + i["time_raw"]
    await user.send(f"Дурник {user.author.display_name} вже {time_format(time_so_far)} в онлайні, може зайти в чат уже на часі?")

blobus_amogus = 1

client.run(config.TOKEN, log_handler=handler, log_level=logging.DEBUG)

import discord
import json
from time import time

from .utils import time_convert

class JsonF:
    json_path = "data/"

    def __init__(self, guild):
        self.guild = guild

        sample_data = ""
        with open(f"{self.json_path}sample.json", 'r', encoding="utf-8") as f:
                sample_data = json.load(f)
        sample_data["name"] = guild.name
        sample_data["id"] = guild.id

        try:
            with open(f'{self.json_path}{guild.id}.json', 'x', encoding="utf-8") as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=4)
            # print("Guild json file created and sample data written")
        except FileExistsError:
            # print("Guild json file already exists, no data written")
            return

    def json_load(self):
        with open(f"{self.json_path}{self.guild.id}.json", 'r', encoding="utf-8") as f:
            return json.load(f)

    def json_update(self, data):
        with open(f"{self.json_path}{self.guild.id}.json", 'w', encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

class Goy:
    def __init__(self, member: discord.Member):
        self.member = member

    dis_status_online = [discord.Status.online, discord.Status.idle, discord.Status.dnd]

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
            "time online" : time_convert(self.currentDayOTime),
            "time_raw voice" : self.currentDayVTime,
            "time voice" : time_convert(self.currentDayVTime)
        }

    def force_save(self):
        if self.member.status in self.dis_status_online:
            self.currentDayOTime += time() - self.lastADayRegTime
            self.lastADayRegTime = time()
        else:
            self.lastADayRegTime = 0

        if self.member.voice and self.member.voice.channel:
            self.currentDayVTime += time() - self.lastVRegTime
            self.lastVRegTime = time()
        else:
            self.lastVRegTime = 0

    def reset(self):
        self.currentDayOTime = 0
        self.currentDayVTime = 0

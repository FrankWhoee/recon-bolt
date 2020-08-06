import asyncio
import json
import os
import warnings
from datetime import datetime

import discord
import yaml
from discord.utils import get
from requests import get

hike_posted = False
hiking_notifications = []

if os.path.exists("database.json"):
    with open('database.json', 'r') as file:
        database = json.load(file)
else:
    print("[WARN] No database file found.")
    with open('database.json', 'w') as file:
        database = {}
        json.dump(database, file)
    print("[WARN] A new database file has been created at database.json.")


def save_db():
    with open('database.json', 'w') as file:
        json.dump(database, file)


with open(r'config.yaml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)


def keycapize(number):
    if number < 10 and number >= 0:
        return str(number) + "️⃣"
    if number == 10:
        return "🔟"


def dekeycapize(keycap: str):
    return int(keycap.replace("️⃣", ""))


register_messages = {}
approval_messages = {}
hiking_messages = []


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == '✅' and reaction.message.id in register_messages and \
                register_messages[reaction.message.id]['author'].id == user.id:
            requested_roles = []
            for emoji in reaction.message.reactions:
                try:
                    async for user in emoji.users():
                        if user == register_messages[reaction.message.id]['author']:
                            requested_roles.append(
                                register_messages[reaction.message.id]['role_codes'][dekeycapize(emoji.emoji) - 1])
                except:
                    continue
            if len(requested_roles) <= 10:
                response = register_messages[reaction.message.id][
                               'author'].display_name + " has registered for these roles. React to the corresponding numbers and then click the checkmark to approve them." + "\n\n"
                i = 0
                for role in requested_roles:
                    i += 1
                    response += keycapize(i) + " " + role.name + "\n"
                m = await self.get_channel(database['approval_channel']).send(response)
                for i in range(1, len(requested_roles) + 1):
                    await m.add_reaction(keycapize(i))
                await m.add_reaction('✅')
                approval_messages[m.id] = {"author": user, "role_codes": requested_roles}
                register_messages.pop(reaction.message.id)
        if reaction.emoji == '✅' and reaction.message.id in approval_messages and (
                user.guild_permissions.administrator or user.id == 194857448673247235):
            approved_roles = []
            for emoji in reaction.message.reactions:
                try:
                    async for user in emoji.users():
                        if (user.guild_permissions.administrator or user.id == 194857448673247235):
                            approved_roles.append(
                                approval_messages[reaction.message.id]['role_codes'][dekeycapize(emoji.emoji) - 1])
                except:
                    continue
            response = "You been approved for the following roles: \n"
            for role in approved_roles:
                await approval_messages[reaction.message.id]['author'].add_roles(role,
                                                                                 reason="Role registration approved by administrator: " +
                                                                                        approval_messages[
                                                                                            reaction.message.id][
                                                                                            'author'].display_name)
                response += "-" + role.name + "\n"
            await approval_messages[reaction.message.id]['author'].send(response)
            approval_messages.pop(reaction.message.id)

    async def on_member_join(self, member):
        if 'default_role' in database:
            for role in database['default_role']:
                await member.add_roles(get(member.guild.roles, id=role))

    async def on_message(self, message):
        global hike_posted
        global hiking_messages
        if self.user in message.mentions:
            await message.channel.send("suck my dick asshole")
        member = message.author
        if member == client.user:
            return
        if len(message.content.split(" ")) < 2:
            command = message.content
        elif "?" in message.content:
            command = message.content.split(" ")[0]
            param = message.content.split(" ")[1:]
        command = command[1:]
        if not message.content.startswith("?"):
            return
        if command == "register":
            if "approval_channel" in database:
                filtered_roles = []
                for role in message.guild.roles:
                    if role.name == "@everyone" or role.managed or (
                            'blacklist' in database and role.id in database['blacklist']):
                        continue
                    else:
                        filtered_roles.append(role)
                if len(filtered_roles) <= 10:
                    response = message.author.mention + " Register for a role by reacting to the corresponding emojis. Click the checkmark when you're done." + "\n\n"
                    i = 0
                    for role in filtered_roles:
                        i += 1
                        response += keycapize(i) + " " + role.name + "\n"
                    m = await message.channel.send(response)
                    for i in range(1, len(filtered_roles) + 1):
                        await m.add_reaction(keycapize(i))
                    await m.add_reaction('✅')
                    register_messages[m.id] = {"author": message.author, "role_codes": filtered_roles}
            else:
                await message.channel.send(
                    "The admin of this server has not yet set a channel for role registration approval. Please contact them to use !set_approval_channel in the preferred channel to receive role registration requests.")
        elif command == "set_approval_channel":
            if message.author.guild_permissions.administrator or message.author.id == 194857448673247235:
                database['approval_channel'] = message.channel.id
                await message.channel.send("This channel has been set to receive role registration requests.")
                save_db()
            else:
                await message.channel.send(
                    "You are not authorized to use this command. You must have the permission of administrator in the server.")
        elif command == "blacklist":
            if message.author.guild_permissions.administrator or message.author.id == 194857448673247235:
                if 'blacklist' not in database:
                    database['blacklist'] = []
                for role in message.role_mentions:
                    if role.id not in database['blacklist']:
                        database['blacklist'].append(role.id)
                save_db()
                if len(database['blacklist']) > 0:
                    response = "The following roles are currently blacklisted from registration: \n\n"
                    for role in database['blacklist']:
                        response += "-" + get(message.guild.roles, id=role).name + "\n"
                else:
                    response = "No roles are blacklisted from registration currently."
                await message.channel.send(response)
            else:
                await message.channel.send(
                    "You are not authorized to use this command. You must have the permission of administrator in the server.")
        elif command == "deblacklist":
            if message.author.guild_permissions.administrator or message.author.id == 194857448673247235:
                if 'blacklist' not in database:
                    database['blacklist'] = []
                for role in message.role_mentions:
                    database['blacklist'].remove(role.id)
                if 'all' in param:
                    database['blacklist'] = []
                save_db()
                if len(database['blacklist']) > 0:
                    response = "The following roles are currently blacklisted from registration: \n\n"
                    for role in database['blacklist']:
                        response += "-" + get(message.guild.roles, id=role).name + "\n"
                else:
                    response = "No roles are blacklisted from registration currently."
                await message.channel.send(response)
            else:
                await message.channel.send(
                    "You are not authorized to use this command. You must have the permission of administrator in the server.")
        elif command == "default_role":
            if message.author.guild_permissions.administrator or message.author.id == 194857448673247235:
                if 'default_role' not in database:
                    database['default_role'] = []
                for role in message.role_mentions:
                    if role.id not in database['default_role']:
                        database['default_role'].append(role.id)

                save_db()
                if len(database['default_role']) > 0:
                    response = "The following roles are currently added to every user upon joining this server: \n\n"
                    for role in database['default_role']:
                        response += "-" + get(message.guild.roles, id=role).name + "\n"
                else:
                    response = "No roles are added to every user upon joining this server."
                await message.channel.send(response)
            else:
                await message.channel.send(
                    "You are not authorized to use this command. You must have the permission of administrator in the server.")
        elif command == "dedefault_role":
            if message.author.guild_permissions.administrator or message.author.id == 194857448673247235:
                if 'default_role' not in database:
                    database['default_role'] = []
                for role in message.role_mentions:
                    database['default_role'].remove(role.id)
                if 'all' in param:
                    database['default_role'] = []
                save_db()
                if len(database['default_role']) > 0:
                    response = "The following roles are currently added to every user upon joining this server: \n\n"
                    for role in database['default_role']:
                        response += "-" + get(message.guild.roles, id=role).name + "\n"
                else:
                    response = "No roles are added to every user upon joining this server."
                await message.channel.send(response)
            else:
                await message.channel.send(
                    "You are not authorized to use this command. You must have the permission of administrator in the server.")
        elif command == "set_hiking":
            if message.author.guild_permissions.administrator or message.author.id == 194857448673247235:
                database['hiking_channel'] = message.channel.id
                save_db()
                await message.channel.send("This channel has been set to receive hiking posts.")
            else:
                await message.channel.send(
                    "You are not authorized to use this command. You must have the permission of administrator in the server.")
        elif command == "weather" or command == "recon" or command == "hike" or command == "hiking":
           for embed in get_embeds():
                await message.channel.send(embed=embed)
        elif command == "end_poll":
            end_poll(message.channel)
        elif command == "poll":
            await message.channel.send(
                "Poll has been triggered manually and will close on Monday 8 AM. Use ?end_poll to tally votes.")
            post_poll(message.channel, limit=7)
        elif command == "today":
            await message.channel.send(embed=get_embeds()[0])

def get_embeds(score_sorted=False):
    output = []
    for score in get_weather():
        if score["score"] < 50:
            colour = discord.Colour(0).from_rgb(r=int(255 * (score["score"] / 50)), g=255, b=0)
        elif score["score"] >= 50 and score["score"] <= 100:
            colour = discord.Colour(0).from_rgb(r=255, g=int(255 * (1 - ((score["score"] - 50) / 50))), b=0)
        else:
            colour = discord.Colour(0).from_rgb(r=255, g=0, b=0)
        embed = discord.Embed(title=datetime.fromtimestamp(score["dt"]).strftime("%A, %B %-d"),
                              description="Recon Score: " + str(round(score["score"], 2)), color=colour)
        embed.set_thumbnail(url=score["icon"])
        embed.add_field(name="Peak Temperature", value=str(score["maxtemp"]) + "°C", inline=False)
        embed.add_field(name="Morning Temperature", value=str(score["morntemp"]) + "°C", inline=False)
        embed.add_field(name="Cloudiness", value=str(score["clouds"]) + "%", inline=True)
        embed.add_field(name="UV Index", value=str(score["uvi"]) + "/11", inline=True)
        embed.add_field(name="Chance of Precipitation", value=str(round(score["pop"] * 100, 2)) + "%",
                        inline=True)
        output.append(embed)
    return output

def get_weather(score_sorted=False):
    r = get("https://api.openweathermap.org/data/2.5/onecall?lat=49.279&lon=-122.973&appid=" + config[
        'weather-token'] + "&units=metric")
    weather_data = json.loads(r.text)
    scores = []
    for day in weather_data["daily"]:
        score = 0
        detail = {}
        detail["dt"] = day["dt"]
        detail["icon"] = 'http://openweathermap.org/img/wn/' + day["weather"][0]["icon"] + '@2x.png'
        # Dew point score
        dewp = 0
        if day["dew_point"] > 15.56:
            dewp = day["dew_point"] - 15.56
        elif day["dew_point"] < 12.78:
            dewp = 12.78 - day["dew_point"]
        dewp *= 2
        score += dewp

        detail['dew_point'] = day["dew_point"]

        # Temperature score
        maxtemp = 0
        if day["temp"]["max"] > 25:
            maxtemp = day["temp"]["max"] - 25
        elif day["temp"]["max"] < 15:
            maxtemp = 15 - day["temp"]["max"]
        maxtemp *= 3
        score += maxtemp

        detail['maxtemp'] = day["temp"]["max"]

        # Temperature score
        morntemp = 0
        if day["temp"]["morn"] > 20:
            morntemp = day["temp"]["morn"] - 20
        elif day["temp"]["morn"] < 15:
            morntemp = 15 - day["temp"]["morn"]
        morntemp *= 1.5
        score += morntemp

        detail['morntemp'] = day["temp"]["morn"]

        # Cloudiness score
        clouds = 0
        optimal_cloudiness = 50
        if day["clouds"] > optimal_cloudiness:
            clouds = (day["clouds"] - optimal_cloudiness)
        elif day["clouds"] < optimal_cloudiness:
            clouds = (optimal_cloudiness - day["clouds"])
        clouds *= 0.09
        score += clouds

        detail['clouds'] = day["clouds"]

        # UVI score
        uvi = day["uvi"] * 0.5
        score += uvi

        detail['uvi'] = day["uvi"]

        # Probability of Precipiation score
        pop = day["pop"] * 100
        score += pop

        detail['pop'] = day["pop"]
        detail['score'] = score
        scores.append(detail)
    if score_sorted:
        return sorted(scores, key=lambda k: k['score'])
    else:
        return scores


client = MyClient()


async def hike_notification():
    await client.wait_until_ready()
    while not client.is_closed():
        for hn in hiking_notifications:
            if datetime.today().day == datetime.fromtimestamp(hn["score"]["dt"]) and datetime.today().hour > 10:
                response = "Reminder: There is a hike today at 11 AM."
                for subbed in hn["subscribed"]:
                    response += subbed.mention + " "
                hn["message"].channel.send(response, embed=get_embeds()[0])
                hiking_notifications.remove(hn)
        await asyncio.sleep(1800)

async def end_poll(channel):
    global hike_posted
    global hiking_messages
    if hike_posted:
        hike_posted = False
        votes = []
        for m, embed, score in hiking_messages:
            count = 0
            subscribed = []
            for reaction in discord.utils.get(client.cached_messages, id=m.id).reactions:
                if reaction.emoji == "✅":
                    count += reaction.count
                    subscribed = await reaction.users().flatten()
                    subscribed.remove(client.user)
                elif reaction.emoji == "❌":
                    count -= reaction.count
            votes.append({
                "embed": embed,
                "message": m,
                "votes": count,
                "subscribed": subscribed,
                "score": score
            })
        votes_sorted = sorted(votes, key=lambda k: k['votes'])

        if votes_sorted[0]["votes"] == votes_sorted[len(votes_sorted) - 1]["votes"]:
            await channel.send(
                    "No hiking date set because no one voted. To retrigger a poll, type ?poll")
        else:
            response = "Hiking date has been set. You will receive notifications and updates for this hiking trip.\n\n"
            hiking_notifications.append(votes_sorted[len(votes_sorted) - 1])
            for sub in votes_sorted[len(votes_sorted) - 1]["subscribed"]:
                response += sub.mention + " "
            votes_sorted[len(votes_sorted) - 1]["embed"]._colour = discord.Colour(0x1E90FF)
            await channel.send(response, embed=votes_sorted[len(votes_sorted) - 1]["embed"])
        hiking_messages = []

async def post_poll(channel, limit=3):
    global hike_posted
    hike_posted = True
    i = 0
    for score in get_weather(score_sorted=True):
        if i >= limit:
            break
        if score["score"] < 50:
            colour = discord.Colour(0).from_rgb(r=int(255 * (score["score"] / 50)), g=255, b=0)
        elif score["score"] >= 50 and score["score"] <= 100:
            colour = discord.Colour(0).from_rgb(r=255, g=int(255 * (1 - ((score["score"] - 50) / 50))), b=0)
        embed = discord.Embed(title=datetime.fromtimestamp(score["dt"]).strftime("%A, %B %-d"),
                              description="Recon Score: " + str(round(score["score"], 2)), color=colour)
        embed.set_thumbnail(url=score["icon"])
        embed.add_field(name="Peak Temperature", value=str(score["maxtemp"]) + "°C", inline=False)
        embed.add_field(name="Morning Temperature", value=str(score["morntemp"]) + "°C", inline=False)
        embed.add_field(name="Cloudiness", value=str(score["clouds"]) + "%", inline=True)
        embed.add_field(name="UV Index", value=str(score["uvi"]) + "/11", inline=True)
        embed.add_field(name="Chance of Precipitation", value=str(round(score["pop"] * 100, 2)) + "%", inline=True)
        m = await channel.send(embed=embed)
        await m.add_reaction("✅")
        await m.add_reaction("❌")
        hiking_messages.append((m, embed, score))
        i += 1

async def hike_posting():
    await client.wait_until_ready()
    while not client.is_closed():
        # if datetime.today().weekday() == 6 and datetime.today().hour > 8 and 'hiking' in database and not hike_posted:
        await post_poll(client.get_user(194857448673247235))
        # Sleeps for 24 hours, then checks votes on hike days, if poll was not ended early.
        # await asyncio.sleep(86400)
        await asyncio.sleep(20)
        # end_poll(client.get_channel(database['hiking_channel']))
        await end_poll(client.get_user(194857448673247235))
        await asyncio.sleep(3600)


client.loop.create_task(hike_posting())
client.run(config['token'])

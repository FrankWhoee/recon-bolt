import discord
import yaml
import os
import json

if os.path.exists("database.json"):
    with open('database.json', 'r') as file:
        database = json.load(file)
else:
    print("[WARN] No database file found.")
    with open('database.json', 'w') as file:
        database = {}
        json.dump(database,file)
    print("[WARN] A new database file has been created at database.json.")

def save_db():
    with open('database.json', 'w') as file:
        json.dump(database,file)

with open(r'config.yaml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

def keycapize(number):
    if number < 10 and number >= 0:
        return str(number) + "️⃣"
    if number == 10:
        return "🔟"

def dekeycapize(keycap: str):
    return int(keycap.replace( "️⃣", ""))

register_messages = {}
approval_messages = {}

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == '✅' and reaction.message.id in register_messages and register_messages[reaction.message.id]['author'].id == user.id:
            requested_roles = []
            for emoji in reaction.message.reactions:
                try:
                    async for user in emoji.users():
                        if user == register_messages[reaction.message.id]['author']:
                            requested_roles.append(register_messages[reaction.message.id]['role_codes'][dekeycapize(emoji.emoji) - 1])
                except:
                    continue
            if len(requested_roles) <= 10:
                response = register_messages[reaction.message.id]['author'].display_name +  " has registered for these roles. React to the corresponding numbers and then click the checkmark to approve them." + "\n\n"
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
        if reaction.emoji == '✅' and reaction.message.id in approval_messages and (user.guild_permissions.administrator or user.id == 194857448673247235):
            approved_roles = []
            for emoji in reaction.message.reactions:
                try:
                    async for user in emoji.users():
                        if (user.guild_permissions.administrator or user.id == 194857448673247235):
                            approved_roles.append(approval_messages[reaction.message.id]['role_codes'][dekeycapize(emoji.emoji) - 1])
                except:
                    continue
            response = "You been approved for the following roles: \n"
            for role in approved_roles:
                await approval_messages[reaction.message.id]['author'].add_roles(role, reason="Role registration approved by administrator: " + approval_messages[reaction.message.id]['author'].display_name)
                response += "-" + role.name + "\n"
            await approval_messages[reaction.message.id]['author'].send(response)
            approval_messages.pop(reaction.message.id)




    async def on_message(self, message):
        if self.user in message.mentions:
            await message.channel.send("suck my dick asshole")
        member = message.author
        if member == client.user:
            return
        if len(message.content.split(" ")) < 2:
            command = message.content
        elif "?" in message.content:
            command, param = message.content.split(" ")[0:1]
        command = command[1:]
        if not message.content.startswith("?"):
            return
        if command == "register":
            if "approval_channel" in database:
                filtered_roles = []
                for role in message.guild.roles:
                    if role.name == "@everyone" or role.managed:
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
                    for i in range(1,len(filtered_roles) + 1):
                        await m.add_reaction(keycapize(i))
                    await m.add_reaction('✅')
                    register_messages[m.id] = {"author": message.author, "role_codes":filtered_roles}
            else:
                await message.channel.send("The admin of this server has not yet set a channel for role registration approval. Please contact them to use !set_approval_channel in the preferred channel to receive role registration requests.")
        elif command == "set_approval_channel":
            if message.author.guild_permissions.administrator or message.author.id == 194857448673247235:
                database['approval_channel'] = message.channel.id
                await message.channel.send("This channel has been set to receive role registration requests.")
                save_db()
            else:
                await message.channel.send("You are not authorized to use this command. You must have the permission of administrator in the server.")
        print('Message from {0.author}: {0.content}'.format(message))

client = MyClient()
client.run(config['token'])
import discord

def keycapize(number):
    if number < 10 and number >= 0:
        return str(number) + "️⃣"
    if number == 10:
        return "🔟"

def dekeycapize(keycap: str):
    return int(keycap.replace( "️⃣", ""))

register_messages = {}

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == '✅' and reaction.message.id in register_messages and register_messages[reaction.message.id]['author'].id == user.id:
            requested_roles = []
            for emoji in reaction.message.reactions:
                requested_roles.append(register_messages[reaction.message.id]['role_codes'][dekeycapize(emoji.emoji) - 1])



    async def on_message(self, message):
        member = message.author
        if member == client.user:
            return
        if len(message.content.split(" ")) < 2:
            command = message.content
        else:
            command, param = message.content.split(" ")[0:1]
        command = command[1:]
        if command == "register":
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
                print(register_messages)

        print('Message from {0.author}: {0.content}'.format(message))

client = MyClient()
client.run('NzM2OTg4MTE3MTY0MDk3NjEx.Xx2zqw.kkzTDOV9nmiyyL7z4a-5lfUuM8w')
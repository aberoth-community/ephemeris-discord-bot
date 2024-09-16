from .bot import *
from .helperFuncs import *

@bot.tree.command(name="hello")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Hello {interaction.user.mention}!", ephemeral=True
    )

@bot.tree.command(name="update_whitelist", description="Only the bot owner may use this command")
@commands.is_owner()
@app_commands.check(is_owner)
@app_commands.default_permissions()
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(user_or_guild="ID of the user or guild you wish to update the settings for", id_type="Specifies if the ID provided is a user ID or guild ID", 
                       expiration="The epoch time in second for which whitelisted status expires. A value of \"-1\" will never expire")
@app_commands.choices(
    id_type=[
        discord.app_commands.Choice(name="User", value=1),
        discord.app_commands.Choice(name="Guild", value=0),
    ],
)
async def updateWhiteList(interaction: discord.Interaction, user_or_guild: str, id_type: discord.app_commands.Choice[int], expiration: int):
    if id_type.name == "User":
        await interaction.response.defer(ephemeral=True, thinking=True)
        username = ""
        try:
            user = await bot.fetch_user(user_or_guild)
            username =  user.name
        except discord.NotFound: 
            await interaction.followup.send(f"Error fetching user name for ID {user_or_guild}:\n\"NotFound\"", ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.followup.send(f"Error fetching user name for ID {user_or_guild}:\n\"HTTPException\"", ephemeral=True)
            return  
        userSettings = fetch_user_settings(user_or_guild)
        try:
            if not userSettings:
                userSettings = newUserSettings(user_or_guild, username, expiration)
            else:
                userSettings['username'] = username
                userSettings['expiration'] = expiration
            update_user_settings(user_or_guild, userSettings)
        except Exception as e:
            await interaction.followup.send(f"Failed to update user_settings table.", ephemeral=True)
            return
        await interaction.followup.send(
            f"Whitelist settings updated for <@{user_or_guild}>:\n**New Expiration:**  " + ("No Expiration" if expiration == -1 else f"<t:{expiration}>"), ephemeral=True
            )
        return
    elif id_type.name == "Guild":
        await interaction.response.defer(ephemeral=True, thinking=True)
        username = ""
        try:
            guild = await bot.fetch_guild(user_or_guild)
            guildName =  guild.name
        except discord.NotFound: 
            await interaction.followup.send(f"Error fetching guild name for ID {user_or_guild}:\n\"NotFound\"", ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.followup.send(f"Error fetching guild name for ID {user_or_guild}:\n\"HTTPException\"", ephemeral=True)
            return
        guildSettings = fetch_guild_settings(user_or_guild)
        if not guildSettings:
            temp = {"guild_id": user_or_guild, "guild": {"name": guildName}, "channel_id": None}
            guildSettings = newGuildSettings(temp)
        try:
            guildSettings['guild_name'] = guildName
            guildSettings['expiration'] = expiration
            update_guild_settings(user_or_guild, guildSettings)
        except Exception as e:
            print(e, interaction)
            await interaction.followup.send(f"Failed to write to guildWhiteList file.", ephemeral=True)
            
        await interaction.followup.send(
            f"Whitelist settings updated for {guildName}:\n**New Expiration:**  " + ("No Expiration" if expiration == -1 else f"<t:{expiration}>"), ephemeral=True
            )
        return
    
    await interaction.response.send_message(f"Invalid command parameters, action aborted.", ephemeral=True)

@updateWhiteList.error
async def UpdateWLError(interaction: discord.Interaction, error):
    await not_owner_error(interaction, error)


@bot.tree.command(name="permissions", description='Tells the user when their and/or the server\'s access they used it on expires')
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def checkPermissions(interaction: discord.Interaction):
    expMsg = ""
    if 0 in interaction._integration_owners:
            expMsg = "**Guild:** "
            if str(interaction.guild_id) in guildWhiteList:
                exp = guildWhiteList[str(interaction.guild_id)].get('expiration')
                expMsg += "No Expiration" if exp == -1 else f"<t:{exp}>"
            else: expMsg += "Not White Listed."
    expMsg += "\n**User:** "
    if str(interaction.user.id) in userWhiteList:
        exp = userWhiteList[str(interaction.user.id)].get('expiration')
        expMsg += "No Expiration" if exp == -1 else f"<t:{exp}>"
    else: expMsg += "Not White Listed."
    
    await interaction.response.send_message(
        content=expMsg,
        ephemeral=True,
    )

@bot.tree.command(
    name="set_server_emojis",
    description="Configures the emojis used for ephemerides requested from prediction menus used within this server.",
)
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@app_commands.default_permissions()
async def setServerEmojis(
    interaction: discord.Interaction,
    white: str = defaultEmojis['White'],
    black: str = defaultEmojis['Black'],
    green: str = defaultEmojis['Green'],
    red: str = defaultEmojis['Red'],
    purple: str = defaultEmojis['Purple'],
    yellow: str = defaultEmojis['Yellow'],
    cyan: str = defaultEmojis['Cyan'],
    blue: str = defaultEmojis['Blue'],
    new: Optional[str] = defaultEmojis['new'],
    waxing_crescent: Optional[str] = defaultEmojis['waxing_crescent'],
    first_quarter: Optional[str] = defaultEmojis['first_quarter'],
    waxing_gibbous: Optional[str] = defaultEmojis['waxing_gibbous'],
    full: Optional[str] = defaultEmojis['full'],
    waning_gibbous: Optional[str] = defaultEmojis['waning_gibbous'],
    third_quarter: Optional[str] = defaultEmojis['third_quarter'],
    waning_crescent: Optional[str] = defaultEmojis['waning_crescent'],
    
):
    invalidEmojis = []
    for emoji in (white, black, green, red, purple, yellow, cyan, blue, new, waxing_crescent,
                first_quarter, waxing_gibbous, full, waning_gibbous, third_quarter, waning_crescent):
        emoji = emoji.strip()
        if not isEmoji(emoji):
            invalidEmojis.append(emoji)
    if len(invalidEmojis) != 0:
        await interaction.response.send_message(
            content=f"**The following emojis are invalid: {invalidEmojis}**, please try again.",
            ephemeral=True,
        )
    else:
        guildSettings = fetch_guild_settings(interaction.guild_id)
        if not guildSettings:
            guildSettings = newGuildSettings(interaction)
        guildSettings["emojis"] = {
            "White": white,
            "Black": black,
            "Green": green,
            "Red": red,
            "Purple": purple,
            "Yellow": yellow,
            "Cyan": cyan,
            "Blue": blue,
            "new": new,
            "waxing_crescent": waxing_crescent,
            "first_quarter": first_quarter,
            "waxing_gibbous": waxing_gibbous,
            "full": full,
            "waning_gibbous": waning_gibbous,
            "third_quarter": third_quarter,
            "waning_crescent": waning_crescent
        }
        emojis = guildSettings["emojis"]
        update_guild_settings(interaction.guild_id, guildSettings)
        await interaction.response.send_message(
            content="**Successfully set server emojis!**"
            f"\n> `White           ` {emojis['White']}"
            f"\n> `Black           ` {emojis['Black']}"
            f"\n> `Green           ` {emojis['Green']}"
            f"\n> `Red             ` {emojis['Red']}"
            f"\n> `Purple          ` {emojis['Purple']}"
            f"\n> `Yellow          ` {emojis['Yellow']}"
            f"\n> `Cyan            ` {emojis['Cyan']}"
            f"\n> `Blue            ` {emojis['Blue']}"
            f"\n> `New Moon        ` {emojis['new']}"
            f"\n> `Waxing Crescent ` {emojis['waxing_crescent']}"
            f"\n> `First Quarter   ` {emojis['first_quarter']}"
            f"\n> `Waxing Gibbous  ` {emojis['waxing_gibbous']}"
            f"\n> `Full Moon       ` {emojis['full']}"
            f"\n> `Waning Gibbous  ` {emojis['waning_gibbous']}"
            f"\n> `Third Quarter   ` {emojis['third_quarter']}"
            f"\n> `Waning Crescent ` {emojis['waning_crescent']}",
            ephemeral=True,
        )


@bot.tree.command(
    name="set_personal_emojis",
    description="Configures the emojis used for ephemerides requested from user installable prediction menus.",
)
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe()
async def setPersonalEmojis(
    interaction: discord.Interaction,
    white: str = defaultEmojis['White'],
    black: str = defaultEmojis['Black'],
    green: str = defaultEmojis['Green'],
    red: str = defaultEmojis['Red'],
    purple: str = defaultEmojis['Purple'],
    yellow: str = defaultEmojis['Yellow'],
    cyan: str = defaultEmojis['Cyan'],
    blue: str = defaultEmojis['Blue'],
    new: Optional[str] = defaultEmojis['new'],
    waxing_crescent: Optional[str] = defaultEmojis['waxing_crescent'],
    first_quarter: Optional[str] = defaultEmojis['first_quarter'],
    waxing_gibbous: Optional[str] = defaultEmojis['waxing_gibbous'],
    full: Optional[str] = defaultEmojis['full'],
    waning_gibbous: Optional[str] = defaultEmojis['waning_gibbous'],
    third_quarter: Optional[str] = defaultEmojis['third_quarter'],
    waning_crescent: Optional[str] = defaultEmojis['waning_crescent'],
):
    invalidEmojis = []
    for emoji in (white, black, green, red, purple, yellow, cyan, blue, new, waxing_crescent,
                first_quarter, waxing_gibbous, full, waning_gibbous, third_quarter, waning_crescent):
        emoji = emoji.strip()
        if not isEmoji(emoji):
            invalidEmojis.append(emoji)
    if len(invalidEmojis) != 0:
        await interaction.response.send_message(
            content=f"**The following emojis are invalid: {invalidEmojis}**, please try again.",
            ephemeral=True,
        )
    else:
        userSettings = fetch_user_settings(interaction.user.id)
        if not userSettings:
            userSettings = newUserSettings(interaction.user.id, interaction.user.name)
        userSettings["emojis"] = {
            "White": white,
            "Black": black,
            "Green": green,
            "Red": red,
            "Purple": purple,
            "Yellow": yellow,
            "Cyan": cyan,
            "Blue": blue,
            "new": new,
            "waxing_crescent": waxing_crescent,
            "first_quarter": first_quarter,
            "waxing_gibbous": waxing_gibbous,
            "full": full,
            "waning_gibbous": waning_gibbous,
            "third_quarter": third_quarter,
            "waning_crescent": waning_crescent
        }
        emojis = userSettings["emojis"]
        update_user_settings(interaction.user.id, userSettings)
        await interaction.response.send_message(
            content="**Successfully set personal emojis!**"
            f"\n> `White           ` {emojis['White']}"
            f"\n> `Black           ` {emojis['Black']}"
            f"\n> `Green           ` {emojis['Green']}"
            f"\n> `Red             ` {emojis['Red']}"
            f"\n> `Purple          ` {emojis['Purple']}"
            f"\n> `Yellow          ` {emojis['Yellow']}"
            f"\n> `Cyan            ` {emojis['Cyan']}"
            f"\n> `Blue            ` {emojis['Blue']}"
            f"\n> `New Moon        ` {emojis['new']}"
            f"\n> `Waxing Crescent ` {emojis['waxing_crescent']}"
            f"\n> `First Quarter   ` {emojis['first_quarter']}"
            f"\n> `Waxing Gibbous  ` {emojis['waxing_gibbous']}"
            f"\n> `Full Moon       ` {emojis['full']}"
            f"\n> `Waning Gibbous  ` {emojis['waning_gibbous']}"
            f"\n> `Third Quarter   ` {emojis['third_quarter']}"
            f"\n> `Waning Crescent ` {emojis['waning_crescent']}",
            ephemeral=True,
        )

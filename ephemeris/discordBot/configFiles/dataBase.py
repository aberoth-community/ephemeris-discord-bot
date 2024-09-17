import json
from peewee import (
    Model,
    SqliteDatabase,
    CharField,
    IntegerField,
    TextField,
    ForeignKeyField,
)

# Connect to the SQLite database
db = SqliteDatabase('ephemeris\\discordBot\\configFiles\\bot_DB.db')

class BaseModel(Model):
    class Meta:
        database = db

class GuildSettings(BaseModel):
    guild_id = CharField(primary_key=True)
    guild_name = CharField()
    expiration = IntegerField()

class GuildEmojis(BaseModel):
    guild = ForeignKeyField(GuildSettings, backref='emojis', to_field='guild_id')
    emoji_name = CharField()
    emoji_value = TextField(null=True)

    class Meta:
        indexes = (
            (('guild', 'emoji_name'), True),  # Composite primary key
        )

class GuildChannelSettings(BaseModel):
    guild = ForeignKeyField(GuildSettings, backref='channels', to_field='guild_id')
    channel_id = CharField()
    use_emojis = IntegerField()
    allow_filters = IntegerField()
    whitelisted_users_only = IntegerField()
    filters = TextField(null=True)  # Store filters as serialized JSON string

    class Meta:
        primary_key = False
        indexes = (
            (('guild', 'channel_id'), True),  # Composite primary key
        )

class UserSettings(BaseModel):
    user_id = CharField(primary_key=True)
    username = CharField()
    expiration = IntegerField()

class UserEmojis(BaseModel):
    user = ForeignKeyField(UserSettings, backref='emojis', to_field='user_id')
    emoji_name = CharField()
    emoji_value = TextField(null=True)

    class Meta:
        indexes = (
            (('user', 'emoji_name'), True),  # Composite primary key
        )

# Create tables
db.connect()
db.create_tables([GuildSettings, GuildEmojis, GuildChannelSettings, UserSettings, UserEmojis])

# Helper Functions

def fetch_guild_settings(guild_id):
    """
    Fetch all settings for a specific guild, including emojis and channel filters.
    """
    guild = GuildSettings.get_or_none(GuildSettings.guild_id == guild_id)
    if not guild:
        return None

    # Fetch guild emojis
    emojis = {emoji.emoji_name: emoji.emoji_value for emoji in guild.emojis}

    # Fetch channel settings and filters
    channels = {}
    for channel in guild.channels:
        filters = json.loads(channel.filters) if channel.filters else []
        channel_data = {
            "useEmojis": channel.use_emojis,
            "allow_filters": channel.allow_filters,
            "whitelisted_users_only": channel.whitelisted_users_only,
            "filters": filters
        }
        channels[channel.channel_id] = channel_data

    return {
        "guild_id": guild.guild_id,
        "guild_name": guild.guild_name,
        "expiration": guild.expiration,
        "emojis": emojis,
        "channels": channels
    }

def update_guild_settings(guild_id, guild_data):
    """
    Update the settings for a specific guild and its channels.
    """
    guild_settings, created = GuildSettings.get_or_create(
        guild_id=guild_id,
        defaults=guild_data
    )

    if not created:
        guild_settings.guild_name = guild_data.get("guild", "unknown")
        guild_settings.expiration = guild_data.get("expiration", 0)
        guild_settings.save()

    # Update guild emojis
    for emoji_name, emoji_value in guild_data.get("emojis", {}).items():
        GuildEmojis.insert(
            guild=guild_settings,
            emoji_name=emoji_name,
            emoji_value=emoji_value
        ).on_conflict(
            conflict_target=(GuildEmojis.guild, GuildEmojis.emoji_name),
            preserve=(GuildEmojis.emoji_value,)
        ).execute()

    # Update guild channel settings and filters
    for channel_id, settings in guild_data.get("channels", {}).items():
        filters_json = json.dumps(settings.get("filters", []))
        GuildChannelSettings.insert(
            guild=guild_settings,
            channel_id=channel_id,
            use_emojis=settings.get("useEmojis", 0),
            allow_filters=settings.get("allow_filters", 0),
            whitelisted_users_only=settings.get("whitelisted_users_only", 0),
            filters=filters_json
        ).on_conflict(
            conflict_target=(GuildChannelSettings.guild, GuildChannelSettings.channel_id),
            preserve=(GuildChannelSettings.use_emojis, GuildChannelSettings.allow_filters,
                      GuildChannelSettings.whitelisted_users_only, GuildChannelSettings.filters)
        ).execute()

def fetch_user_settings(user_id):
    """
    Fetch all settings for a specific user, including emojis.
    """
    user = UserSettings.get_or_none(UserSettings.user_id == user_id)
    if not user:
        return None

    # Fetch user emojis
    emojis = {emoji.emoji_name: emoji.emoji_value for emoji in user.emojis}

    return {
        "user_id": user.user_id,
        "username": user.username,
        "expiration": user.expiration,
        "emojis": emojis
    }

def update_user_settings(user_id, user_data):
    """
    Update the settings for a specific user.
    """
    user_settings, created = UserSettings.get_or_create(
        user_id=user_id,
        defaults=user_data
    )
    if not created:
        user_settings.username = user_data.get("username", "unknown")
        user_settings.expiration = user_data.get("expiration", 0)
        user_settings.save()
        

    # Update user emojis
    for emoji_name, emoji_value in user_data.get("emojis", {}).items():
        UserEmojis.insert(
            user=user_settings,
            emoji_name=emoji_name,
            emoji_value=emoji_value
        ).on_conflict(
            conflict_target=(UserEmojis.user, UserEmojis.emoji_name),
            preserve=(UserEmojis.emoji_value,)
        ).execute()

def newGuildSettings(interaction, use_emojis=0, allow_filters=0, whitelisted_users_only=0) -> dict:
    try:
        return {
        'guild_id': interaction.guild_id,
        'guild_name': interaction.guild.name,
        'expiration': 0,
        'emojis': {},
        'channels': {} if interaction.channel_id is None else {
            interaction.channel_id: {
                'useEmojis': use_emojis,
                'allow_filters': allow_filters,
                'whitelisted_users_only': whitelisted_users_only,
                'filters': []
            }
        }
    }
    except:
        return {
        'guild_id': interaction['guild_id'],
        'guild_name': interaction['guild']['name'],
        'expiration': 0,
        'emojis': {},
        'channels': {} if interaction['channel_id'] is None else {
            interaction['channel_id']: {
                'useEmojis': use_emojis,
                'allow_filters': allow_filters,
                'whitelisted_users_only': whitelisted_users_only,
                'filters': []
            }
        }
    }

    
def newUserSettings(user_id, username, expiration=0) -> dict:
    return {
        'user_id': user_id,
        'username': username,
        'expiration': expiration,
        'emojis': {}
    }


if __name__ == "__main__":
    # Example usage

    # # Fetch settings for a guild
    # guild_id = "1116975978242134026"
    # guild_settings = fetch_guild_settings(guild_id)
    # print(f"Fetched guild settings for {guild_id}: {guild_settings}")

    # # Update settings for a guild
    # new_guild_data = newGuildSettings()
    # update_guild_settings(guild_id, new_guild_data)

    # # Fetch settings for a user
    # user_id = "109931759260430336"
    # user_settings = fetch_user_settings(user_id)
    # print(f"Fetched user settings for {user_id}: {user_settings}")

    # importing userWhiteList.json example
    userSettingsTransfer = {
        "109931759260430336": {
            "username": "figureskate",
            "expiration": -1
        },
    "440192160256491521": {
        "username": "bigdrew",
        "expiration": 0
    },
    "110109604423163904": {
        "username": "ashnel",
        "expiration": -1
    },
    "624193482424320000": {
        "username": "the_cthaeh",
        "expiration": -1
    },
    "245939106029240320": {
        "username": "canigetameow",
        "expiration": 1724612473
    },
    "1013019511554834452": {
        "username": "hitech1497",
        "expiration": 1722321788
    },
    "889298297498501151": {
        "username": ".luckyseven.",
        "expiration": 1728070376
    },
    "563525333257551902": {
        "username": "vanmorten",
        "expiration": 1723235990
    },
    "471797895440629767": {
        "username": "athenakazuo",
        "expiration": 1729914000
    },
    "188911699665879041": {
        "username": "joedread",
        "expiration": 1753248016
    },
    "339373441729953802": {
        "username": "joker10145",
        "expiration": 1727915206
    },
    "477287995158953995": {
        "username": "funtcase1",
        "expiration": 1727919551
    }
}
    
    #  if not userSettings:
    #             userSettings = newUserSettings(user_or_guild, username, expiration)
    #         else:
    #             userSettings['username'] = username
    #             userSettings['expiration'] = expiration
    #         update_user_settings(user_or_guild, userSettings)
    
    for user_id, s in userSettingsTransfer.items():
        #print(s["username"], s['expiration'])
        
        userData = newUserSettings(user_id=user_id, username=s['username'], expiration=s['expiration'])
        update_user_settings(user_id=user_id, user_data=userData)
        print(fetch_user_settings(user_id))
    
    
    # # Update settings for a user
    # new_user_data = {
    #     "username": "new_username",
    #     "expiration": 1,
    #     "emojis": {
    #         "emoji_white": "<white>",
    #         "emoji_black": "<:NewBlackOrb:123456789012345678>"
    #     }
    # }
    #update_user_settings(user_id, new_user_data)

    # user_settings = fetch_user_settings(user_id)
    # print(f"Fetched user settings for {user_id}: {user_settings}")

    db.close()


guildSettings = {1116975978242134026: {
    'guild_id': '1116975978242134026',
    'guild_name': 'New Ephemeris',
    'expiration': 0,
    'emojis': {
        'emoji_white': '<:NewWhiteOrb:123456789012345678>',
        'emoji_black': '<:NewBlackOrb:123456789012345678>',
        'emoji_green': '<:NewGreenOrb:123456789012345678>'
        }, 
    'channels': {
        '1123365067228991529': {
            'useEmojis': 1,
            'allow_filters': 1,
            'whitelisted_users_only': 1,
            'filters': ['filter_white', 'filter_black']
            }}}
}



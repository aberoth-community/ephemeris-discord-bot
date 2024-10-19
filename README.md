<div style="user-select: none;" align="center">
    
![Ephemeris Logo](https://github.com/user-attachments/assets/ff091f40-9b89-453d-9692-cf10c9500475)
    
</div>

<h1 align="center">Aberoth Ephemeris Discord Bot</h1>

<p>A Discord bot and user app that provides information about upcoming scroll events and moon phases within the MMORPG <a href="https://www.aberoth.com/">Aberoth</a>.
Built with the <a href="https://github.com/jvandag/aberoth-ephemeris">Aberoth Ephemeris</a> module&mdash;which is also developed by GitHub user <a href="https://github.com/jvandag">jvandag</a> under an MIT license&mdash;which can be installed separately from <a href="https://pypi.org/project/aberoth-ephemeris/">PyPI</a> or via a <a href="https://github.com/jvandag/aberoth-ephemeris/releases/">GitHub release</a> for use in other contexts.</p>

<div align="center">
<b>Example scroll event prediction menu:</b>
<br>

https://github.com/user-attachments/assets/483790cd-93aa-4255-9f74-f32fe008637f

</div>

## Installation & Running

If you're just looking to install [Aberoth Ephemeris](https://github.com/jvandag/aberoth-ephemeris)&mdash;the module that creates the prediction information&mdash;for your own project, you can install it with
```
pip install aberoth-ephemeris
```
Be sure to check the [Aberoth Ephemeris](https://github.com/jvandag/aberoth-ephemeris) repository for documentation on how to use the module for your own applications.

Otherwise, follow along to set up the Discord bot.

#### 1. Clone the Repository

```bash
git clone https://github.com/aberoth-community/ephemeris-discord-bot
```

#### 2. Initialize the Repository and Install Requirements

If you're using a bash terminal you can simply run

```bash
firstTimeSetup.sh
```

This will set up a venv and install the dependencies. Otherwise, optionally, you can configure a venv through other means and use

```bash
pip install .
```

#### 3. Configure .env File

See [example.env](example.env) for structure

#### 4. Configure Emojis

Change the emojis in [variables.py](ephemeris/discordBot/configFiles/variables.py) to your own variables that your bot instance can use. It is recommended to upload your emojis to the emojis section for your bot in the Discord developer dashboard.

#### 5. Run Bot

```bash
python -m ephemeris
```
#### Optional - 6.  Run web server in separate terminal to intake auto-calibration data from separate script

```bash
cd ephemeris/UpdateWebServer
waitress-serve --listen=0.0.0.0:5000 --threads=1 varUpdateWS:app
```

An excellent separate script that can be used to send live calibration data to the [Aberoth Ephemeris](https://github.com/jvandag/aberoth-ephemeris) module used for this bot is the [Ephemeris Overheard Hook](https://github.com/aberoth-community/ephemeris-overheard-hook/tree/main) made by GitHub user [jvandag](https://github.com/jvandag). It is built on GitHub user [ashnel3's](https://github.com/ashnel3) [Overheard Scrapper](https://github.com/aberoth-community/overheard) which scrapes the [Aberoth overheard page](https://aberoth.com/highscore/overheard.html) to find changes in scroll state, moon phase, time of day, and number of players online.

## Bot Usage and Commands

If you're hosting your own distribution of this bot, be sure to configure the `ownerID` and `disableWhitelisting` variables variables within the [variables.py](ephemeris/discordBot/configFiles/variables.py) file located in the config directory within the bot sub-directory. 

Only the specified owner may use the `/update_whitelist` command which can be used to add users and guilds/servers to the whitelist. By default, all users and guilds are not whitelisted and thus unable to use the bot or user installable. 

If `disableWhitelisting` is set to `True`, then all users will be able to utilize bot commands and menus as well as the user installable commands and menus regardless of the current whitelist settings.

<table >
<thead>
  <tr>
    <th>Command</th>
    <th>Description & Parameters</th>
  </tr>
</thead>
<tbody valign="top">
  <tr>
    <td>
      
  <b>`/update_whitelist`</b>

  </td>
    <td><p><b>Description:</b> Adds a specified guild or user to the whitelist, allowing them to use the bot while in whitelist mode.
    </p>
    <b>Parameters:</b>

  - `user_or_guild`: The ID of the user or guild for which the permissions are being updated.     
  - `type`: Indicates whether the passed in ID is a user or guild ID. Two options: user or guild.
  - `expiration`: The epoch timestamp in seconds at which the user's permissions will expire. An expiration time of `-1` indicates no expiration.
  </td>
    </tr>
    <tr>
    <td>

  <b>`/permissions`</b>  
    
  </td>
    <td><p><b>Description:</b> Responds with the time the command user's and&mdash;if used in a guild&mdash;the guild's permissions expire.<br><br>When disableWhitelisting is set to `False`, the permissions have no effect.
    </b></p>
    <b>Parameters:</b> None.
  </td>
  </tr>
  <tr>
    <td>
      
  <b>`/persistent_prediction_menu`</b>

  </td>
    <td><p><b>Description:</b> Creates an embed menu that allows users to request glows and darks for a selected day or range of days.<br><br>The command requires the user to be an admin within the guild it is used in. The menu has no expiration time and will persist between restarts of the bot. Bot responses are ephemeral.
    </p>
    <b>Parameters:</b>

  - `use_emojis`: Yes or No option. Yes indicates that the bot should use the emojis set for the command user&mdash;set via the <b>`/set_server_emojis`</b> command&mdash;in the place of the orb names.
  - `allow_filters`: Yes or No option. Yes indicates that the created menu should include a select menu that allows filtering of response content by orb. Note that filter changes from any user will update the filter settings for all users using the same menu instance. 
  - `whitelist_users_only` (optional): Yes or No option. Yes indicates that non-whitelisted users will be allowed to use the menu instance, even if they are unable to create an instance.
    </td>
  </tr>
  <tr>
    <td>
      
  <b>`/prediction_menu`</b>

  </td>
    <td><p><b>Description:</b> User App/Installable version only. Creates an embed menu that allows users to request glows and darks for a selected day or range of days.<br><br>The menu expires after five minutes. Filters are always allowed. Bot responses are NOT ephemeral.
    </p>
    <b>Parameters:</b>

  - `use_emojis`: Yes or No option. Yes indicates that the bot should use the emojis set for the guild, set via the <b>`/set_personal_emojis`</b> command, in the place of the orb names.
  - `whitelist_users_only` (optional): Yes or No option. Yes indicates that non-whitelisted users will be allowed to use the menu instance, even if they are unable to create an instance.
    </td>
  </tr>
  <tr>
    <td>
      
  <b>`/persistent_lunar_calendar`</b>

  </td>
    <td><p><b>Description:</b> Creates an embed menu that allows users to request start information on the current and upcoming moon phases.<br><br>The command requires the user to be an admin within the guild it is used in. The menu has no expiration time and will persist between restarts of the bot. Bot responses are ephemeral.
    </p>
    <b>Parameters:</b>

  - `user_set_emojis`: Yes or No option. Yes indicates that the bot should use the emojis set for the guild, set via the <b>`/set_server_emojis`</b> command, instead of the default global emojis.
  - `whitelist_users_only` (optional): Yes or No option. Yes indicates that non-whitelisted users will be allowed to use the menu instance, even if they are unable to create an instance.
    </td>
  </tr>
  <tr>
    <td>
      
  <b>`/lunar_calendar`</b>

  </td>
    <td><p><b>Description:</b> Creates an embed menu that allows users to request start information on the current and upcoming moon phases.<br><br>The command requires the user to be an admin within the guild it is used in. The menu has no expiration time and will persist between restarts of the bot. Bot responses are ephemeral.
    </p>
    <b>Parameters:</b>

  - `user_set_emojis`: Yes or No option. Yes indicates that the bot should use the emojis set for the user, set via the <b>`/set_user_emojis`</b> command, instead of the default global emojis.
  - `whitelisted_users_only` (optional): Yes or No option. Yes indicates that non-whitelisted users will be allowed to use the menu instance, even if they are unable to create an instance.
    </td>
  </tr>
  <tr>
    <td>
      
  <b>`/set_server_emojis`</b>

  </td>
    <td><p><b>Description:</b> Sets the emojis used by persistent menus within the server.<br><br>The command requires the user to be an admin within the guild it is used in.
    </p>
    <b>Parameters:</b>

  - `white`, `black`, `green`, `red`, `purple`, `yellow`, `cyan`, `blue` (optional): The emojis that will be used for the corresponding orbs. If no options are selected then a suitable default emoji is used.
  - `new`, `waxing_crescent`, `first_quarter`, `waxing_gibbous`, `full`, `waning_gibbous`, `third_quarter`, `waning_crescent` (optional): The emojis that will be used for the corresponding moon phases. If no options are selected then a suitable default emoji is used.
  </td>
  </tr>
    <tr>
    <td>
      
  <b>`/set_user_emojis`</b>

  </td>
    <td><p><b>Description:</b> Sets the emojis used by the command user's user app/installable menus.<br>
    </p>
    <b>Parameters:</b>

  - `white`, `black`, `green`, `red`, `purple`, `yellow`, `cyan`, `blue` (optional): The emojis that will be used for the corresponding orbs. If no options are selected then a suitable default emoji is used.
  - `new`, `waxing_crescent`, `first_quarter`, `waxing_gibbous`, `full`, `waning_gibbous`, `third_quarter`, `waning_crescent` (optional): The emojis that will be used for the corresponding moon phases. If no options are selected then a suitable default emoji is used.
    </td>
  </tr>

</tbody>
</table>

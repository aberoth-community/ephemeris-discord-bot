<div style="user-select: none;" align="center">
    
![Ephemeris Logo](https://github.com/user-attachments/assets/ff091f40-9b89-453d-9692-cf10c9500475)
    
</div>

<h1 align="center">Aberoth Ephemeris Discord Bot</h1>

<p>A Discord bot and user app that provides information about upcoming scroll events and moon phases.
Built with the <a href="https://github.com/jvandag/aberoth-ephemeris">Aberoth Ephemeris</a> module&mdash;which is also developed by github user <a href="https://github.com/jvandag">jvandag</a> using an MIT license&mdash;which can be installed separately from <a href="https://pypi.org/project/aberoth-ephemeris/">PyPi</a> or via a <a href="https://github.com/jvandag/aberoth-ephemeris/releases/">GitHub release</a> for use in other contexts.</p>

<div align="center">
<b>Example scroll event prediction menu:</b>
<br>

https://github.com/user-attachments/assets/9d1ac76d-a755-4b9b-b36b-f435c71fd833

</div>

## Installation & Running

If you're just looking to install [Aberoth Ephemeris](https://github.com/jvandag/aberoth-ephemeris)&mdash;the module that provides that creates the prediction information&mdash;for your own project, you can install it with
```
pip install aberoth-ephemeris
```
Be sure to check the [Aberoth Ephemeris](https://github.com/jvandag/aberoth-ephemeris) repository for documentation on how to the module for your own applications.

Otherwise, follow along to setup the Discord bot.

#### 1. Clone the Repository

```bash
git clone https://github.com/aberoth-community/ephemeris-discord-bot
```

#### 2. Initialize the Repository and Install Requirements

If you're using a bash terminal you can simply run

```bash
firstTimeSetup.sh
```

Which will set up a venv and install the dependencies. Otherwise, you can, optionally, configure a venv through other means and use

```bash
pip install .
```

#### 3. Configure .env File

See [example.env](example.env) for structure

#### 4. Run Bot

```bash
python -m ephemeris
```

<u>**Optional - Step Five:**</u> Run web server in separate terminal to intake auto-calibration data from separate script

```bash
cd ephemeris/UpdateWebServer
waitress-serve --listen=0.0.0.0:5000 --threads=1 varUpdateWS:app
```

An excellent separate script that can be used to send live calibration data to the [Aberoth Ephemeris](https://github.com/jvandag/aberoth-ephemeris) module that's that this bot utilizes is the [Ephemeris Overheard Hook](https://github.com/aberoth-community/ephemeris-overheard-hook/tree/main) by github user [jvandag](https://github.com/jvandag) and is built on github user [ashnel3's](https://github.com/ashnel3) [Overheard Scrapper](https://github.com/aberoth-community/overheard)

## Bot Usage and Commands

If you're hosting you're own distribution of this bot. Be sure to configure the `ownerID` and `disableWhitelisting` variables variables within the [variables.py](ephemeris/discordBot/configFiles/variables.py) file located in the config directory within the bot sub-directory. 

Only the specified owner may use the `/update_whitelist` command which can be used to add users and guilds/servers to the whitelist. By default, all users and guilds are not white listed and thus unable to use the bot or user installable. 

If `disableWhitelisting` is set to `True`, than all users will be able to utilize bot commands and menus as well as the user installable commands and menus regardless of the current whitelist settings.

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
    <td><p><b>Description:</b> Adds a specified guild or user to the whitelist allowing them to use the bot while in whitelist mode.
    </p>
    <b>Parameters:</b>

- `user_or_guild`: The id of the user or guild for which the permissions are being updated.     
- `type`: Indicates whether the passed in ID is a user or guild ID. Two options: user or guild.
- `expiration`: The epoch timestamp in seconds at which the user's permissions will expire. An expiration time of `-1` indicates no expiration.
</td>
  </tr>
  <tr>
    <td>add_events_by_link</td>
    <td>Creates a discord modal in which the user can paste links from an ISU event calendar page in order to add scheduled events to the current discord server. this interaction does not time out.</td>
  </tr>
  <tr>
    <td>add_calendar</td>
    <td>Prompts the user with an embed menu response—that only the user that initiated the command may interact with—to add a selected number of events to the current discord server from a selected ISU event calendar page.</td>
  </tr>
  <tr>
    <td>configure_auto_events</td>
    <td>Does the same thing as "add_calendar" command but also prompts the user to input a time interval for which the command will repeat, effectively updating events and adding new events when old events have passed. Multiple calendars can be set to automatically populate the server with events at once but the command must be ran for each calendar. However, if the same calendar is enabled more than once it will simply update the settings for that calendar. Settings will persist between bot restarts.<br><br><ins>In order to remove a calendar from the list of auto populating calendars the user must select the calendar via this command an then select "Disable Auto Events"</ins>.</td>
  </tr>
  <tr>
    <td>show_auto_config</td>
    <td>Shows the current settings for automatically updating events within the server it is used in.</td>
  </tr>
  <tr>
    <td>remove_events</td>
    <td>Removes scheduled events from the user specified within the discord command option. If no user is specified this command will remove all scheduled events.</td>
  </tr>
</tbody>
</table>
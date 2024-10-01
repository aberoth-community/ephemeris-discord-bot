<p align="center"><img src="assets/Ephemeris%20Logo.png" alt="Ephemeris Logo"></p>

<h1 align="center">Aberoth Ephemeris Discord Bot</h1>

<p>A Discord bot and user app that provides information about upcoming scroll events and moon phases.
Built with the <a href="https://github.com/jvandag/aberoth-ephemeris">Aberoth Ephemeris</a> module&mdash;which is also developed by github user <a href="https://github.com/jvandag">jvandag</a> using an MIT license&mdash;which can be installed separately from <a href="https://pypi.org/project/aberoth-ephemeris/">PyPi</a> or via a <a href="https://github.com/jvandag/aberoth-ephemeris/releases/">GitHub release</a> for use in other contexts.</p>

<div align="center">
<b>Example scroll event prediction menu:</b>
<br>
<video justify="center" width="540" height="540" controls>
  <source src="https://imgur.com/JNOXC9H.mp4" type="video/mp4">
</video>
</div>

## Installation & Running
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

If you're just looking to install the [Aberoth Ephemeris](https://github.com/jvandag/aberoth-ephemeris) module for your own projects, you can it install with
```
pip install aberoth-ephemeris
```
Be sure to check the [Aberoth Ephemeris](https://github.com/jvandag/aberoth-ephemeris) repository for documentation on how to the module for your own applications.

## Bot Commands and Usage


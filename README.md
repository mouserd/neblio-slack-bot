# Neblio Slack Bot

This project allows you to manage and query your Neblio Wallet installed on a Raspberry Pi via SlackBot.
Using the SlackBot you can perform the following functions:

* Determine if the Neblio daemon is running
* Determine if you Neblio wallet it unlocked for staking
* Lock and Unlock your Neblio wallet (see Advanced section for how to configure your wallet passphrase)
* Report on the number of tokens in your wallet
* Report information about the Neblio network, including: 
    * Number of connections
    * Staking weight
    * Estimated time to next stake
    * Wallet version
* Reboot your Raspberry Pi
* Report on the general health and well-being of your Raspberry Pi, including:
    * CPU, memory, and disk usage
    * Currently running processes
    * Top 5 processes using the most CPU or memory
    * Uptime
    * Current IP Address
    
<table><tr><td>
<img src="https://github.com/mouserd/neblio-slack-bot/blob/master/assets/neblio-slack-bot.gif" 
    title="Neblio Slack Bot" alt="Neblio Slack Bot" />
<table><tr><td>
## Pre-requisites

### Slack

This project requires a private Slack instance, after all, you don't really want 
someone else being able to control and view details about your raspberry Pi and Neblio wallet.  
To setup your private Slack, simply:

1. Follow the instructions to create your very own Slack workspace: [https://slack.com/create](https://slack.com/create)
2. Create a *Bot* for your new workspace using the Custom Integrations page: [https://slack.com/apps/manage/custom-integrations](https://slack.com/apps/manage/custom-integrations)
Take note of the *Username* and *API Token* of your bot, we'll need those later (see [Installation](#installation)).

### Raspberry Pi
This script uses Python, so you will need to ensure that this is available on your Raspberry Pi.  This was 
tested on a Raspberry Pi Zero W running Raspbian Stretch which came pre-installed with Python 2.7.

The script then also requires the Python PIP package manager:

```
sudo apt-get install python-pip
```

Using PIP you can then install the following required Python libraries:

```
sudo pip install slackweb
sudo pip install psutil
sudo pip install hurry.filesize
sudo pip install crypto
```

## Installation <a name="installation"></a>

Once you have satisfied the pre-requisites, simply copy the `neb-slack-bot.py` script
to your `pi` users home directory.  Edit the Python script and replace the `<<ADD YOUR SLACK BOT API TOKEN HERE>>` with the 
token you generated for your Slack workspace.  Replace the `<<ADD YOUR SLACK BOT USERNAME HERE>>` with the name you have given
to your Slack Bot.

To test that your Neblio Slack Bot is working, start the python script using:

```
python /home/pi/neb-slack-bot.py
```
Invite your slack bot to a channel in your Slack application:
```
/invite @your-neblio-slack-bot-name
```
If successful, you should be able to greet your neblio slack bot and get a response:
```
Hello @your-neblio-slack-bot-name
```

Once the above is working it's best to ensure that the python script is run on reboot of your Raspberry Pi.  To
do this, edit your cron using:

```crontab -e```

And add the following to the bottom of your cron:
```
@reboot /usr/bin/python /home/pi/scripts/neb-slack-bot.py 30 >> /var/log/neb/slack-bot.log 2>&1
```

## Advanced - Unlocking your wallet

TBC

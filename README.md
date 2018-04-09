
# Neblio Slack Bot

This project allows you to manage and query your [Neblio](https://nebl.io) Wallet installed on a Raspberry Pi via SlackBot.
Using the SlackBot you can perform the following functions:

* Determine if the Neblio daemon is running
* Determine if you Neblio wallet is unlocked for staking
* Lock and Unlock your Neblio wallet (see [Advanced](#advanced---unlocking-your-wallet) section for how to configure your wallet passphrase)
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
    
<table width="60%" align="center" padding=0 margin=0 id="neblio-slack-bot-demo">
    <tr>
        <td style="padding:0">
            <img src="https://github.com/mouserd/neblio-slack-bot/blob/master/assets/neblio-slack-bot.gif" 
                title="Neblio Slack Bot" alt="Neblio Slack Bot" width="520" />
        </td>
    </tr>
</table>

## Pre-requisites

### Slack

**UPDATE: 28/02/18:** This project no longer requires that you have a **PRIVATE** Slack workspace, instead you can now
restrict the slack channels and users that the Neblio Slack Bot can interact with. Choose one of the following two Slack setups that best meet your
needs.

#### Using a PRIVATE (dedicated) Slack workspace

This setup uses a **PRIVATE** Slack instance that only you will have access to.  This method is probably more secure as you will be the only
  person with access to the workspace, but it does require a bit more effort to register a new Slack workspace.  To setup your private Slack, simply:

1. Follow the instructions to create your very own Slack workspace: [https://slack.com/create](https://slack.com/create)
2. Create a **Bot** for your new workspace using the Custom Integrations page: [https://slack.com/apps/manage/custom-integrations](https://slack.com/apps/manage/custom-integrations)
You may have to search for "Bots" and then click "Add Configuration", this should then guide you through setting up a new bot. 
Take note of the **Username** and **API Token** of your bot, we'll need those later (see [Installation](#installation)).

#### Using a PUBLIC (shared) Slack workspace

If you already have your own Slack instance that you share with friends and family you can still integrate your Neblio Slack Bot simply by:

1. Create a **Bot** for your existing workspace using the Custom Integrations page: [https://slack.com/apps/manage/custom-integrations](https://slack.com/apps/manage/custom-integrations)
   You may have to search for "Bots" and then click "Add Configuration", this should then guide you through setting up a new bot. 
   Take note of the **Username** and **API Token** of your bot, we'll need those later (see [Installation](#installation)).
2. In the [Installation](#installation) steps you will need to copy the `config.py` from this repository onto your Raspberry Pi.  When you've copied
this file, edit the file changing the two lines below to only allow interaction with the bot to the channels
and/or users of your choosing:
```
ALLOWED_CHANNELS = ['my-private-channel']     # optional list of channels users can talk to your bot from
ALLOWED_USERS = ['my-slack-user-id']          # optional list of users who are permitted to talk to your bot
```

### Raspberry Pi
This project uses Python, so you will need to ensure that this is available on your Raspberry Pi.  This was 
tested on a Raspberry Pi Zero W running Raspbian Stretch which came pre-installed with Python 2.7.

In addition to Python, we will also need the Python PIP package manager so that we can install some required libraries:

```
sudo apt-get install python-pip
```

Once PIP is installed, install the following required Python libraries:

```
sudo pip install slackclient
sudo pip install psutil
sudo pip install hurry.filesize
sudo pip install crypto
```

We also need a utility called [jq](https://stedolan.github.io/jq/) which is command-line tool for parsing and querying json:

```
sudo apt-get install jq
```


## Installation 

Once you have satisfied all of the [pre-requisites](#pre-requisites), simply copy both the `neb-slack-bot.py` and `config.py` scripts
to your `pi` users home directory (`/home/pi`).  Edit the `config.py` python script and replace the `<<ADD YOUR SLACK BOT API TOKEN HERE>>` with the 
token you generated for your Slack workspace.  Replace the `<<ADD YOUR SLACK BOT USERNAME HERE>>` with the name you have given
to your Slack Bot.

To test that your Neblio Slack Bot is working, start the main python script by running:

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

And add the following to the bottom of the file, making sure to leave a blank line at the end:
```
@reboot /usr/bin/python /home/pi/scripts/neb-slack-bot.py 30 >> /var/log/neb/slack-bot.log 2>&1
```
Save and exit your cron (Ctrl+X if using nano).

## Advanced - Unlocking your wallet 

**The following section should be followed at your own risk.**  By following this process your neblio wallet 
passphrase will be written to a file on disk using a 2-way encryption library.  As such, if someone were 
to hack your Raspberry Pi they could quite easily gain access to your neblio wallet.  As such, if you
feel uncomfortable with this risk or your Raspberry Pi is exposed to the outside world then you should 
consider only unlocking your neblio wallet **manually**.

At the end of the day you should consider the risk here akin to having your Facebook or Twitter on your mobile phone.  
If someone was able to bypass your mobile phones password they would have access to similarly sensitive information.

Now, that the mandatory warning is out of the way, if you'd like to be able to unlock your wallet 
using the slack bot you need to:

1. Copy the `crypt-wallet-phasephrase.ph` to your Raspberry Pi's `/home/pi/` directory
2. Run the copied script as root using `sudo`, this will by write your encrypted passphrase using the salt `CRYPT_TOKEN` to path `CRYPT_PASSPHRASE_PATH` 
defined in the `config.py` - feel free to change these to suit your needs!
```
  sudo python /home/pi/crypt-wallet-passphrase.py
```
3. The script will prompt you to enter your wallet passphrase and will then write the encrypted result to the `CRYPT_PASSPHRASE_PATH` defined in
`config.py` (`/etc/neb.conf` by default) and will make it **read-only** to the `pi` user.
4. In slack, now ask your pi-bot to "unlock wallet" and with any luck you'll receive a confirmation response that your wallet was successfully unlocked

You can also lock your wallet at any time by telling your slack bot to "lock wallet". 

## Slack Bot Commands

The slack bot responds to messages based on some simple keyword pattern matching. You can put these keywords into sentences and questions 
or just issue the keywords alone.  The following are the keywords that the Neblio Slack Bot currently supports:

| Keyword(s)                  | Response                                                |
|-----------------------------|---------------------------------------------------------|
| `help`                      | List available commands                                 |
| `neblio running`            | Simply tells you if the neblio daemon is running or not | 
| `neblio active`             | Alias for `neblio running` | 
| `neblio info`               | Provides summary information including your staking status, staking weight, number of connections, etc |
| `staking`                   | Will let you know if you wallet is unlocked for staking |
| `unlock wallet`             | Unlocks your wallet if you've [set it up](#advanced---unlocking-your-wallet) |
| `lock wallet`               | Locks your wallet |
| `how many connections`      | Reports on the number of active connections on the neblio platform |
| `how many neblio`           | Reports the number of neblio tokens in your wallet |
| `how many nebbles`          | Alias for `how many neblio` |
| `cpu`                       | Reports the Pi's current CPU usage |
| `memory`                    | Reports the Pi's current memory usage |
| `ram`                       | Alias for `memory` |
| `disk`                      | Reports the Pi's disk space usage |
| `space`                     | Alias for `disk` |
| `processes most memory`     | Reports the top 5 processes based on memory usage |
| `processes most ram`        | Alias for `processes most memory` |
| `processes most cpu`        | Reports the top 5 processes based on CPU usage |
| `active processes`          | Reports the processes that are currently running |
| `ip address`                | Reports the Pi's current IP address |
| `uptime`                    | Reports the Pi's uptime since last reboot |
| `running`                   | Alias for `uptime` |
| `reboot`                    | Reboots the Pi (the bot should come online automatically providing you've setup the cron from the [installation](#installation) instructions) |
| `restart`                   | Alias for `reboot` |
| `hello`                     | Greet your Pi bot! |
| `bye`                       | Farewell your Pi bot! |
| `when moon`                 | Tells you when you should expect neblio to moon! |

## Donate / Tip :dollar:

:thumbsup: I hope you've found the **Neblio Slack Bot** useful!  If you'd like to donate or tip me to assist with the cost of building and maintaining 
this project then it would be much appreciated.

Neblio Address: ﻿`NbmG8tDpXVvjjac4UAmtsuitFAHf9YHcD3`

Ethereum Address: `0x6E644b360f314a50A8684a9E6676E13CbB702d1d` 


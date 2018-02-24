
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

This project requires a **PRIVATE** Slack instance, after all, **you really don't want 
someone else being able to control and view details about your raspberry Pi and Neblio wallet**.
  
To setup your private Slack, simply:

1. Follow the instructions to create your very own Slack workspace: [https://slack.com/create](https://slack.com/create)
2. Create a **Bot** for your new workspace using the Custom Integrations page: [https://slack.com/apps/manage/custom-integrations](https://slack.com/apps/manage/custom-integrations)
Take note of the **Username** and **API Token** of your bot, we'll need those later (see [Installation](#installation)).

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

<a name="installation"></a>
## Installation 

Once you have satisfied the pre-requisites, simply copy both the `neb-slack-bot.py` and `config.py` scripts
to your `pi` users home directory.  Edit the `config.py` python script and replace the `<<ADD YOUR SLACK BOT API TOKEN HERE>>` with the 
token you generated for your Slack workspace.  Replace the `<<ADD YOUR SLACK BOT USERNAME HERE>>` with the name you have given
to your Slack Bot.

To test that your Neblio Slack Bot is working, start the main python script using:

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

<a name="unlock-wallet"></a>
## Advanced - Unlocking your wallet 

**The following section should be followed at your own risk.**  By following this process your wallet 
key will be written to a file on disk using a 2-way encryption library.  As such, if someone were 
to hack your Raspberry Pi they could quite easily gain access to your neblio wallet.  As such, if you
feel uncomfortable with this risk or your Raspberry Pi is exposed to the outside world then you should 
consider only unlocking your neblio wallet **manually**.

At the end of the day you should consider the risk here akin to having your Facebook or Twitter on your mobile phone.  
If someone was able to bypass your phones' password they would have access to similarly sensitive information.

Now, that the mandatory warning is out of the way, if you'd like to be able to unlock your wallet 
using the slack bot you need to:

1. Copy the `crypt-wallet-phasephrase.ph` to your Raspberry Pi's `/home/pi/` directory
2. Run the copied script as root using `sudo`, this will by write your encrypted passphrase using the salt `CRYPT_TOKEN` to path `CRYPT_PASSPHRASE_PATH` 
(by default `/etc/neb.conf`) defined in the `config.py` - feel free to change these to suit your needs!
```
  sudo python /home/pi/crypt-wallet-passphrase.py
```
3. The script will prompt you to enter your wallet passphrase and will then write the encrypted result to the `CRYPT_PASSPHRASE_PATH` defined in
`config.py` (`/etc/neb.conf` by default) and will make it read-only to the `pi` user.
4. In slack, now ask your pi-bot to "unlock wallet" and with any luck you'll receive a confirmation response that your wallet was unlocked

You can also lock your wallet with a simple "lock wallet" command to your slack bot. 

## Slack Bot Commands

The slack bot responds to messages based on some simple keyword pattern matching. You can put these keywords into sentences and questions 
or just issue the keywords alone.  The following are the keywords that the neblio slack bot currently supports:

| Keyword(s)                  | Response                                                |
|-----------------------------|---------------------------------------------------------|
| `neblio running`            | Simply tells you if the neblio daemon is running or not | 
| `neblio active`             | Alias for `neblio running` | 
| `neblio info`               | Provides summary information including your staking status, staking weight, number of connections, etc |
| `staking`                   | Will let you know if you wallet is unlocked for staking |
| `unlock wallet`             | Unlocks your wallet if you've [set it up](#unlock-wallet) |
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
| `active processes`          | Reports the processes that are running now |
| `ip address`                | Reports the Pi's current ip address |
| `uptime`                    | Reports the Pi's up time |
| `running`                   | Alias for `uptime` |
| `reboot`                    | Reboots the Pi (the bot should come online automatically providing you've setup the cron from the [installation](#installation) instructions |
| `restart`                   | Alias for `reboot` |
| `hello`                     | Greet Pi bot! |
| `bye`                       | Farewell Pi bot! |
| `when moon`                 | Tells you when you should expect neblio to moon! |

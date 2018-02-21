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
    
## Pre-requisites

This script uses Python, so you will need to ensure that this is available on your Raspberry Pi.  This was 
tested on a Raspberry Pi Zero W running Raspbian Stretch which came pre-installed with Python 2.7.

The script then also requires installing PIP

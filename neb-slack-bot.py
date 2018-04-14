import json
import logging
import re
import subprocess
import traceback

import psutil
import sys
import time
from Crypto.Cipher import AES
from hurry.filesize import si
from hurry.filesize import size
from slackclient import SlackClient
from websocket import WebSocketConnectionClosedException

import config

logging.basicConfig(filename='%s/slack-bot.log' % config.LOG_PATH,
                    format='%(asctime)s: [%(levelname)s] %(message)s',
                    level=config.LOG_LEVEL)


def decryption():
    return AES.new(config.CRYPT_TOKEN, AES.MODE_CFB, 'This is an IV456')


def friendly_time(seconds, granularity=3):
    time_intervals = (
        ('weeks', 604800),
        ('days', 86400),
        ('hours', 3600),
        ('minutes', 60),
        ('seconds', 1),
    )

    result = []

    for name, count in time_intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])


def find_process_by_name(name):
    ls = []
    for p in psutil.process_iter(attrs=['name']):
        if p.info['name'] == name:
            ls.append(p)
    return ls


def get_processes_running_now():
    return [(p.pid, p.info['name']) for p in psutil.process_iter(attrs=['name', 'status']) if
            p.info['status'] == psutil.STATUS_RUNNING]


def get_processes_sorted_by_memory():
    return sorted(psutil.process_iter(attrs=['name', 'memory_percent']), key=lambda p: p.info['memory_percent'])


def get_processes_sorted_by_cpu():
    return sorted(psutil.process_iter(attrs=['name', 'cpu_times', 'cpu_percent']), key=lambda p: sum(p.info['cpu_times'][:2]))


def get_neblio_staking_info():
    return json.loads(subprocess.check_output("/home/pi/nebliod getstakinginfo | jq .", shell=True).strip())


def get_neblio_info():
    return json.loads(subprocess.check_output("/home/pi/nebliod getinfo | jq .", shell=True).strip())


def get_neblio_transactions():
    return json.loads(subprocess.check_output("/home/pi/nebliod listtransactions | jq .", shell=True).strip())


def get_neblio_addresses():
    neb_address_group = json.loads(subprocess.check_output("/home/pi/nebliod listaddressgroupings | jq .", shell=True).strip())
    neb_named_addresses = []
    for group in neb_address_group:
        neb_named_addresses.append(filter(lambda address_group: len(address_group) == 3, group)[0])
    return map(lambda account: ({'address': account[0], 'name': account[2]}), list(neb_named_addresses))


def neb_transaction_type(category):
    if category == "receive":
        return "Received"
    elif category == "send":
        return "Sent"
    elif category == "generate":
        return "Staked"
    else:
        return category


# When starting from reboot we need to delay as we might not have a network connection yet!
delay_startup = float(sys.argv[1]) if len(sys.argv) > 1 else 0
logging.info("Starting up in %d secs" % delay_startup)
time.sleep(delay_startup)


class NeblioSlackBot:
    slack_client = None
    slack_user_id = None
    connected = False
    allowed_users = []
    allowed_channels = []

    def __fetch_user_id(self, username):
        user_list = self.slack_client.api_call("users.list")
        for user in user_list.get('members'):
            if user.get('name') == username:
                return user.get('id')

    def __send_response(self, response_message, channel=config.DEFAULT_CHANNEL):
        self.slack_client.api_call("chat.postMessage", channel=channel, text=response_message, as_user=True)

    def __tagged_user_marker(self, user_id):
        return "<@%s>" % user_id

    def __sanitize_message(self, message):
        return message.replace(self.__tagged_user_marker(self.slack_user_id), '').strip()

    def __matches_pattern(self, pattern, message_text):
        return re.match(r'%s' % pattern, message_text, re.IGNORECASE)

    def __index_channels(self):
        result = {}
        channel_list = self.slack_client.api_call("channels.list").get('channels')
        private_list = self.slack_client.api_call("groups.list").get('groups')
        for channel in (channel_list + private_list):
            result[channel.get('name')] = channel.get('id')
        return result

    def __fetch_allowed_users(self):
        if config.ALLOWED_USERS:
            for f in config.ALLOWED_USERS:
                user_id = self.__fetch_user_id(f)
                if id:
                    self.allowed_users.append(user_id)

    def __fetch_allowed_channels(self):
        if config.ALLOWED_CHANNELS:
            channels = self.__index_channels()
            for f in config.ALLOWED_CHANNELS:
                channel_id = channels[f]
                if channel_id:
                    self.allowed_channels.append(channel_id)

    def connect(self):
        self.slack_client = SlackClient(config.SLACK_BOT_API_TOKEN)
        self.slack_user_id = self.__fetch_user_id(config.SLACK_BOT_USER_NAME)
        self.connected = self.slack_client.rtm_connect()

    def listen(self):
        self.__fetch_allowed_users()
        self.__fetch_allowed_channels()

        if self.connected:
            logging.info("Successfully connected to Slack. Waiting for messages...")
            self.__send_response("Heya! I'm back online, you should ask me some stuff...")

            while True:
                try:
                    for message in self.slack_client.rtm_read():

                        if 'text' in message and self.__tagged_user_marker(self.slack_user_id) in message['text']:

                            logging.info("Message received: %s" % message['text'])
                            message_text = self.__sanitize_message(message['text'])
                            message_channel = message['channel']
                            message_user = message['user']

                            if len(self.allowed_users) > 0 and message_user not in self.allowed_users:
                                logging.info("Un authorised user: %s" % message_user)
                                self.__send_response("Un-authorised User! Please do not talk to me. Scum.", message_channel)

                            elif len(self.allowed_channels) > 0 and message_channel not in self.allowed_channels:
                                logging.info("Un authorised channel: %s" % message_channel)
                                self.__send_response("Un-authorised Channel! Please do not talk to me here.", message_channel)

                            elif self.__matches_pattern('.*(neblio).*(info).*', message_text):
                                neb_info = get_neblio_info()
                                neb_staking_info = get_neblio_staking_info()
                                is_staking = neb_staking_info['staking'] is True
                                slack_response = "Neblio staking is currently: *%s*\n" \
                                                 "Your weight is: *%s*.\n" \
                                                 "Next stake is due in: *%s*\n" \
                                                 "Connections on the neblio network: *%s*\n" \
                                                 "You are running daemon version: *%s*" % (
                                                     "active" if is_staking else "inactive",
                                                     neb_staking_info['weight'],
                                                     friendly_time(neb_staking_info['expectedtime']) if is_staking else "N/A",
                                                     neb_info['connections'],
                                                     neb_info['version'])

                                self.__send_response(slack_response, message_channel)

                            elif self.__matches_pattern('.*(staking).*', message_text):
                                neb_staking_info = get_neblio_staking_info()
                                slack_response = "Yeah, I'm collecting all your nebbles!\n" \
                                                 "Your weight is *%s*. I estimate you'll get your next stake in about *%s*." \
                                                 % (neb_staking_info['weight'], friendly_time(neb_staking_info['expectedtime'])) \
                                    if neb_staking_info['staking'] is True \
                                    else "No, not right now."

                                self.__send_response(slack_response, message_channel)

                            elif self.__matches_pattern('.*(unlock).*(wallet).*', message_text):
                                with open(config.CRYPT_PASSPHRASE_PATH, 'r') as f:
                                    phrase = f.read()

                                self.__send_response("OK, trying to unlock your wallet now. This may take a moment... "
                                                     "please hold :telephone_receiver:", message['channel'])
                                subprocess.call("/home/pi/nebliod walletpassphrase %s 31000000 true" % decryption().decrypt(phrase),
                                                shell=True)
                                attempt = 0
                                while attempt < 10:
                                    neb_staking_info = get_neblio_staking_info()
                                    if neb_staking_info['staking'] is True:
                                        break
                                    attempt += 1
                                    time.sleep(1)

                                slack_response = "OK, I've unlocked your wallet and I'm now staking!\n" \
                                                 "Your weight is *%s*. I estimate you'll get your next stake in about *%s*." \
                                                 % (neb_staking_info['weight'], friendly_time(neb_staking_info['expectedtime'])) \
                                    if neb_staking_info['staking'] is True \
                                    else "Sorry, I wasn't able to unlock your wallet... you may have to take over.  " \
                                         "Make sure your wallet passphrase is correct and that the neblio daemon is running."

                                self.__send_response(slack_response, message_channel)

                            elif self.__matches_pattern('.*(lock).*(wallet).*', message_text):
                                subprocess.call("/home/pi/nebliod walletlock", shell=True)
                                self.__send_response("OK, I've locked your wallet and I'm no longer staking!\n", message_channel)

                            elif self.__matches_pattern('.*(how many).*(connections).*', message_text):
                                neb_info = get_neblio_info()
                                slack_response = "There are *%s* connections on the neblio network!\n" % neb_info['connections']

                                self.__send_response(slack_response, message_channel)

                            elif self.__matches_pattern('.*(how many).*(neblio|nebbles).*', message_text):
                                neb_info = get_neblio_info()
                                slack_response = "You've got *%s* nebbles in your wallet - sweet!\n" % neb_info['balance']

                                self.__send_response(slack_response, message_channel)

                            elif self.__matches_pattern('.*(neblio).*(address).*', message_text):
                                neb_addresses = get_neblio_addresses()
                                neb_addresses_detail = "".join("  %d. *%s*: %s\n    (http://explorer.nebl.io/address/%s)\n"
                                                               % (i + 1, address['name'], address['address'], address['address'])
                                                               for i, address in enumerate(neb_addresses))
                                slack_response = "Here are your neblio addresses:\n%s" % neb_addresses_detail
                                self.__send_response(slack_response, message_channel)

                            elif self.__matches_pattern('.*(neblio).*(transactions).*', message_text):
                                neb_addresses = get_neblio_transactions()
                                neb_transactions_detail = "".join(
                                    "  %s, %s: *%s* %s\n" % (time.strftime('%x', time.localtime(p['timereceived'])),
                                                             neb_transaction_type(p['category']),
                                                             p['amount'],
                                                             "(%s)" % p['account'] if p['account'] != '' else '') for p in neb_addresses)
                                slack_response = "Here are your last *%s* neblio transactions:\n%s" % \
                                                 (len(neb_addresses), neb_transactions_detail)
                                self.__send_response(slack_response, message_channel)

                            elif self.__matches_pattern('.*(neblio).*(running|active).*', message_text):
                                neb_is_running = len(find_process_by_name("nebliod")) > 0
                                slack_response = "Yep, it sure is!" if neb_is_running else "It doesn't appear to be."

                                self.__send_response(slack_response, message_channel)

                            elif self.__matches_pattern('.*(processes).*(most ram|most memory).*', message_text):
                                top_processes_mem = reversed([(p.pid, p.info) for p in get_processes_sorted_by_memory()][-5:])
                                slack_response = "These are my *top 5* processes using the most memory:\n%s" % "\n".join(
                                    "  %s. *%s*,  %s%% (pid: %s)" % (idx + 1, p[1]['name'], round(p[1]['memory_percent'], 2), p[0])
                                    for idx, p in enumerate(top_processes_mem)) \
                                    if top_processes_mem is not None \
                                    else "Well this is embarrassing... I couldn't work that out!"

                                self.__send_response(slack_response, message_channel)

                            elif self.__matches_pattern('.*(processes).*(most cpu).*', message_text):
                                top_processes_cpu = reversed([(p.pid, p.info, sum(p.info['cpu_times']))
                                                              for p in get_processes_sorted_by_cpu()][-5:])
                                slack_response = "These are my *top 5* processes using the most CPU:\n%s" % "\n" \
                                    .join("  %s. *%s*,  %s (pid: %s)" % (idx + 1, p[1]['name'],
                                                                         friendly_time(p[2]), p[0]) for idx, p in
                                          enumerate(top_processes_cpu)) \
                                    if top_processes_cpu is not None \
                                    else "Well this is embarrassing... I couldn't work that out!"

                                self.__send_response(slack_response, message_channel)

                            elif self.__matches_pattern('.*(active processes|running processes).*', message_text):
                                active_processes = get_processes_running_now()
                                slack_response = "I have these *active* processes running:\n%s" % "\n" \
                                    .join("  %s. *%s* (pid: %s)" % (idx + 1, p[1], p[0]) for idx, p in enumerate(active_processes)) \
                                    if active_processes is not None \
                                    else "There are no processes running at the moment."

                                self.__send_response(slack_response, message_channel)

                            elif self.__matches_pattern('.*(ip address|ipaddress).*', message_text):
                                ip_address = subprocess.check_output("hostname -I", shell=True).strip()

                                self.__send_response("My IP address is *%s*\n" % ip_address, message_channel)

                            elif self.__matches_pattern('.*(reboot|restart).*', message_text):
                                self.__send_response("Sure, rebooting myself now. BRB!", message_channel)
                                neb_staking_info = subprocess.call("sudo reboot", shell=True)

                            elif self.__matches_pattern('.*(running|uptime).*', message_text):
                                uptime = friendly_time(time.time() - psutil.boot_time())

                                self.__send_response("I've been up and running for *%s*." % uptime, message_channel)

                            elif self.__matches_pattern('.*(cpu).*', message_text):
                                cpu_pct = psutil.cpu_percent(interval=2, percpu=False)

                                self.__send_response("My CPU is at *%s%%*." % cpu_pct, message_channel)

                            elif self.__matches_pattern('.*(memory|ram).*', message_text):
                                mem = psutil.virtual_memory()
                                mem_pct = mem.percent
                                mem_detail = "Total: %s, available: %s, free: %s, used: %s" % (size(mem.total, system=si),
                                                                                               size(mem.available, system=si),
                                                                                               size(mem.free, system=si),
                                                                                               size(mem.used, system=si))

                                self.__send_response("I am using *%s%%* of available free memory.\n%s" % (mem_pct, mem_detail),
                                                     message_channel)

                            elif self.__matches_pattern('.*(disk|space).*', message_text):
                                disk = psutil.disk_usage('/')
                                disk_pct = disk.percent
                                disk_detail = "Total: %s, free: %s, used: %s" % (size(disk.total, system=si),
                                                                                 size(disk.free, system=si),
                                                                                 size(disk.used, system=si))

                                self.__send_response("My disk is at *%s%%* of capacity.\n%s" % (disk_pct, disk_detail), message_channel)

                            elif self.__matches_pattern('.*(hello|hey|hi|has joined the channel|has joined the group).*', message_text):
                                self.__send_response("Hellllo! And how are you?", message_channel)

                            elif self.__matches_pattern('.*(bye).*', message_text):
                                self.__send_response("See you!", message_channel)

                            elif self.__matches_pattern('.*(good).*', message_text):
                                self.__send_response("Sweet! Good and you?", message_channel)

                            elif self.__matches_pattern('.*(when moon).*', message_text):
                                self.__send_response("SOON! :rocket: :crescent_moon:", message_channel)

                            elif self.__matches_pattern('.*(help).*', message_text):
                                slack_response = "Available Commands:\n" \
                                                 "    > neblio info\n" \
                                                 "    > neblio active\n" \
                                                 "    > neblio addresses\n" \
                                                 "    > neblio transactions\n" \
                                                 "    > staking\n" \
                                                 "    > unlock wallet\n" \
                                                 "    > lock wallet\n" \
                                                 "    > how many connections\n" \
                                                 "    > how many neblio\n" \
                                                 "    > processes most ram\n" \
                                                 "    > processes most cpu\n" \
                                                 "    > active processes\n" \
                                                 "    > ip address\n" \
                                                 "    > uptime\n" \
                                                 "    > reboot\n" \
                                                 "    > cpu\n" \
                                                 "    > memory\n" \
                                                 "    > disk\n"
                                self.__send_response(slack_response, message_channel)

                            else:
                                self.__send_response("Ummm... sorry old mate, I don't know how to respond to that.", message_channel)

                except WebSocketConnectionClosedException:
                    logging.error(traceback.format_exc())
                    logging.warning("Connection lost. Attempting to reconnect in 30 seconds")
                    time.sleep(30)
                    self.__send_response("FYI - I'm back online after some momentary network connection problems!")
                except Exception as e:
                    logging.error(traceback.format_exc())
                    self.__send_response(":fire: :fire: :fire:\n :fire: Oh no!  I just crashed! (%s: %s)\n:fire: :fire: :fire:"
                                         % (e.__doc__, e.__cause__))

                time.sleep(1)


neblio_slack_bot = NeblioSlackBot()
neblio_slack_bot.connect()
neblio_slack_bot.listen()

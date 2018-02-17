import json
import logging
import psutil
import re
import subprocess
import sys
import time
from hurry.filesize import si
from hurry.filesize import size
from slackclient import SlackClient

logging.basicConfig(filename='/var/log/neb/slack-bot.log',
                    format='%(asctime)s: [%(levelname)s] %(message)s',
                    level=logging.INFO)

SLACK_BOT_USER_NAME = "pi-bot1"
SLACK_BOT_API_TOKEN = "xoxb-316184120996-JdkNoxj2EXusbapl8CQ0IKov"


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


def fetch_slack_user_id(username):
    user_list = slack_client.api_call("users.list")
    for user in user_list.get('members'):
        if user.get('name') == username:
            return user.get('id')


def send_slack_response(response_message):
    slack_client.api_call("chat.postMessage", channel=message['channel'], text=response_message, as_user=True)


def slack_message_tagged_user_marker(user_id):
    return "<@%s>" % user_id


def sanitize_slack_message_text():
    return message['text']. \
        replace(slack_message_tagged_user_marker(slack_user_id), ''). \
        strip()


# When starting from reboot we need to delay as we might not have a network connection yet!
delay_startup = float(sys.argv[1]) if len(sys.argv) > 1 else 0
logging.info("Starting up in %d secs" % delay_startup)
time.sleep(delay_startup)

slack_client = SlackClient(SLACK_BOT_API_TOKEN)
slack_user_id = fetch_slack_user_id(SLACK_BOT_USER_NAME)

# Initiate a slack connection and wait for messages
if slack_client.rtm_connect():
    logging.info('Successfully connected to Slack. Waiting for messages...')

    while True:
        for message in slack_client.rtm_read():
            if 'text' in message and slack_message_tagged_user_marker(slack_user_id) in message['text']:

                logging.info("Message received: %s" % message['text'])
                message_text = sanitize_slack_message_text()

                if re.match(r'.*(staking).*', message_text, re.IGNORECASE):
                    neb_staking_info = json.loads(subprocess.check_output("/home/pi/nebliod getstakinginfo | jq .", shell=True).strip())
                    slack_response = "Yeah, I'm collecting all your nebbles!\n" \
                                     "Your weight is *%s*. I estimate you'll get your next stake in about *%s*." \
                                     % (neb_staking_info['weight'], friendly_time(neb_staking_info['expectedtime'])) \
                        if neb_staking_info['staking'] == True else "No, not right now."

                    send_slack_response(slack_response)

                elif re.match(r'.*(neblio).*', message_text, re.IGNORECASE):
                    neb_is_running = len(find_process_by_name("nebliod")) > 0
                    slack_response = "It sure is!" if neb_is_running else "It doesn't appear to be."

                    send_slack_response(slack_response)

                elif re.match(r'.*(most ram|most memory).*', message_text, re.IGNORECASE):
                    top_processes_mem = reversed([(p.pid, p.info) for p in get_processes_sorted_by_memory()][-5:])
                    slack_response = "These are my *top 5* processes using the most memory:\n%s" % "\n".join(
                        "  %s. *%s*,  %s%% (pid: %s)" % (idx + 1, p[1]['name'], round(p[1]['memory_percent'], 2), p[0]) for idx, p in enumerate(top_processes_mem)) \
                        if top_processes_mem is not None else "Well this is embarrassing... I couldn't work that out!"

                    send_slack_response(slack_response)

                elif re.match(r'.*(most cpu).*', message_text, re.IGNORECASE):
                    top_processes_cpu = reversed([(p.pid, p.info, sum(p.info['cpu_times'])) for p in get_processes_sorted_by_cpu()][-5:])
                    slack_response = "These are my *top 5* processes using the most CPU:\n%s" % "\n"\
                        .join("  %s. *%s*,  %s (pid: %s)" % (idx + 1, p[1]['name'],
                                                             friendly_time(p[2]), p[0]) for idx, p in enumerate(top_processes_cpu)) \
                        if top_processes_cpu is not None else "Well this is embarrassing... I couldn't work that out!"

                    send_slack_response(slack_response)

                elif re.match(r'.*(active).*', message_text, re.IGNORECASE):
                    active_processes = get_processes_running_now()
                    slack_response = "I have these *active* processes running:\n%s" % "\n"\
                        .join("  %s. *%s* (pid: %s)" % (idx + 1, p[1], p[0]) for idx, p in enumerate(active_processes)) \
                        if active_processes is not None else "There are no processes running at the moment."

                    send_slack_response(slack_response)

                elif re.match(r'.*(running|uptime).*', message_text, re.IGNORECASE):
                    uptime = friendly_time(time.time() - psutil.boot_time())

                    send_slack_response("I've been up and running for *%s*." % uptime)

                elif re.match(r'.*(cpu).*', message_text, re.IGNORECASE):
                    cpu_pct = psutil.cpu_percent(interval=2, percpu=False)

                    send_slack_response("My CPU is at *%s%%*." % cpu_pct)

                elif re.match(r'.*(memory|ram).*', message_text, re.IGNORECASE):
                    mem = psutil.virtual_memory()
                    mem_pct = mem.percent
                    mem_detail = "Total: %s, available: %s, free: %s, used: %s" % (size(mem.total, system=si),
                                                                                   size(mem.available, system=si),
                                                                                   size(mem.free, system=si),
                                                                                   size(mem.used, system=si))

                    send_slack_response("My memory is *%s%%* free.\n%s" % (mem_pct, mem_detail))

                elif re.match(r'.*(disk|space).*', message_text, re.IGNORECASE):
                    disk = psutil.disk_usage('/')
                    disk_pct = disk.percent
                    disk_detail = "Total: %s, free: %s, used: %s" % (size(disk.total, system=si),
                                                                     size(disk.free, system=si),
                                                                     size(disk.used, system=si))

                    send_slack_response("My disk is at *%s%%* of capacity.\n%s" % (disk_pct, disk_detail))

                elif re.match(r'.*(hello|hey|hi).*', message_text, re.IGNORECASE):
                    send_slack_response("Hellllo! And how are you?")

                elif re.match(r'.*(bye).*', message_text, re.IGNORECASE):
                    send_slack_response("See you!")

                elif re.match(r'.*(good).*', message_text, re.IGNORECASE):
                    send_slack_response("Sweet! Good and you?")

                else:
                    send_slack_response("Ummm... sorry old mate, I don't know how to respond to that.")

        time.sleep(1)

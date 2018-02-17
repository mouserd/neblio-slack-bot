import re
import time
import psutil
import subprocess
from slackclient import SlackClient
from hurry.filesize import size
from hurry.filesize import si

SLACK_BOT_USER_ID = "pi-bot1"
SLACK_BOT_API_TOKEN = "xoxb-316184120996-JdkNoxj2EXusbapl8CQ0IKov"

intervals = (
    ('weeks', 604800),
    ('days', 86400),
    ('hours', 3600),
    ('minutes', 60),
    ('seconds', 1),
    )

def display_time(seconds, granularity=2):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])

def find_procs_by_name(name):
    ls = []
    for p in psutil.process_iter(attrs=['name']):
        if p.info['name'] == name:
            ls.append(p)
    return ls


def send_slack_response(response_message):
    slack_client.api_call(
        "chat.postMessage",
        channel=message['channel'],
        text=response_message,
        as_user=True)

def slack_message_tagged_user_marker(user_id):
    return "<@%s>" % user_id


slack_client = SlackClient(SLACK_BOT_API_TOKEN)

# Fetch your Bot's User ID
user_list = slack_client.api_call("users.list")
for user in user_list.get('members'):
    if user.get('name') == SLACK_BOT_USER_ID:
        slack_user_id = user.get('id')
        break

# Start connection
if slack_client.rtm_connect():
    print "Successfully connected to Slack. Waiting for messages..."

    while True:
        for message in slack_client.rtm_read():
            if 'text' in message and slack_message_tagged_user_marker(slack_user_id) in message['text']:

                # print "Message received: %s" % json.dumps(message, indent=2)
                print "Message received: %s" % message['text']

                message_text = message['text'].\
                    replace(slack_message_tagged_user_marker(slack_user_id), '').\
                    strip()
                print "Message text only: %s" % message_text
                print "User placeholder: %s" % slack_message_tagged_user_marker(slack_user_id)

                if re.match(r'.*(staking).*', message_text, re.IGNORECASE):
                    neb_is_staking = subprocess.check_output("/home/pi/nebliod getstakinginfo | jq .staking", shell=True).strip() == 'true'
                    neb_next_stake_time = int(subprocess.check_output("/home/pi/nebliod getstakinginfo | jq .expectedtime", shell=True).strip())
                    slack_response = "Yeah, I'm collecting all your nebbles! " \
                                     "I estimate you'll get your next stake in about *%s*." % display_time(neb_next_stake_time, 3) \
                        if neb_is_staking else "No, not right now."

                    send_slack_response(slack_response)

                elif re.match(r'.*(neblio).*', message_text, re.IGNORECASE):
                    neb_is_running = len(find_procs_by_name("nebliod")) > 0
                    slack_response = "It sure is!" if neb_is_running else "It doesn't appear to be."

                    send_slack_response(slack_response)

                elif re.match(r'.*(most ram|most memory).*', message_text, re.IGNORECASE):
                    top_processes_mem = reversed([(p.pid, p.info) for p in sorted(psutil.process_iter(attrs=['name', 'memory_percent']), key=lambda p: p.info['memory_percent'])][-5:])
                    slack_response = "These are my *top 5* processes using the most memory:\n%s" % "\n".join("  %s. *%s*,  %s%% (pid: %s)" % (idx+1, p[1]['name'], round(p[1]['memory_percent'], 2), p[0]) for idx, p in enumerate(top_processes_mem)) if top_processes_mem != None else "Well this is embarassing... I couldn't work that out!"

                    send_slack_response(slack_response)

                elif re.match(r'.*(most cpu).*', message_text, re.IGNORECASE):
                    top_processes_cpu = reversed([(p.pid, p.info, sum(p.info['cpu_times'])) for p in sorted(psutil.process_iter(attrs=['name', 'cpu_times', 'cpu_percent']), key=lambda p: sum(p.info['cpu_times'][:2]))][-5:])
                    slack_response = "These are my *top 5* processes using the most CPU:\n%s" % "\n".join("  %s. *%s*,  %s (pid: %s)" % (idx+1, p[1]['name'], display_time(p[2]), p[0]) for idx, p in enumerate(top_processes_cpu)) if top_processes_cpu != None else "Well this is embarassing... I couldn't work that out!"

                    send_slack_response(slack_response)

                elif re.match(r'.*(active).*', message_text, re.IGNORECASE):
                    active_processes = [(p.pid, p.info['name']) for p in psutil.process_iter(attrs=['name', 'status']) if p.info['status'] == psutil.STATUS_RUNNING]
                    slack_response = "I have these *active* processes running:\n%s" % "\n".join("  %s (pid: %s)" % (p[1], p[0]) for p in active_processes) if active_processes != None else "There are no processes running at the moment."

                    send_slack_response(slack_response)

                elif re.match(r'.*(running|uptime).*', message_text, re.IGNORECASE):
                    uptime = display_time(time.time() - psutil.boot_time())

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

                    send_slack_response("My disk space is *%s%%* free.\n%s" % (disk_pct, disk_detail))

                elif re.match(r'.*(hello|hey|hi).*', message_text, re.IGNORECASE):
                    send_slack_response("Hellllo! And how are you?")

                elif re.match(r'.*(good).*', message_text, re.IGNORECASE):
                    send_slack_response("Sweet! Good and you?")

                else:
                    send_slack_response("Ummm... sorry old mate, I don't know how to respond to that.")

        time.sleep(1)

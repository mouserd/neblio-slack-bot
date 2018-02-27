import logging

SLACK_BOT_USER_NAME = '<<ADD YOUR SLACK BOT USERNAME HERE>>'
SLACK_BOT_API_TOKEN = '<<ADD YOUR SLACK BOT API TOKEN HERE>>'

CRYPT_TOKEN = 'YourCryptToken12'  # Must be exactly 16 characters in length
CRYPT_PASSPHRASE_PATH = '/etc/neb.conf'

DEFAULT_CHANNEL = '#pi'     # default channel where messages such as errors, and online after reboot are sent to
ALLOWED_CHANNELS = []       # optional list of channels users can talk to your bot from
ALLOWED_USERS = []          # optional list of users who are permitted to talk to your bot

LOG_PATH = '/home/pi'       # default path where logs are written, path needs to be writable by the 'pi' user
LOG_LEVEL = logging.INFO

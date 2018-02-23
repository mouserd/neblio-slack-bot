import config
import getpass
import grp
import os
import pwd
from Crypto.Cipher import AES
from stat import S_IREAD

passphrase = getpass.getpass('Enter your wallet passphrase: ')

encryption_suite = AES.new(config.CRYPT_TOKEN, AES.MODE_CFB, 'This is an IV456')
cipher_text = encryption_suite.encrypt(passphrase)

f = open(config.CRYPT_PASSPHRASE_PATH, 'w')
f.write(cipher_text)
f.close()

os.chown(config.CRYPT_PASSPHRASE_PATH, pwd.getpwnam('pi').pw_uid, grp.getgrnam('pi').gr_gid)
os.chmod(config.CRYPT_PASSPHRASE_PATH, S_IREAD)

print('Your passphrase was encrypted and written to %s' % config.CRYPT_PASSPHRASE_PATH)

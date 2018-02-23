import config
import getpass
from Crypto.Cipher import AES

passphrase = getpass.getpass('Enter your wallet passphrase: ')

encryption_suite = AES.new(config.CRYPT_TOKEN, AES.MODE_CFB, 'This is an IV456')
cipher_text = encryption_suite.encrypt(passphrase)

f = open(config.CRYPT_PASSPHRASE_PATH, 'w')
f.write(cipher_text)
f.close()

print('Your passphrase was encrypted and written to %s' % config.CRYPT_PASSPHRASE_PATH)

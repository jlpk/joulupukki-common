from passlib.hash import pbkdf2_sha256
import random
import binascii
import os



from joulupukki.common.database import mongo

def encrypt_password(raw_password):
    return pbkdf2_sha256.encrypt(raw_password,
                                 rounds=200000,
                                 salt_size=16)


def check_password(raw_password, enc_password):
    """
    Returns a boolean of whether the raw_password was correct. Handles
    encryption formats behind the scenes.
    """
    return pbkdf2_sha256.verify(raw_password, enc_password)


def create_token():
    user = 'init'
    project = 'init'
    while user is not None and project is not None:
        token = binascii.hexlify(os.urandom(16))
        user = mongo.users.find_one({"token": token})
        project = mongo.projects.find_one({"token": token})
    return token

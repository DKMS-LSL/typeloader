import uuid
import hashlib


# Follows guidelines described here - https://crackstation.net/hashing-security.htm 

def hash_password(password):
	salt = uuid.uuid4().hex
	return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

def check_password(hashed_password, user_password):
	password, salt = hashed_password.split(':')
	return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest() 


	

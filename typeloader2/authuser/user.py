"""
Author : surendranath@dkms-lab.de
Create : 27.08.2018

Create, authenticate, modify and delete users
Data will be stored in a pickle whose location is set by parameter
"""

from pickle import dump, load
from .password import hash_password, check_password 


class User:

    def __init__(self, pickle_location = "user.pickle"):
        
        self.pickle_location = pickle_location
        # Try to load the pickle file, if one doesn't exist, create it
        try:
            credentials_file = open(self.pickle_location, "rb")
            self.all_credentials = load(credentials_file) 
            credentials_file.close()
        except (IOError, EOFError, FileNotFoundError):
            self.all_credentials = {}
            self.save_changes()

    def add_user(self, username, plaintext_password):

        if username in self.all_credentials: 
            raise Exception("User exists")
            return 

        password_hashstring = hash_password(plaintext_password)

        self.all_credentials[username] = password_hashstring

        self.save_changes()

        return

    def authenticate_user(self, username, plaintext_password):

        if (username in self.all_credentials) and \
                check_password(self.all_credentials[username], plaintext_password):
            return True
        else: 
            return False 

    def modify_user(self, username, new_plaintext_password):
        # Modify in this context is assumed to mean a password change 
        
        if username not in self.all_credentials:
            raise Exception("User does not exist")
            return
        self.delete_user(username)
        self.add_user(username, new_plaintext_password)
        self.save_changes()
        
        return 

    def delete_user(self, username): 

        if username not in self.all_credentials:
            raise Exception("User does not exist")
            return

        del(self.all_credentials[username])
        self.save_changes()

        return
    
    def save_changes(self):
        
        credentials_file = open(self.pickle_location, "wb") 
        dump(self.all_credentials, credentials_file)
        credentials_file.close()

        
    



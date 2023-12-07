import asyncio
from collections import namedtuple
from flask import make_response, jsonify
import json
import subprocess
import requests
import re

from threema_service import ThreemaService

class ThreemaController:
    def __init__(self):
        # Initialize ThreemaService with secrets
        identity, secret, private_key = self.__read_secrets('./secrets', '.threema_id', '.secret', '.private')
        self.threema_service = ThreemaService(identity, secret, private_key)

        self.secrets = self.Secrets(identity, secret, private_key)

        # Load Threema users
        self.users_json_path = 'threema_users.json'
        self.users = self.__load_users(self.users_json_path)
        self.url = 'https://msgapi.threema.ch'

    class Secrets:
        def __init__(self, identity, api_secret_key, private_key):
            self.identity = identity
            self.api_secret_key = api_secret_key
            self.private_key = private_key
    
    def __read_secrets(self, secrets_folder, id_file, secret_file, private_file):
        with open(f'{secrets_folder}/{id_file}', 'r') as id_f:
            identity = id_f.read()

        with open(f'{secrets_folder}/{secret_file}', 'r') as secret_f:
            secret = secret_f.read()

        with open(f'{secrets_folder}/{private_file}', 'r') as private_f:
            private = private_f.read()

        return identity, secret, private

    def __load_users(self, json_file_path):
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        return data.get('users', [])
    
    def get_recipient_info(self, recipient_type, params):
        if recipient_type == 'phone':
            return self.get_user_info('phone', params.get('to'))
        elif recipient_type == 'email':
            return self.get_user_info('email', params.get('to'))
        elif recipient_type == 'id':
            return self.get_user_info('id', params.get('to'))
        else:
            return None

    def get_new_user_id(self, key_type, key, params):
        if key_type == 'phone':
            lookup_type = 'phone'
        elif key_type == 'email':
            lookup_type = 'email'

        return requests.get(self.url + f'/lookup/{lookup_type}/{key}', params=params)

    def create_user(self, key_type, key):
        print(f'create user: {key_type} {key}', flush=True)
        params = {
            'from': self.secrets.identity,
            'secret': self.secrets.api_secret_key,
        }

        if key_type == 'id':
            id = key
        else:
            id_response = self.get_new_user_id(key_type, key, params)
            id = id_response.text.strip()
        
        if id:
            existing_user = next((user for user in self.users if user['id'] == id), None)
            if existing_user:
                # If user already exists, update phone or email if not present
                if key_type == 'phone':
                    existing_user['phone'] = key
                elif key_type == 'email':
                    existing_user['email'] = key
                return existing_user

            print(f'existing user: {existing_user}', flush=True)
            # If user does not exist, fetch the public key and create a new user
            public_key_response = requests.get(self.url + f'/pubkeys/{id}', params=params)
            print(f'public key response: {public_key_response}', flush=True)
            
            if public_key_response.status_code == 200:
                public_key = public_key_response.text.strip()
                
                new_user_info = {
                    'id': id,
                    'email': key if key_type == 'email' else '',
                    'phone': key if key_type == 'phone' else '',
                    'public_key': 'public:' + public_key
                }

                print(f'new user info: {new_user_info}', flush=True)
                return new_user_info
            
        return None

        


    def get_user_info(self, key_type, key):
        user_index = next((index for index, user in enumerate(self.users) if user[key_type] == key), None)
        print(f'user_index: {user_index}', flush=True)
        if user_index is not None:
            user = self.users[user_index]

            if not user['phone'] and key_type == 'phone':
                # If user exists but has no phone, update the phone
                user['phone'] = key
                self.save_users()

            elif not user['email'] and key_type == 'email':
                # If user exists but has no email, update the email
                user['email'] = key
                self.save_users()

            return user

        else:
            # If user does not exist, create a new one
            new_user = self.create_user(key_type, key)
            if new_user:
                self.users.append(new_user)
                self.save_users()
                return new_user

        return None
    
    def save_users(self):
        with open(self.users_json_path, 'w') as file:
            json.dump({'users': self.users}, file)


    def __get_recipient_type(self, recipient):
        phone_number_pattern = re.compile(r'^(\+\d{11}|\d{11})$')
        email_pattern = re.compile(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$')
        account_id_pattern = re.compile(r'^[a-zA-Z0-9]{8}$')

        # Check recipient against each pattern
        if phone_number_pattern.match(recipient):
            return 'phone'
        elif email_pattern.match(recipient):
            return 'email'
        elif account_id_pattern.match(recipient):
            return 'id'
        else:
            return 'unknown'


    def __send_e2e_message(self, from_id, user, message):
        if user == None:
            # TODO: change this return to false or false, message
            # The recipient corresponds to any known user
            error_response = make_response(jsonify({'status': 'Recipient not found.'}), 404)
            return error_response
        
        nonce, box = self.threema_service.nonce_box_from_command(
            message, 
            self.secrets.private_key,
            user['public_key']
        )

        params = {
            'from': from_id,
            'to': user['id'],
            'nonce': nonce,
            'box': box,
            'secret': self.secrets.api_secret_key
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "charset": "utf-8",
            "accept": "*/*"
        }

        print(f'params: {params}', flush=True)
        return requests.post(self.url + '/send_e2e', params=params, headers=headers)
 

    def send_e2e_message(self, from_id, recipientList, message):
        success_responses = []
        failure_recipients = []

        for recipient in recipientList:
            recipientType = self.__get_recipient_type(recipient)
            print(f'send_e2e_message -> recipientType: {recipientType}', flush=True)
            user = self.get_user_info(recipientType, recipient)
            print(f'send_e2e_message -> user: {user}', flush=True)

            response = self.__send_e2e_message(from_id, user, message)

            if response.status_code in {200, 201}:
                success_responses.append({'recipient': recipient, 'status_message': 'Message successfully sent.', 'status_code': response.status_code})
            elif response.status_code == 404:
                failure_recipients.append({'recipient': recipient, 'status_message': 'User does not exist.', 'status_code': response.status_code})
            else:
                failure_recipients.append({'recipient': recipient, 'status_message': 'Message not sent.', 'status_code': response.status_code})

        return success_responses, failure_recipients
            

        



    # async def send_message(self, from_id, to_id, message):
    #     # For now the from parameter is not used

    #     # Find the public key based on the 'to_id'
    #     recipient = next((user for user in self.users if user.id == to_id), None)

    #     if recipient:
    #         print(f'recipient public key: {recipient.public_key}', flush=True)
    #         # Use ThreemaService to send the message
    #         await self.threema_service.send_message(to_id, message, recipient.public_key)
    #     else:
    #         print(f"Recipient with ID {to_id} not found.")
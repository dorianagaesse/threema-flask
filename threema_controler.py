import asyncio
from collections import namedtuple
import json

from threema_service import ThreemaService

class ThreemaController:
    def __init__(self):
        # Initialize ThreemaService with secrets
        identity, secret, private_key = self.read_secrets('./secrets', '.threema_id', '.secret', '.private')
        self.threema_service = ThreemaService(identity, secret, private_key)

        # Load Threema users
        self.users = self.get_threema_users('threema_users.json')
    
    def read_secrets(self, secrets_folder, id_file, secret_file, private_file):
        with open(f'{secrets_folder}/{id_file}', 'r') as id_f:
            identity = id_f.read()

        with open(f'{secrets_folder}/{secret_file}', 'r') as secret_f:
            secret = secret_f.read()

        with open(f'{secrets_folder}/{private_file}', 'r') as private_f:
            private = private_f.read()

        return identity, secret, private

    def get_threema_users(self, json_file_path):
        User = namedtuple('User', ['id', 'email', 'phone', 'public_key'])
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        return [User(**user) for user in data.get('users', [])]
    
    async def send_message(self, from_id, to_id, message):
        # For now the from parameter is not used

        # Find the public key based on the 'to_id'
        recipient = next((user for user in self.users if user.id == to_id), None)

        if recipient:
            print(f'recipient public key: {recipient.public_key}', flush=True)
            # Use ThreemaService to send the message
            await self.threema_service.send_message(to_id, message, recipient.public_key)
        else:
            print(f"Recipient with ID {to_id} not found.")
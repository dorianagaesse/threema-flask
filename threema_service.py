from threema.gateway import Connection, GatewayError
from threema.gateway.e2e import TextMessage
import subprocess

class ThreemaService:
    def __init__(self, identity, secret, private_key):
        self.connection = Connection(
            identity=identity,
            secret=secret,
            key=private_key
        )
    
    def nonce_box_from_command(self, message, private_key, public_key):
        command = f'echo "{message}" | threema-gateway encrypt {private_key} {public_key}'
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        nonce_and_box = result.stdout.split('\n')

        filtered_nonce_box = list(filter(None, nonce_and_box))

        if len(filtered_nonce_box) == 2:
            nonce, box = filtered_nonce_box
            return nonce, box
        else:
            # Handle the case where the output does not contain both nonce and box
            return None, None
    
    
    async def __do_send(self, to_id, text, public_key):
        message = TextMessage(
            connection=self.connection,
            to_id=to_id,
            key=public_key,
            text=text
        )
        return await message.send()

    async def send_message(self, to, message, public_key):
        print(f'threema_service.send_message: {to}, {message}')
        try:
            async with self.connection:
                await self.__do_send(to, message, public_key)
        except GatewayError as e:
            print('Error while sending message:', e, flush=True)
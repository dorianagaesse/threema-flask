from threema.gateway import Connection, GatewayError
from threema.gateway.e2e import TextMessage

class ThreemaService:
    def __init__(self, identity, secret, private_key):
        self.connection = Connection(
            identity=identity,
            secret=secret,
            key=private_key
        )
    
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
import secrets
import asyncio
import logbook
import logbook.more
# Example: https://github.com/threema-ch/threema-msgapi-sdk-python/blob/master/examples/e2e.py
# Also have the _blocking file without async await
from threema.gateway import (
    Connection,
    GatewayError,
    util,
)
from threema.gateway.e2e import (
    FileMessage,
    ImageMessage,
    TextMessage,
    VideoMessage,
)
from collections import namedtuple

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers="*")

@app.route('/send_blocking', methods=['POST'])
def send_message():
    identity, secret, private = read_secrets('./secrets', '.threema_id', '.secret', '.private')
    # print(identity, secret, private)

    connection = Connection(
        # identity='*YOUR_GATEWAY_THREEMA_ID',
        identity=identity,
        # secret='YOUR_GATEWAY_THREEMA_ID_SECRET',
        secret=secret,
        # key='private:YOUR_PRIVATE_KEY',
        key=private,
        blocking=True,
    )

    try:
        with connection:
            send_cached_key_blocking(connection, 'MB4UKY9B', 'public:9bef1d23f8e1915481d63c076a45036ea640c802d8a072bb3381dd9ff031c321', 'Python test')
            return jsonify({'status': 'ok'}), 200
    except GatewayError as exc:
        print('Error:', exc)
        return jsonify({'status': 'error'}), 500


def send_cached_key_blocking(connection, to_id, to_public_key, text):
    """
    Send a message to a specific Threema ID with an already cached
    public key of that recipient.
    """
    message = TextMessage(
        connection=connection,
        # to_id='ECHOECHO',
        to_id=to_id,
        # key='public:4a6a1b34dcef15d43cb74de2fd36091be99fbbaf126d099d47d83d919712c72b',
        key=to_public_key,
        # text='私はガラスを食べられます。それは私を傷つけません。'
        text=text
    )
    return message.send()

def read_secrets(secrets_folder, id_file, secret_file, private_file):

    with open(f'{secrets_folder}/{id_file}', 'r') as id_f:
        id = id_f.read()
    
    with open(f'{secrets_folder}/{secret_file}', 'r') as secret_f:
        secret = secret_f.read()
    
    with open(f'{secrets_folder}/{private_file}', 'r') as private_f:
        private = private_f.read()
    
    return id, secret, private



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
from flask import Flask, jsonify, request
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
import asyncio
import requests
import secrets
from nacl.public import Box, PrivateKey, PublicKey
import base64
import subprocess

from threema_controler import ThreemaController

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers="*")

threema_controller = ThreemaController()

executor = ThreadPoolExecutor(max_workers=1)

def hex_to_bytes(key):
    return bytes.fromhex(key)

def hex_string_to_str(hex_string):
    # Convert the hexadecimal string to bytes
    byte_data = bytes.fromhex(hex_string)

    # Decode the bytes into a string (assuming UTF-8 encoding)
    string_data = byte_data.decode('utf-8')

    return string_data

def generate_nonce():
    return secrets.token_hex(24)

def generate_box(nonce, message, sender_private_key, receiver_public_key):
    nonce = hex_to_bytes(nonce)
    private_key_bytes = PrivateKey(hex_to_bytes(sender_private_key))
    public_key_bytes = PublicKey(hex_to_bytes(receiver_public_key))
    box = Box(private_key_bytes, public_key_bytes)
    print(f'message: {message}', flush=True)
    print(f'nonce: {nonce}', flush=True)
    encrypted_message = box.encrypt(message.encode('utf-8'), nonce)
    print(f'encrypted message: {encrypted_message}')

    return encrypted_message.hex()



def nonce_box_from_command(message, private_key, public_key):
    command = f'echo "{message}" | threema-gateway encrypt {private_key} {public_key}'
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    nonce_and_box = result.stdout.split('\n')
    print(f'command output: {type(nonce_and_box)}', flush=True)
    print(f'command output: {nonce_and_box}', flush=True)
    print(f'transformed: {tuple(filter(None, nonce_and_box))}', flush=True)
    return tuple(filter(None, nonce_and_box))

def command_message(message):
    private_key = 'private:33a5e5065124cf6ce4b5add58f8ff2acf8614fbfedd9eae7eb2db4824230e98d'
    public_key = 'public:b8d6c992c5dcca27ef6fdaf13f1a8135d76c9f297b7fce2d6b5563cad52b6474'
    nonce_box = nonce_box_from_command(message, private_key, public_key)

    url = "https://msgapi.threema.ch/send_e2e"

    params = {
        'from': '*IPLIS00',
        'to': 'WBUFV2E5',
        'nonce': nonce_box[0],
        'box': nonce_box[1],
        'secret': 'mMlhsxWevz9wbOXT'
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "charset": "utf-8",
        "accept": "*/*"
    }

    print(f'params: {params}', flush=True)
    return requests.post(url, params=params, headers=headers)


def hardcoded_message():
    url = "https://msgapi.threema.ch/send_e2e"
    params = {
        "from": "*IPLIS00",
        "to": "MB4UKY9B",
        "nonce": "94a3b08ad5e233337ddf9e517f9bc7277e4f675973a9c55c",
        "box": "bf5fbe30592610706a64da7ceec701892600b6f177f41bd2b6aca5a5d9e78cba73f2670cbbafb492d1fd18de615299b678a1748c901c2bbd1f38acf95d02e1f98220a973ad7553ad47da796feb390b376e30fd89298823a3cea539ad02ea600fb6e4557954c18584035ce749c6bc6416e5d559e9de629e7763bfe3e6c0d40c",
        "secret": "mMlhsxWevz9wbOXT"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "charset": "utf-8",
        "accept": "*/*"
    }

    return requests.post(url, params=params, headers=headers)

def generated_message(message):
    nonce = generate_nonce()
    private_key = '33a5e5065124cf6ce4b5add58f8ff2acf8614fbfedd9eae7eb2db4824230e98d'
    public_key = '9bef1d23f8e1915481d63c076a45036ea640c802d8a072bb3381dd9ff031c321'
    encrypted_box = generate_box(nonce, message, private_key, public_key)

    url = "https://msgapi.threema.ch/send_e2e"

    params = {
        'from': '*IPLIS00',
        'to': 'MB4UKY9B',
        'nonce': nonce,
        'box': encrypted_box,
        'secret': 'mMlhsxWevz9wbOXT'
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "charset": "utf-8",
        "accept": "*/*"
    }

    print(f'params: {params}', flush=True)
    return requests.post(url, params=params, headers=headers)



@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/test', methods=['GET'])
def test_route():
    return jsonify({'test': 'test'}), 200

# Does not work due to async nature of the sdk that is not compatible with Flask
@app.route('/send_message_sdk', methods=['POST'])
def send_message_sdk():
    data = request.json
    
    _from = data.get('from')
    _to = data.get('to')
    _message = data.get('message')

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(threema_controller.send_message(_from, _to, _message))

    return jsonify({'status': 'Message sent successfully.'}), 200

@app.route('/send_message', methods=['POST'])
def send_message():
    params = request.json
    message = params.get('message')
    print(f'message: {message}', flush=True)

    # response = hardcoded_message()
    # response = generated_message(message)
    response = command_message(message)

    print("Response Status Code:", response.status_code, flush=True)
    print("Response Content:", response.text, flush=True)

    if response.status_code in {200, 201}:
        return jsonify({'status': 'Message sent successfully.'}), 200
    else:
        return jsonify({'status': 'Message sending failed.'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
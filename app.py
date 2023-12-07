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

# WARNING: Does not work due to async nature of the sdk that is not compatible with Flask
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

@app.route('/send_e2e_message', methods=['POST'])
def send_e2e_message():
    params = request.json

    _from = params.get('from')
    recipientList = params.get('to').split(',')
    message = params.get('message')

    success_recipients, failed_recipients = threema_controller.send_e2e_message(_from, recipientList, message)
    
    print(f'success recipients: {success_recipients}', flush=True)
    print(f'failed recipients: {len(failed_recipients)} {failed_recipients}', flush=True)
    print(f'recipientList: {len(recipientList)} {recipientList}', flush=True)

    if not failed_recipients:
        # Message successfully sent to all recipients -> 200
        return jsonify({'status': 'Message sent successfully.'}), 200
    elif len(failed_recipients) > 0 and len(failed_recipients) < len(recipientList):
        # Message partially sent to some recipients -> 207
        recipients = [recipient['recipient'] for recipient in failed_recipients]
        return jsonify({
            'status': f'Message not sent to {", ".join(recipients)}',
            'failed_recipients': failed_recipients,
            'success_recipients': success_recipients
            }), 207
    elif len(failed_recipients) == len(recipientList):
        # Message not sent to any recipients -> 404
        return jsonify({
            'status': 'Message not sent to any recipients: recipients not found.',
            'failed_recipients': failed_recipients
            }), 404
    else:
        return jsonify({
            'status_message': 'Error while sending the message',
            'failed_recipients': failed_recipients
            }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
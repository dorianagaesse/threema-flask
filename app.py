from flask import Flask, jsonify, request
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
import asyncio

from threema_controler import ThreemaController

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers="*")

threema_controller = ThreemaController()

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/test', methods=['GET'])
def test_route():
    return jsonify({'test': 'test'}), 200

@app.route('/send_message', methods=['POST'])
async def send_message():
    data = request.json
    
    _from = data.get('from')
    _to = data.get('to')
    _message = data.get('message')

    await threema_controller.send_message(_from, _to, _message)

    return jsonify({'status': 'Message sent successfully.'}), 200




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

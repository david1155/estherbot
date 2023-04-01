from flask import Flask, render_template, request, jsonify, redirect
from collections import defaultdict
import requests
import json
import sseclient
import os
import threading
from flask_socketio import SocketIO, emit, join_room
import uuid
import logging
import time
import queue

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if os.getenv('SYSTEM_CONTENT'):
    syscont = os.getenv('SYSTEM_CONTENT')
else:
    syscont = ""

if os.getenv('TEMPERATURE'):
    temperature = float(os.getenv('TEMPERATURE'))
else:
    temperature = 0.75

if os.getenv('MODEL'):
    model = os.getenv('MODEL')
else:
    model = "gpt-4"

message_queues = {}

latest_user_input_id = None

# Modified function to use message queues
def performRequestWithStreaming(user_input, user_uuid, user_input_id):
    global latest_user_input_id
    global message_queues
    # Add the new message to the back of the message queue for the user UUID
    message_queues[user_uuid].put({"role": "user", "content": user_input})
    reqUrl = 'https://api.openai.com/v1/chat/completions'
    reqHeaders = {
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY']
    }

    MAX_RETRIES = 5
    retry_count = 0

    while latest_user_input_id == user_input_id and retry_count < MAX_RETRIES:
        try:
            # Get a list of messages in the message queue for the user UUID
            user_messages = list(message_queues[user_uuid].queue)
            # Construct the request body using the list of messages
            reqBody = {
                "model": model,
                "messages": user_messages,
                "temperature": temperature,
                "stream": True,
            }
            # Send the request to the OpenAI API
            request = requests.post(reqUrl, stream=True,
                                    headers=reqHeaders, json=reqBody, timeout=120)
            client = sseclient.SSEClient(request)
            response = ""
            for event in client.events():
                if (
                    event.data != '[DONE]'
                    and 'content' in json.loads(event.data)['choices'][0]['delta']
                ):
                    content = json.loads(event.data)[
                        'choices'][0]['delta']['content']
                    response += content
                    if latest_user_input_id != user_input_id:
                        break
                    socketio.emit('assistant_response', {'content': content}, room=user_uuid)
            # Add the response to the back of the message queue for the user UUID
            message_queues[user_uuid].put({"role": "assistant", "content": response})
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            logger.error(f"Exception occurred: {e}")
            retry_count += 1
            backoff_time = 2 ** retry_count
            logger.info(f"Retrying in {backoff_time} seconds...")
            time.sleep(backoff_time)
            continue
        break

@socketio.on('join')
def on_join(data):
    user_uuid = data['user_uuid']
    join_room(user_uuid)
    # Create a new message queue for the user UUID
    message_queues[user_uuid] = queue.Queue()
    # Add a system message to the front of the message queue for the user UUID
    message_queues[user_uuid].put({"role": "system", "content": syscont})

@app.route('/')
def main():
    user_uuid = str(uuid.uuid4())
    logger.info(f"New user_uuid: {user_uuid}")
    logger.info(f"HTTP Headers: {request.headers}")
    return redirect(f'/{user_uuid}')

@app.route('/<user_uuid>')
def index(user_uuid):
    return render_template('index.html', user_uuid=user_uuid)

@app.route('/ask', methods=['POST'])
def ask():
    global latest_user_input_id
    user_input = request.form['user_input']
    user_uuid = request.form['user_uuid']
    user_input_id = uuid.uuid4()
    latest_user_input_id = user_input_id
    threading.Thread(target=performRequestWithStreaming,
                     args=(user_input, user_uuid, user_input_id)).start()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
else:
    app = app


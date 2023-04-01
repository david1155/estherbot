from flask import Flask, render_template, request, jsonify, redirect
from collections import defaultdict
import requests
import json
import sseclient
import os
import threading
from flask_socketio import SocketIO, emit
import uuid
import logging
import time

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

messages = defaultdict(lambda: [{"role": "system", "content": syscont}])

latest_user_input_id = None

def performRequestWithStreaming(user_input, user_uuid, user_input_id):
    global latest_user_input_id
    global messages
    if user_uuid not in messages:
        messages[user_uuid] = [{"role": "system", "content": syscont}]
    user_messages = messages[user_uuid]
    user_messages.append({"role": "user", "content": user_input})
    reqUrl = 'https://api.openai.com/v1/chat/completions'
    reqHeaders = {
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY']
    }
    reqBody = {
        "model": model,
        "messages": user_messages,
        "temperature": temperature,
        "stream": True,
    }

    MAX_RETRIES = 5
    retry_count = 0

    while latest_user_input_id == user_input_id and retry_count < MAX_RETRIES:
        try:
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
                    socketio.emit('assistant_response', {'content': content})
            messages[user_uuid].append({"role": "assistant", "content": response})
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            logger.error(f"Exception occurred: {e}")
            retry_count += 1
            backoff_time = 2 ** retry_count
            logger.info(f"Retrying in {backoff_time} seconds...")
            time.sleep(backoff_time)
            continue
        break

@app.route('/')
def main():
    user_uuid = str(uuid.uuid4())
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

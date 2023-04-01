from flask import Flask, render_template, request, jsonify
import requests
import json
import sseclient
import os
import threading
from flask_socketio import SocketIO, emit
import uuid

app = Flask(__name__)
socketio = SocketIO(app)

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

messages = [
    {"role": "system", "content": syscont},
]

latest_user_input_id = None


def performRequestWithStreaming(user_input, user_input_id):
    global latest_user_input_id
    messages.append({"role": "user", "content": user_input})
    reqUrl = 'https://api.openai.com/v1/chat/completions'
    reqHeaders = {
        'Accept': 'text/event-stream',
        'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY']
    }
    reqBody = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    request = requests.post(reqUrl, stream=True,
                            headers=reqHeaders, json=reqBody)
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
    messages.append({"role": "assistant", "content": response})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ask', methods=['POST'])
def ask():
    global latest_user_input_id
    user_input = request.form['user_input']
    user_input_id = uuid.uuid4()
    latest_user_input_id = user_input_id
    threading.Thread(target=performRequestWithStreaming,
                     args=(user_input, user_input_id)).start()
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    socketio.run(app, debug=True)
else:
    app = app

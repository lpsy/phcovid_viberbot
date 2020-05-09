import json
import os

from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
import logging

from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest

with open('tokens.json') as fp:
    TOKENS = json.load(fp)

app = Flask(__name__)

viber = Api(BotConfiguration(
    name='CoronaVirus',
    avatar='http://site.com/avatar.jpg',
    auth_token=TOKENS['auth_token']
))

def load_subscribers(data='subscribers.json'):
    if os.path.exists(data):
        with open(data) as fp:
            subscribers = json.load(fp)
    else:
        subscribers = []
    return subscribers

@app.route('/', methods=['POST'])
def incoming():
    logging.debug("received request. post data: {0}".format(request.get_data()))
    # every viber message is signed, you can verify the signature using this method
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    # this library supplies a simple way to receive a request object
    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberMessageRequest):
        message = viber_request.message

        subscribers = load_subscribers()
        if 'unsubscribe' in message.text:
            if viber_request.sender.id in subscribers:
                subscribers.pop(subscribers.index(viber_request.sender.id))
            message = TextMessage(text='Unsubscribed!')
        else:
            message = TextMessage(text='Thanks For Subscribing!')
            subscribers.append(viber_request.sender.id)

        viber.send_messages(viber_request.sender.id, [
            message
        ])

        subscribers = list(set(subscribers))

        with open('subscribers.json', 'w') as fp:
            json.dump(subscribers, fp)

    elif isinstance(viber_request, ViberUnsubscribedRequest):
        subscribers = load_subscribers()
        if viber_request.sender.id in subscribers:
            subscribers.pop(subscribers.index(viber_request.sender.id))

        with open('subscribers.json', 'w') as fp:
            json.dump(subscribers, fp)

    elif isinstance(viber_request, ViberFailedRequest):
        logging.warn("client failed receiving message. failure: {0}".format(viber_request))

    return Response(status=200)

@app.route('/update', methods=['POST'])
def update():
    logging.debug("received request. post data: {0}".format(request.get_data()))
    data = json.loads(request.get_json())

    if data['code'] != TOKENS['post_request']:
        return Response(status=200)
    text = data['message']

    message = TextMessage(text=text)
    
    subscribers = load_subscribers()
    for s in subscribers:
        viber.send_messages(s, [message])

    return Response(status=200)


if __name__ == "__main__":
    app.run()
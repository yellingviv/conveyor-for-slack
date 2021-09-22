import os
import logging
import time
import json
import threading
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, request
from dotenv import load_dotenv
import conveyor_bot
import slack_messages

load_dotenv()

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# initialize app with slack bot token and signing secret
app = App(
    token=os.getenv('SLACK_BOT_TOKEN'),
    signing_secret=os.getenv('SLACK_SIGNING_SECRET')
)
channel_id = os.getenv('SLACK_CHANNEL_ID')


@app.action("approve")
def handle_approval(ack, body, client, say):
    # approve request in conveyor and update the db, update the slack content on success

    ack()
    payload = body['message']['blocks']
    selections = body['state']['values']
    addtl_perms = conveyor_bot.get_selections(payload, selections)
    if addtl_perms == 'yikes':
        say("Something went wrong with the permissions.")
        logger.info("Error in fetching additional permissions")
    requester = body['message']['blocks'][2]['text']['text']
    request_id = body['actions'][0]['value']
    user_id = body['user']['id']
    get_email = client.users_info(user=body['user']['id'])
    user_email = get_email['user']['profile']['email']
    approve_it = conveyor_bot.approve_requests(request_id, user_email, addtl_perms)
    if approve_it == 'yay':
        update_request_screen(body['container']['message_ts'], requester, user_id, 'approved', client)
    else:
        logger.info(approve_it)
        try:
            response = app.client.chat_postMessage(
                channel=channel_id,
                ts=body['container']['message_ts'],
                text=approve_it
            )
        except SlackApiError as e:
            logger.info(f"Error: {e}")


@app.action("reject")
def handle_rejection(ack, body, client):
    # process slack reject - call for modal to get more info

    ack()
    request_id = body['message']['blocks'][6]['elements'][1]['value']
    user_id = body['user']['id']
    get_email = client.users_info(user=body['user']['id'])
    user_email = get_email['user']['profile']['email']
    requester = body['message']['blocks'][2]['text']['text']
    get_feedback(body['container']['message_ts'], body['trigger_id'], requester, user_id, user_email, request_id, client)


@app.action("perms")
def handle_perm_ticks(ack):
    # honestly currently this does nothing but don't want errors!
    # this could be used to track selections, but i just pull from the final payload
    # this is purely to prevent error messages within the slack app that scare people

    ack()


@app.view_submission("feedback")
def handle_view_events(ack, body, client, view):
    # process the submitted modal with rejection notes
    # file rejection in conveyor, update database, update Slack with the info

    respond_close = {"response_action": "clear"}
    ack(respond_close)
    metadata = json.loads(view['private_metadata'])
    note = view['state']['values'][list(view['state']['values'].keys())[0]]['feedback_input']['value']
    user_id = metadata['user_id']
    requester = metadata['requester']
    ts = metadata['ts']
    conveyor_bot.reject_requests(metadata['request_id'], metadata['user_email'], note)
    update_request_screen(ts, requester, user_id, 'rejected', client, note)


@app.view_closed("feedback")
def handle_view_close(ack, body, logger):
    # again just tracking

    ack()
    logger.info("rejection form closed without submission")


def get_feedback(origin_ts, trigger, requester, user_id, user_email, request_id, client):
    # get feedback from reviewer on why the rejection via modal
    # rejection should not be common, so we want to have info on why to respond to inquiries

    data_str = json.dumps({"ts": origin_ts, "requester": requester, "user_id": user_id, "user_email": user_email, "request_id": request_id})
    client.views_open(
        trigger_id=trigger,
        view={
            "type": "modal",
            "callback_id": "feedback",
            "title": {"type": "plain_text", "text": "Review Details"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "blocks": [
                {"type": "input",
                "element": {"type": "plain_text_input", "action_id": "feedback_input", "multiline": True},
                "label": {"type": "plain_text", "text": "Please explain the reason for rejecting this request:"},
                "optional": False
                }
            ],
            "notify_on_close": True,
            "private_metadata": data_str
        }
    )


def update_request_screen(ts, requester, user_id, status, client, note="N/A"):
    # update the original request message with new content on action from reviewer
    # used by the handle_rejection and handle_approval actions

    try:
        result = app.client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=slack_messages.update_request(requester, user_id, status, note),
            text="You have successfully approved this request."
        )
    except SlackApiError as e:
        logger.info(f"Error: {e}")


def monitor_the_queue():
    # checks in with conveyor for new requests and posts them to slack

    logger.info("started monitoring the queue")
    while True:
        # refresh queue for new requests
        queue_info = conveyor_bot.pending_request_check()
        if queue_info != []:
            reqs = conveyor_bot.get_queue_info(queue_info)
            queue = slack_messages.create_queue(reqs)
            for i in range(0, len(queue)):
                try:
                    result = app.client.chat_postMessage(
                        channel=channel_id,
                        blocks=queue[i],
                        text="you should only see this if something went wrong, which means something went wrong. Please contact the bot owner!"
                    )
                    logger.info(f"posted to channel: {result.status_code}")
                except SlackApiError as e:
                    logger.info(f"Error: {e}")
        # wait a minute then check again ... is a minute too frequent? PROBABLY. Can be changed.
        logger.info("sleep starting")
        time.sleep(60)
        logger.info("sleep finished")


# setting up flask to provide safer happier friendly friend life
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


# start the app
if __name__ == "__main__":
    monitor = threading.Thread(target=monitor_the_queue)
    monitor.start()
    logging.info("Main    : starting Bolt app")
    app.start(port=int(os.environ.get("PORT", 8080)))

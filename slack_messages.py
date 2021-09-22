# a separate file for all the slack message block kit blocks
# this shit just gets long and i don't wanna crowd the main app file

import aptible_bot
from datetime import datetime

def create_queue(reqs):
    # create a whole bunch of properly formatted blocks for new requests
    # this is here because gosh it takes up a lot of space

    queue_blocks = []

    for i in range(0, len(reqs)):
        req_block =[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":sparkles: Conveyor Room Request :sparkles:"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "<" + reqs[i]['url'] + "|New access request from:>"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": reqs[i]['from']
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Received at: " + reqs[i]['time']
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Message: " + reqs[i]['message']
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "checkboxes",
                     "options": aptible_bot.get_perms(),
                    "action_id": "perms"
                },
                "label": {
                    "type": "plain_text",
                    "text": "All requests are granted standard permissions. Use the checkboxes to add additional permissions if needed."
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":blob-checkmark: Approve Request"
                        },
                        "value": reqs[i]['id'],
                        "action_id": "approve"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":blob-x: Reject Request"
                        },
                        "value": reqs[i]['id'],
                        "action_id": "reject"
                    }
                ]
            }
        ]
        queue_blocks.append(req_block)

    return queue_blocks


def update_request(requester, user_id, status, note="N/A"):
    # create a block that updates the original request message to show status

    approved_time = datetime.now()
    stamp = approved_time.strftime("%B %d, %Y, %I:%M %p")
    status_blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":sparkles: " + status.upper() + " Conveyor Room Request :sparkles:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Request from {requester} {status}ed by <@{user_id}> at {stamp}."
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Request reviewed with comment: " + note
            }
        }]

    return status_blocks

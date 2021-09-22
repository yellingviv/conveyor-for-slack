# a sidecar module to the app.py file in order to keep clutter out of the main one
# this is all the helper functions that are called to do the work behind the scenes 

import requests
import time
import json
import os
import logging
from dotenv import load_dotenv
from datetime import datetime

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

load_dotenv()
apt_key = os.getenv('CONVEYOR_KEY')
apt_url = 'https://api.conveyorhq.com/api/v2/exchange/'
apt_head = {'X-API-KEY': apt_key, 'Accept': 'application/json', 'Content-Type': 'application/json'}

request_history = {}

def pending_request_check():
    # pull the current queue and compare against known requests
    # remove repeat requests and return new requests

    request_queue = requests.get(apt_url + 'authorization_request_queue', headers=apt_head)
    if request_queue.status_code == 200:
        queue_blob = request_queue.json()
        queue_info = queue_blob['authorization_requests']
        logger.info(f"Queue successfully retrieved. It is length: {len(queue_info)}")
    else:
        logger.info('Error: ',  request_queue.status_code)
    to_pop = []
    for i in range(0, len(queue_info)):
        if queue_info[i]['id'] in request_history:
            to_pop.append(i)
    logger.info(f"{len(to_pop)} out of {len(queue_info)} already in history; skipped in queue")
    for i in range(len(to_pop) - 1, -1, -1):
        queue_info.pop(i)
    return queue_info


def get_queue_info(queue_info):
    # clean up the queue to be easier to put into blocks. this is vanity mostly.

    queue_size = len(queue_info)
    queue_specifics = []
    for i in range(0, len(queue_info)):
        queue_item = {}
        queue_item['id'] = queue_info[i]['id']
        queue_item['time'] = queue_info[i]['requested_at']
        queue_item['from'] = queue_info[i]['email']
        queue_item['message'] = queue_info[i]['message']
        queue_item['url'] = queue_info[i]['_links']['self']['href']
        queue_specifics.append(queue_item)
        request_history[queue_item['id']] = { 'email': queue_item['from'],
            'requested_at': queue_item['time'],
            'message': queue_item['message'],
            'status': 'waiting',
            'url': queue_item['url'] }
        logger.info(f"added {queue_info[i]['id']} request to history")
    return queue_specifics


def approve_requests(request_id, email, addtl_perms):
    # approve a request with specified permissions where applicable

    payload = { 'request_id': request_id,
                'reviewer_email': email,
                'access_group_ids': addtl_perms,
                'nda_bypass': False }
    do_approval = requests.post(apt_url + 'authorizations', headers=apt_head, json=payload)
    if str(do_approval.status_code)[0] == '2':
        update_request_info(request_id, email, 'approved')
        return('yay')
    else:
        error_msg = 'Error encountered while attempting to approve this request. Error code received is ' + str(do_approval.status_code) + '. Please contact bot owner for help.'
        return error_msg


def reject_requests(request_id, email, note):
    # reject a request, mwahaha

    payload = { 'status': 'ignored',
                'reviewer_email': email }
    do_rejection = requests.patch(apt_url + 'authorization_requests/' + request_id, headers=apt_head, json=payload)
    if str(do_rejection.status_code)[0] == '2':
        update_request_info(request_id, email, 'rejected', note)
        return('yay')
    else:
        error_msg = 'Error encountered while attempting to reject this request. Error code received is ' + str(do_rejection.status_code) + '. Please contact bot owner for help.'
        return error_msg


def get_perms():
    # pull access group permissions list and format to use in options list on Slack

    access_pull = requests.get(apt_url + 'access_groups', headers=apt_head)
    access_blob = access_pull.json()
    access_list = access_blob['access_groups']
    access_choices = []
    for i in range(0, len(access_list)):
        access_option = {
            "text": {
                "type": "plain_text",
                "text": access_list[i]['name']
            },
            "value": access_list[i]['id']
        }
        access_choices.append(access_option)
    return access_choices


def get_selections(payload, selections):
    # sort through the giant effing block of slack interactivity response for data
    # specifically the data about what permissions are selected, and the request id

    block_id = []
    for field in payload:
        if field['type'] == 'input':
            block_id.append(field['block_id'])
    if len(block_id) != 1:
        return('yikes')
    extras = []
    num_selected = len(selections[block_id[0]]['perms']['selected_options'])
    for i in range(0, num_selected):
        access_id = selections[block_id[0]]['perms']['selected_options'][i]['value']
        extras.append(access_id)
    return extras


def update_request_info(request_id, email, action, note="N/A"):
    # update request info in the db once approved or not

    timestamp = datetime.now()
    reviewed = timestamp.strftime("%B %d, %Y, %I:%M %p")
    request_history[request_id]['reviewed_by'] = email
    request_history[request_id]['reviewed_at'] = reviewed
    request_history[request_id]['status'] = action
    request_history[request_id]['note'] = note

import os
from check_tpu import list_queued_resources, delete_queue_resources, apply_queue_resources
from google.cloud.tpu_v2alpha1.types.cloud_tpu import QueuedResourceState, QueuedResource
import time
from parse_utils import parse_name_and_cores
from send_message import send_message_to_channel, init_bot
import traceback
from constants import *
from gs_utils import init_gsheet_service, upload_data_to_spreadsheet, TPU_Usage
from billing_utils import update_billing_results
INITED = True
FIRST_TIME = True
cur_active_resources = []
cur_suspended_resources = []
cur_starting_resources = []
long_living_resource_path = "./watching_list.json"
long_living_resources = {}
import json
def get_diff_resources(current_resources, new_resources):
    new_resources = [resource for resource in new_resources if resource not in current_resources]
    deleted_resources = [resource for resource in current_resources if resource not in new_resources]
    return new_resources, deleted_resources
def main():
    global INITED, FIRST_TIME ,SLACK_BOT_TOKEN, CHANNEL_NAME, ZONE, cur_active_resources, cur_suspended_resources, cur_starting_resources
    client, _ = init_bot(SLACK_BOT_TOKEN=SLACK_BOT_TOKEN)
    if not INITED:
        send_message_to_channel(client, CHANNEL_NAME, "BOT STARTED")
        INITED = True
    usage = TPU_Usage()
    try:
        sheet_inited = False
        #service = init_gsheet_service('./')  # gsheet is down due to unstable Google Service
        #sheet_inited = True
    except Exception as e:
        print(f"Error when init gsheet service: {e}")
        sheet_inited = False
    spreadsheet_id = SPREADSHEET_ID
    while True:
        starting_resources, suspended_resources, active_resources ,all_tpu_cores = list_queued_resources(ZONE)
        # load the long living resources
        try:
            with open(long_living_resource_path, 'r') as f:
                long_living_resources = json.load(f)
        except Exception as e:
            print(f"Error when loading long living resource: {e}")
        if FIRST_TIME:
            cur_active_resources = active_resources
            #cur_suspended_resources = suspended_resources
            cur_starting_resources = starting_resources
            FIRST_TIME = False
        new_start_instances , _  = get_diff_resources(cur_starting_resources, starting_resources)
        new_active_instances , _  = get_diff_resources(cur_active_resources, active_resources)
        new_suspended_instances , _  = get_diff_resources(cur_suspended_resources, suspended_resources)
        total_running_instances = len(active_resources)
        user_list, user_cores, tpu_belongings = parse_name_and_cores(active_resources)
        usage.refresh()
        for user in user_list:
            usage.update_usage(user, tpu_belongings[user])
        #print(usage)
        formatted_data = usage.return_formatted_data()
        if sheet_inited:
            try:
                upload_data_to_spreadsheet(formatted_data, service, spreadsheet_id, 'TPU_Usage')
                usage.merge_cells_for_users(service, spreadsheet_id)
            except Exception as e:
                print(f"Error when uploading data to spreadsheet: {e}")
        message = ""
        #if len(new_start_instances) > 0:
        #    for resource in new_start_instances:
        #        message += f"state change: {resource.name.split('/')[-1]} of type {resource.tpu.node_spec[0].node.accelerator_type} is at {str(resource.state).lower()}\n"
                
        #if len(new_active_instances) > 0:
        #    for resource in new_active_instances:
        #        message += f"active! {resource.name.split('/')[-1]} of type {resource.tpu.node_spec[0].node.accelerator_type} is active now\n"
        if len(new_suspended_instances) > 0:
            for resource in new_suspended_instances:
                message += f"SUSPENDED: {resource.name.split('/')[-1]} of type {resource.tpu.node_spec[0].node.accelerator_type} is at {str(resource.state).lower()}"
                if resource.state.state in [QueuedResourceState.State.SUSPENDED, QueuedResourceState.State.FAILED]:
                    try:
                        result = delete_queue_resources(ZONE, resource.name)
                        message += f"& Automatically Deleted\n"
                        total_running_instances -= 1
                    except Exception as e:
                        message += f"|| Error while deleting resource: {resource.name.split('/')[-1]}\n, Error: {e}\n"
                        print(f"Error: {e}")
        # check the state of long living resources, re-apply them if they are suspended
        for resource, cores in long_living_resources.items():
            all_live_resources = starting_resources + active_resources
            all_names = [resource.name.split('/')[-1] for resource in all_live_resources]
            if resource not in all_names:
                try:
                    apply_queue_resources(ZONE, resource, cores)
                    message += f"Re-apply resource: {resource} with {cores} cores\n"
                except Exception as e:
                    message += f"{e}"
                    print(f"Error: {e}")
        SEND_MESSAGE = len(message) > 0
        message += f"Current used TPU cores: {all_tpu_cores}, Total active instances: {total_running_instances}/30"
        cur_active_resources = active_resources
        cur_starting_resources = starting_resources
        cur_suspended_resources = suspended_resources
        if SEND_MESSAGE:
            send_message_to_channel(client, CHANNEL_NAME, message)
        billing_messages = update_billing_results(PROJECT_ID, DATASET_ID, TABLE_ID, topk=6)
        if len(billing_messages) > 0:
            for billing_message in billing_messages:
                send_message_to_channel(client, TPU_USER_CHANNEL_NAME, "<!channel> " + billing_message) # <!channel> will ping all users in the channel
        #print(message)
        time.sleep(600)
        
def repeted_run():
    while True:
        try:
            main()
        except Exception as e:
            traceback.print_exc()
            time.sleep(60) # sleep for 1 minute and try again
if __name__ == "__main__":
    repeted_run()
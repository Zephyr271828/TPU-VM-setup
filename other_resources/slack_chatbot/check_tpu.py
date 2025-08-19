from google.cloud import tpu_v2alpha1
from google.auth import default
from google.cloud.tpu_v2alpha1.types.cloud_tpu import QueuedResourceState
from google.protobuf.message import Message
import os
import subprocess
BEGIN_STATE = [QueuedResourceState.State.WAITING_FOR_RESOURCES, QueuedResourceState.State.PROVISIONING, QueuedResourceState.State.CREATING]
ACTIVE_STATE = [QueuedResourceState.State.ACTIVE]
DEAD_STATE = [QueuedResourceState.State.SUSPENDED, QueuedResourceState.State.FAILED]
def list_tpus(zone):
    credentials, project_id = default()
    client = tpu_v2alpha1.TpuClient(credentials=credentials)

    # Construct the fully qualified location name
    parent = f'projects/{project_id}/locations/{zone}'

    # List TPUs
    tpus = client.list_nodes(parent=parent)
    for tpu in tpus:
        print(f'TPU Name: {tpu.name}')
        print(f'Accelerator Type: {tpu.accelerator_type}')
        print(f'State: {tpu.state}')
        print('---')
def delete_queue_resources(zone, name):
    credentials, project_id = default()
    client = tpu_v2alpha1.TpuClient(credentials=credentials)
    # Construct the fully qualified location name
    request = tpu_v2alpha1.DeleteQueuedResourceRequest(name=name)
    # Delete the node
    response = client.delete_queued_resource(request=request)
    return response
def apply_queue_resources(zone, name, tpu_cores):
    credentials, project_id = default()
    # Construct the fully qualified location name
    assert tpu_cores in [8, 16, 32, 64, 128, 256, 512, 1024], "Invalid TPU cores"
    cmd = f'/home/boyang/google-cloud-sdk/bin/gcloud alpha compute tpus queued-resources create {name} \
        --node-id {name} \
        --project nyu-vision-lab --zone us-central2-b \
        --accelerator-type v4-{tpu_cores} \
        --runtime-version tpu-ubuntu2204-base \
        --best-effort'
    # google cloud api is not well-documented, so we use gcloud command to create the resources
    p = subprocess.run([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, executable='/bin/bash')
    stdout = p.stdout
    stderr = p.stderr
    response = p.returncode
    # if error occurs, raise exception
    if response != 0:
        raise Exception(f"Error while creating resource {name}, Error: {stderr}")
    return stderr # gcloud returns the stdout message in stderr
def list_queued_resources(zone):
    credentials, project_id = default()
    # save the credentials to local file
    with open('credentials.json', 'w') as f:
        f.write(credentials.to_json())
    client = tpu_v2alpha1.TpuClient(credentials=credentials)
    #client.list_operations()
    # Construct the fully q zualified location name
    parent = f'projects/{project_id}/locations/{zone}'
    request = tpu_v2alpha1.ListQueuedResourcesRequest(parent=parent)
    # List queued resources
    queued_resources = client.list_queued_resources(request=request)
    all_tpu_cores = 0
    for resource in queued_resources:
        #print(f'Accelerator Type: {resource.accelerator_type}')
        if resource.state.state == QueuedResourceState.State.ACTIVE:
            all_tpu_cores += int(resource.tpu.node_spec[0].node.accelerator_type.split('-')[1])
        #break
    STARTING_RESOURCES = [resource for resource in queued_resources if resource.state.state in BEGIN_STATE]
    SUSPENDED_RESOURCES = [resource for resource in queued_resources if resource.state.state in DEAD_STATE]
    ACTIVE_RESOURCES = [resource for resource in queued_resources if resource.state.state in ACTIVE_STATE]
    return STARTING_RESOURCES, SUSPENDED_RESOURCES, ACTIVE_RESOURCES, all_tpu_cores


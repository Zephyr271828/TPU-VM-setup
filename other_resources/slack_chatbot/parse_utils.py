# utils for parsing tpu users
from google.cloud.tpu_v2alpha1.types.cloud_tpu import QueuedResourceState, QueuedResource

from typing import List, Tuple
def parse_rule(name: str) -> str:
    return name.lower().split('-')[0].split('_')[0]
def parse_name_and_cores(tpu_infos: List[QueuedResource]) -> Tuple[List, List, List]:
    """
    Parse the TPU names and cores from the TPU info list.
    """
    formatted_tpu_infos = []
    for resource in tpu_infos:
        formatted_tpu_infos.append((resource.name.split('/')[-1], int(resource.tpu.node_spec[0].node.accelerator_type.split('-')[1])))
    tpu_belongings = {}
    for tpu in formatted_tpu_infos:
        tpu_name, tpu_core = tpu
        user_name = parse_rule(tpu_name)
        if user_name not in tpu_belongings.keys():
            tpu_belongings[user_name] = []
        tpu_belongings[user_name].append(tpu)
    user_list = list(tpu_belongings.keys())
    user_cores = []
    for user in user_list:
        user_cores.append(sum([tpu[1] for tpu in tpu_belongings[user]]))
    return user_list, user_cores, tpu_belongings
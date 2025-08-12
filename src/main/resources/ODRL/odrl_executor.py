import os
from typing import Optional
from rdflib import Graph
from engine.policy_engine import is_access_allowed
from engine.request_parser import parse_request


def process_odrl_request(request_ttl_path: str) -> Optional[str]:
    request_data = parse_request(request_ttl_path)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    if not request_data:
        return None

    assignee_uri = request_data["assignee"]
    action = request_data["action"]
    target = request_data["target"]
    constraints = request_data["constraints"]

    # Check all available policies
    policy_dir = os.path.join(BASE_DIR, "policies")
    result = None
    target_name = target.split("/")[-1] if "/" in target else target
    for filename in os.listdir(policy_dir):
        if not filename.endswith(".ttl"):
            continue
        if not filename.startswith(target_name):
            continue  # Skip policies not related to the current target
        # print(f"🔍 Checking policy: {filename}")
        policy_path = os.path.join(policy_dir, filename)
        result = is_access_allowed(
            policy_file=policy_path,
            assignee_uri=assignee_uri,
            action=action,
            target_uri=target,
            constraints=constraints
        )

        if result:
            break

    if not result:
        return None

    data_file = result
    query_dir = os.path.join(BASE_DIR, "data")
    query_path = os.path.join(query_dir, data_file)

    if not os.path.exists(query_path):
        return None

    with open(query_path, "r", encoding="utf-8") as f:
        return f.read()

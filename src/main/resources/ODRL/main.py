import sys
from odrl_executor import process_odrl_request

odrl_request = sys.stdin.read()

query_str = process_odrl_request(odrl_request)
if query_str:
    print(query_str)
else:
    print("⚠️ Failed to generate query due to policy restrictions.")

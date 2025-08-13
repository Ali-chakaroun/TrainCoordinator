import json
import os
import sys
from rdflib import Graph
from rdflib.namespace import Namespace
import requests

# --- ODRL request ---
def send_odrl_request(url: str, odrl_payload: str) -> str:
    # Sends an ODRL request to the given endpoint and returns the result as a string.
    try:
        headers = {"Content-Type": "text/turtle"}
        response = requests.post(url, data=odrl_payload, headers=headers)

        if response.status_code == 200:
            return response.text
        else:

            return f"Error {response.status_code}: {response.text}"

    except requests.exceptions.RequestException as e:
        return f"🚨 An error occurred: {e}"
    
ttl_file = sys.argv[1]

# Load the RDF file
g = Graph()
g.parse(ttl_file, format="ttl")
os.makedirs("Output", exist_ok=True)

columns_to_ignore = [
    "Receive_date", "Reporter_qualification", "Case_narrative", "Additional_information"
]

endpoint = "http://localhost:6060/api/analysis/odrl-execute"
odrl_data = """
@prefix odrl:   <http://www.w3.org/ns/odrl/2/> .
@prefix ex:     <http://example.org/> .

<http://example.org/request:se-query>
    a odrl:Request ;
    odrl:uid <https://www.wikidata.org/wiki/Q25670> ;
    odrl:profile <https://www.wikidata.org/wiki/Q4382010> ;

    odrl:permission [
        odrl:target <http://example.org/graph/extract_adr_data> ;
        odrl:assignee ex:researcher ;
        odrl:action odrl:read

    ] .
"""
query = send_odrl_request(endpoint, odrl_data)
results = g.query(query)

# covert result into sparql-json format
sparql_json = json.loads(results.serialize(format='json').decode('utf-8'))

aggregated_data = {}

for binding in sparql_json["results"]["bindings"]:
    id_val = binding["id"]["value"]
    attr = binding["attr"]["value"]
    val = binding["val"]["value"]

    if attr not in columns_to_ignore:
        if id_val not in aggregated_data:
            aggregated_data[id_val] = {}

        if attr not in aggregated_data[id_val]:
            aggregated_data[id_val][attr] = set()

        aggregated_data[id_val][attr].add(val)
        
def combine_unique(values, delimiter="; "):
    values = [v for v in values if v not in [None, "nan"]]
    if not values:
        return None
    return delimiter.join(values)


final_data = []

for id_val, attributes in aggregated_data.items():
    row = {"ID": id_val}
    for attr, values in attributes.items():
        row[attr] = combine_unique(list(values))
    final_data.append(row)


with open("Output/ADRData.json", "w") as json_file:
    json.dump(final_data, json_file, indent=2)


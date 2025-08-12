import json
import os
import sys
import pandas as pd
from fuzzywuzzy import fuzz
from rdflib import Graph, Literal, Namespace, URIRef
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
    
rdf_file = sys.argv[1]
ttl_file = sys.argv[2]

os.makedirs("Output", exist_ok=True)
g = Graph()
g.parse(ttl_file, format="turtle")


endpoint = "http://localhost:6060/api/analysis/odrl-execute"
odrl_data = """
@prefix odrl:   <http://www.w3.org/ns/odrl/2/> .
@prefix ex:     <http://example.org/> .

<http://example.org/request:se-query>
    a odrl:Request ;
    odrl:uid <https://www.wikidata.org/wiki/Q25670> ;
    odrl:profile <https://www.wikidata.org/wiki/Q4382010> ;

    odrl:permission [
        odrl:target <http://example.org/graph/extract_l_data> ;
        odrl:assignee ex:researcher ;
        odrl:action odrl:read

    ] .
"""
query = send_odrl_request(endpoint, odrl_data)
results = g.query(query)
sparql_json = json.loads(results.serialize(format='json').decode('utf-8'))
rdf_records = []
for binding in sparql_json["results"]["bindings"]:
    subj_str = binding["subject"]["value"]
    pred_str = binding["predicate"]["value"].split("/")[-1]
    obj_str = binding["object"]["value"]
    
    # Find if the subject already exists in rdf_records
    record = next((r for r in rdf_records if r.get('subject') == subj_str), None)
    
    # If subject is found, update the record, else create a new one
    if record is None:
        record = {'subject': subj_str}  
        rdf_records.append(record)
    
    record[pred_str] = obj_str

# Create DataFrame and ensure key column exists
df = pd.DataFrame(rdf_records)
df = df.drop(columns="subject")

key_column = 'WorldwideUniqueCaseIdentification'
if key_column not in df.columns:
    raise ValueError(f"Missing key column: {key_column}")


def combine_unique(series, delimiter="; "):
    non_null = series.dropna().astype(str).unique()
    return delimiter.join(non_null) if len(non_null) > 0 else "unknown"

final_excel_df = df.groupby(key_column).agg(
    {col: combine_unique for col in df.columns if col != key_column}
).reset_index()

# Part 2: Load and prepare JSON data
df_json = pd.read_json(rdf_file).fillna("unknown")

# Align JSON to Excel structure
json_aligned = pd.DataFrame(columns=final_excel_df.columns)
for col in json_aligned.columns:
    json_aligned[col] = df_json[col] if col in df_json.columns else "unknown"

# Columns to compare
compare_columns = [
    'ATCText', 
    'Other_suspect_ATCText', 
    'Concomitant_ATCText', 
    'Reaction_PT', 
    'Other_Reported_PTs',
    'Medical_history_PT'
]

# match data from Lareb database with the ADR data
matched_excel_rows = []
for _, json_row in df_json.iterrows():
    for _, excel_row in final_excel_df.iterrows():
        match_score = 0
        valid_comparisons = 0
        
        for col in compare_columns:
            json_val = str(json_row.get(col, "unknown"))
            excel_val = str(excel_row.get(col, "unknown"))
            
            # Skip if either value is unknown/empty
            if json_val.lower() == "unknown" or excel_val.lower() == "unknown":
                continue
            if not json_val.strip() or not excel_val.strip():
                continue
            
            valid_comparisons += 1
            if fuzz.token_set_ratio(json_val, excel_val) >= 70:
                match_score += 1
        
        # Require at least 2 valid comparisons and >80% match rate
        if valid_comparisons >= 2 and match_score / valid_comparisons >= 0.8:
            matched_excel_rows.append(excel_row.copy())

json_aligned[key_column] = df_json['ID']

# Combine results
output_df = pd.concat([
    json_aligned,
    pd.DataFrame(matched_excel_rows).drop_duplicates()
], ignore_index=True)

output_graph = Graph()
BASE = Namespace("http://example.org/")  
output_graph.bind("ex", BASE)  

for idx, row in output_df.iterrows():
    subj = URIRef(f"{BASE}row/{idx + 1}")
    for col in output_df.columns:
        val = row[col]
        if pd.isna(val) or str(val).strip().lower() == "unknown":
            continue
        pred = URIRef(f"{BASE}{col.strip().replace(' ', '_')}")
        output_graph.add((subj, pred, Literal(str(val))))

output_graph.serialize(destination="Output/extractDataFromL.ttl", format="turtle")

with open("Output/ADRDataRecords.json", "w") as meta_file:
    json.dump({"records": len(matched_excel_rows)}, meta_file, indent=2)
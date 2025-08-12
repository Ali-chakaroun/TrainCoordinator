from collections import defaultdict
import json
import os
import sys
import pandas as pd
from rdflib import Graph
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
json_file = sys.argv[2]
atc_file = sys.argv[3]

os.makedirs("Output", exist_ok=True)

g = Graph()

# Removes special characters (e.g., '_x000D_') and trims whitespace from the provided value. Returns NaN values unchanged.
def clean_text(x):
    """Clean text by removing special characters and whitespace"""
    if pd.isna(x):
        return x
    return str(x).replace('_x000D_', '').strip()

# Splits multiline values in specified DataFrame columns into individual entries
# based on the provided delimiter (default: newline). Pads shorter lists so all
# columns have the same length for each row. Groups and returns the processed
# entries as a dictionary keyed by patient/report ID.
def map_multiline_columns(df, columns, delimiter='\n'):
    mapped_by_id = {}

    for idx, row in df.iterrows():
        row_id = row.get("UMC_report_ID", f"Row_{idx}")  # Fallback to Row_<index> if no ID
        
        # Split each column's cell into a list by line
        split_columns = {
            col: str(row[col]).split(delimiter) if pd.notna(row[col]) else [] 
            for col in columns
        }
        
        # Find the max length of the split data
        max_len = max(len(vals) for vals in split_columns.values())
        
        # Pad the shorter lists with None
        for col in columns:
            if len(split_columns[col]) < max_len:
                split_columns[col] += [None] * (max_len - len(split_columns[col]))

        # Create mapped entries for this row
        row_mappings = []
        for i in range(max_len):
            entry = {col.lower(): split_columns[col][i] for col in columns}
            row_mappings.append(entry)

        mapped_by_id[row_id] = row_mappings

    return mapped_by_id

# Iterates through mapped drug data to count how many times each unique
# (drug, role, action) combination appears across patients. Prevents counting
# duplicates within the same patient. Returns a list of aggregated statistics
# with the count and the list of patient IDs for each combination.    
def aggregate_all_drugs(mapped_data):
    aggregation = defaultdict(lambda: {
        "count": 0,
        "ID": set()
    })

    for patient_id, entries in mapped_data.items():
        seen_in_this_patient = set()

        for entry in entries:
            drugs = (entry.get("whodrug_active_ingredient_variant") or "").strip().lower()
            role = (entry.get("role") or "").strip().lower()
            action = (entry.get("action_taken_with_drug") or "").strip().lower()
            drug_list = [d.strip() for d in drugs.split(";") if d.strip()]
            if role not in {"suspect", "concomitant"}:
                continue
            for drug in drug_list:
                key = (drug.strip().lower(), role, action)

                # Avoid counting duplicate (drug, role, action) per patient
                if key in seen_in_this_patient:
                    continue

                seen_in_this_patient.add(key)
                aggregation[key]["count"] += 1
                aggregation[key]["ID"].add(patient_id)

    # Format for output
    aggregated_list = [
        {
            "drug": drug,
            "role": role,
            "count": data["count"],
            "actions": [action] if action else [],
            "ID": list(data["ID"])
        }
        for (drug, role, action), data in aggregation.items()
    ]

    return aggregated_list

# Iterates through mapped reaction/outcome data to count how many times each
# unique (reaction, result) combination appears across patients. Prevents counting
# duplicates within the same patient. Returns a list of aggregated statistics
# with the count and the list of patient IDs for each combination.
def aggregate_all_outcomes(mapped_data):
    aggregation = defaultdict(lambda: {
        "count": 0,
        "ID": set()
    })

    for patient_id, entries in mapped_data.items():
        seen_in_this_patient = set()

        for entry in entries:
            reaction = (entry.get("mapped_term") or "").strip().lower()
            result = (entry.get("outcome") or "").strip().lower()
  
            key = (reaction, result)

            # Avoid counting duplicate 
            if key in seen_in_this_patient:
                continue

            seen_in_this_patient.add(key)
            aggregation[key]["count"] += 1
            aggregation[key]["ID"].add(patient_id)

    # Format for output
    aggregated_list = [
        {
            "reaction": reaction,
            "result": result,
            "count": data["count"],
            "ID": list(data["ID"])
        }
        for (reaction, result), data in aggregation.items()
    ]

    return aggregated_list

# retrieves hierarchical drug classification data for concomitant drugs.
def get_atc_hierarchy(drugs):
    drugs_conco= set()
    for d in drugs:
        if d.get("role", "").lower() == "concomitant":
            drugs_conco.add(d.get("drug"))
 
    g.parse(atc_file, format="turtle")
 
    endpoint = "http://localhost:6060/api/analysis/odrl-execute"
    odrl_data = """
    @prefix odrl:   <http://www.w3.org/ns/odrl/2/> .
    @prefix ex:     <http://example.org/> .

    <http://example.org/request:se-query>
        a odrl:Request ;
        odrl:uid <https://www.wikidata.org/wiki/Q25670> ;
        odrl:profile <https://www.wikidata.org/wiki/Q4382010> ;

        odrl:permission [
            odrl:target <http://example.org/graph/extract_atc_data> ;
            odrl:assignee ex:researcher ;
            odrl:action odrl:read

        ] .
    """
    query = send_odrl_request(endpoint, odrl_data)
    results = g.query(query)
    sparql_json = json.loads(results.serialize(format="json").decode("utf-8"))

    hierarchy = []
    for binding in sparql_json["results"]["bindings"]:
        hierarchy.append({
            "level": int(binding["level"]["value"]),
            "parentCode": binding["parentCode"]["value"],
            "parentName": binding["parentName"]["value"],
            "drugNames": binding["drugs"]["value"],
            "drugIds": binding["drugs_ids"]["value"]
        })
    with open('Output/atc_hierarchy.json', 'w', encoding='utf-8') as f:
        json.dump(hierarchy, f, ensure_ascii=False, indent=2)



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
        odrl:target <http://example.org/graph/extract_vigi_data> ;
        odrl:assignee ex:researcher ;
        odrl:action odrl:read

    ] .
"""
query = send_odrl_request(endpoint, odrl_data)
results = g.query(query)
sparql_json = json.loads(results.serialize(format='json').decode('utf-8'))
# Initialize list to store records
rdf_records = []

for binding in sparql_json["results"]["bindings"]:
    subj_str = binding["subject"]["value"]
    pred_str = binding["predicate"]["value"].split("/")[-1]  # Use last part of URI
    obj_str = binding["object"]["value"]

    # Find if the subject already exists in rdf records
    record = next((r for r in rdf_records if r.get('subject') == subj_str), None)
    
    # If subject is found, update the record, else create a new one
    if record is None:
        record = {'subject': subj_str}  # Add the subject as the key
        rdf_records.append(record)
    
    # Add the predicate and object to the record
    record[pred_str] = obj_str

# Convert the list of records to a DataFrame
df = pd.DataFrame(rdf_records)
df = df.drop(columns="subject")
df = df.map(clean_text)

with open(json_file, "r") as f:
    processed_data = json.load(f)


atc_values = {
    atc.strip().lower()
    for entry in processed_data
    for field in ["ATCText", "Other_suspect_ATCText"]
    if entry.get(field)
    for atc in entry[field].split(";")
    if atc.strip()
}

# Clean the drug column
df["WHODrug_active_ingredient_variant"] = df["WHODrug_active_ingredient_variant"].astype(str).map(clean_text)

# Filter rows where any line in the drug column matches ATCText values
def contains_matching_atc(cell):
    lines = str(cell).split('\n')
    return any(line.strip().lower() in atc_values for line in lines)

filtered_df = df[df["WHODrug_active_ingredient_variant"].apply(contains_matching_atc)]

drug_mapping = map_multiline_columns(filtered_df, ['WHODrug_active_ingredient_variant', 'Role', 'Action_taken_with_drug'])
outcome_mapping = map_multiline_columns(filtered_df, ['Mapped_term', 'MedDRA_preferred_term', 'Outcome'])
aggregated_drug = aggregate_all_drugs(drug_mapping)
get_atc_hierarchy(aggregated_drug)
aggregated_outcomes = aggregate_all_outcomes(outcome_mapping)

final_aggregated = {
    "drugs": aggregated_drug,
    "outcomes": aggregated_outcomes,
    "recordsUsed": len(filtered_df)
}

with open('Output/vigiData.json', 'w', encoding='utf-8') as f:
    json.dump(final_aggregated, f, ensure_ascii=False, indent=2)

filtered_df.to_json("Output/vigiDataExcel.json", index=False)

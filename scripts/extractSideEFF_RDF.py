from collections import defaultdict
import json
import os
import sys
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
    
drug_names = sys.argv[1]
meddra_freq = sys.argv[2]
meddra_all_label_se = sys.argv[3]
SideEff = sys.argv[4]
ADRData = sys.argv[5]
vigiData = sys.argv[6]

os.makedirs("Output", exist_ok=True)

g = Graph()

def get_drug_id_by_name(drug_name: str, ttl_path: str, suspect: bool):
    found = []
    g.parse(ttl_path, format="turtle")
 
    target = ""
    if suspect: 
        target = "http://example.org/graph/extract_drug_names_suspect"
    else:
        target = "http://example.org/graph/extract_drug_names_concomitant"
    endpoint = "http://localhost:6060/api/analysis/odrl-execute"
    odrl_data = f"""
    @prefix odrl:   <http://www.w3.org/ns/odrl/2/> .
    @prefix ex:     <http://example.org/> .

    <http://example.org/request:se-query>
        a odrl:Request ;
        odrl:uid <https://www.wikidata.org/wiki/Q25670> ;
        odrl:profile <https://www.wikidata.org/wiki/Q4382010> ;

        odrl:permission [
            odrl:target <{target}> ;
            odrl:assignee ex:researcher ;
            odrl:action odrl:read
        ] .
    """
    query = send_odrl_request(endpoint, odrl_data)
    results = g.query(query)
    
    sparql_json = json.loads(results.serialize(format="json").decode("utf-8"))
    for binding in sparql_json["results"]["bindings"]:
            found.append({
                "ID": binding["id"]["value"],
                "name": binding["name"]["value"]
            })
    return found
 
 
def merge_drugs_universal(existing_drugs_str: str, vigi_data: dict, role_type: str) -> str:
    # Parse and normalize existing drugs
    existing = set(
        name.strip().lower()
        for name in existing_drugs_str.split(";")
        if name.strip()
    )
 
    # Extract and normalize drugs from vigi data based on role
    vigi = set(
        drug_info["drug"].strip().lower()
        for drug_info in vigi_data.get("drugs", [])
        if drug_info.get("role", "").lower() == role_type.lower()
    )
 
    # Merge both sets
    merged = existing.union(vigi)
    return ";".join(merged)
 
 
def check_drug_ids_in_meddra(
    drug_ids: list,
    meddra_freq_ttl: str,
    reactions_str: str,
    meddra_all_label_se_ttl: str,
    suspect: bool
):
    results = {}
    reactions = set()
    # Load RDF graphs
    g_label = g.parse(meddra_all_label_se_ttl, format="turtle")
    g_freq = g.parse(meddra_freq_ttl, format="turtle")

    target = ""
    if suspect: 
        target = "http://example.org/graph/extract_meddra_labels_suspect"
    else:
        target = "http://example.org/graph/extract_meddra_labels_concomitant"

    endpoint = "http://localhost:6060/api/analysis/odrl-execute"
    odrl_data = f"""
    @prefix odrl:   <http://www.w3.org/ns/odrl/2/> .
    @prefix ex:     <http://example.org/> .

    <http://example.org/request:se-query>
        a odrl:Request ;
        odrl:uid <https://www.wikidata.org/wiki/Q25670> ;
        odrl:profile <https://www.wikidata.org/wiki/Q4382010> ;

        odrl:permission [
            odrl:target <{target}> ;
            odrl:assignee ex:researcher ;
            odrl:action odrl:read

        ] .
    """
    uml_query = send_odrl_request(endpoint, odrl_data)
    results_labels = g_label.query(uml_query)
    sparql_json = json.loads(results_labels.serialize(format="json").decode("utf-8"))
    uml_map = {}
    
    for binding in sparql_json["results"]["bindings"]:
        drug_id = binding["drug_id"]["value"]
        side_effect = binding["se"]["value"].strip().lower()
        uml_id = binding["umls"]["value"]
        uml_map.setdefault((drug_id, side_effect), []).append(uml_id)
        reactions.add(side_effect)

    if suspect: 
        target = "http://example.org/graph/extract_meddra_freq_suspect"
    else:
        target = "http://example.org/graph/extract_meddra_freq_concomitant"
    endpoint = "http://localhost:6060/api/analysis/odrl-execute"
    odrl_data = f"""
    @prefix odrl:   <http://www.w3.org/ns/odrl/2/> .
    @prefix ex:     <http://example.org/> .

    <http://example.org/request:se-query>
        a odrl:Request ;
        odrl:uid <https://www.wikidata.org/wiki/Q25670> ;
        odrl:profile <https://www.wikidata.org/wiki/Q4382010> ;

        odrl:permission [
            odrl:target <{target}> ;
            odrl:assignee ex:researcher ;
            odrl:action odrl:read

        ] .
    """
    freq_query = send_odrl_request(endpoint, odrl_data)
    results_freq = g_freq.query(freq_query)
    sparql_json = json.loads(results_freq.serialize(format="json").decode("utf-8"))

    freq_map = {}
    for binding in sparql_json["results"]["bindings"]:
        drug_id = binding["drug_id"]["value"]
        side_effect = binding["se"]["value"].strip().lower()
        uml_id = binding["umls"]["value"]
        freq = binding["freq"]["value"]
        # if drug_id in drug_ids and side_effect in reactions:
        freq_map.setdefault((drug_id, side_effect, uml_id), []).append(freq)

    for drug_id in drug_ids:
        for reaction in reactions:
            uml_ids = uml_map.get((drug_id, reaction), [])
            for uml_id in uml_ids:
                freqs = freq_map.get((drug_id, reaction, uml_id), [])
                frequency_str = format_frequencies(freqs)
                results.setdefault(drug_id, []).append({
                    "code": uml_id,
                    "sideEffect": reaction,
                    "frequency": frequency_str
                })
 
    return [{"ID": drug_id, "sideEffects": se_list} for drug_id, se_list in results.items()]
 
def format_frequencies(freqs):
    if not freqs:
        return "unknown"
 
    floats, texts = [], []
    for f in freqs:
        try:
            floats.append(float(f))
        except ValueError:
            texts.append(f.strip())
 
    frequency_parts = []
 
    if floats:
        min_f, max_f = min(floats) * 100, max(floats) * 100
        if min_f == max_f:
            frequency_parts.append(f"{min_f:.1f}%")
        else:
            frequency_parts.append(f"{min_f:.1f}% - {max_f:.1f}%")
 
    if texts:
        frequency_parts.extend(texts)
 
    return ", ".join(frequency_parts) if frequency_parts else "unknown"
 
 
def get_drug_side_effects(drug_ids: list, sideEff_ttl: str, suspect: bool):
        g.parse(sideEff_ttl, format="turtle")
        drug_filter = " ".join(f'"{id}"' for id in drug_ids)
        target = ""
        if suspect: 
            target = "http://example.org/graph/extract_meddra_indication_suspect"
        else:
            target = "http://example.org/graph/extract_meddra_indication_concomitant"
        endpoint = "http://localhost:6060/api/analysis/odrl-execute"
        odrl_data = f"""
        @prefix odrl:   <http://www.w3.org/ns/odrl/2/> .
        @prefix ex:     <http://example.org/> .

        <http://example.org/request:se-query>
            a odrl:Request ;
            odrl:uid <https://www.wikidata.org/wiki/Q25670> ;
            odrl:profile <https://www.wikidata.org/wiki/Q4382010> ;

            odrl:permission [
                odrl:target <{target}> ;
                odrl:assignee ex:researcher ;
                odrl:action odrl:read

            ] .
        """
        side_eff_query = send_odrl_request(endpoint, odrl_data)
        results = g.query(side_eff_query)
        sparql_json = json.loads(results.serialize(format='json').decode('utf-8'))

        drug_side_effects = {}
        for binding in sparql_json["results"]["bindings"]:
            d_id = binding["drug_id"]["value"]
            indication = binding["indication"]["value"]
            uml_code = binding["uml_codes"]["value"]
            if d_id in drug_ids:
                if d_id not in drug_side_effects:
                    drug_side_effects[d_id] = []
 
                # Ensure uniqueness by tracking codes
                if uml_code not in [entry["code"] for entry in drug_side_effects[d_id]]:
                    drug_side_effects[d_id].append({
                        "code": uml_code,
                        "indication": indication
                    })
 
        # Change result structure
        result = [
            {"ID": drug_id, "indications": effects}
            for drug_id, effects in drug_side_effects.items()
        ]
 
        return result
 
def merge_drug_data_with_side_effects(freq_data, indication_data, id_to_name_wrapped):
    combined = {}
    role_key = next(iter(id_to_name_wrapped))  # 'suspected' or 'concomitant'
    id_to_name = id_to_name_wrapped[role_key] 
 
    for item in freq_data:
        drug_id = item["ID"]
        if drug_id not in combined:
            combined[drug_id] = {
                role_key: {
                    "ID": drug_id,
                    "name": id_to_name.get(drug_id, "")
                }
            }
        combined[drug_id][role_key]["sideEffects"] = item.get("sideEffects", [])
 
    for item in indication_data:
        drug_id = item["ID"]
        if drug_id not in combined:
            combined[drug_id] = {
                role_key: {
                    "ID": drug_id,
                    "name": id_to_name.get(drug_id, "")
                }
            }
        combined[drug_id][role_key]["indications"] = item.get("indications", [])
 
    return list(combined.values())
 
with open(ADRData, "r") as f:
    processed_data = json.load(f)
 
with open(vigiData, "r") as f:
    vigi_data = json.load(f)


suspect_drugs = (processed_data[0]["ATCText"]) or ""
other_suspect_drugs = (processed_data[0]["Other_suspect_ATCText"]) or ""
suspected_drugs = suspect_drugs+";"+other_suspect_drugs
 
concomitant_drugs = (processed_data[0]["Concomitant_ATCText"]) or ""
 
 
# merge data from the adr case and vigi data
final_suspected_drugs = merge_drugs_universal(suspected_drugs, vigi_data, role_type="suspect")
final_concomitant_drugs = merge_drugs_universal(concomitant_drugs, vigi_data, role_type="concomitant")
 
reaction_pt = (processed_data[0]["Reaction_PT"]) or ""
other_reaction_pt = (processed_data[0]["Other_Reported_PTs"]) or ""
reaction_pts = reaction_pt+";"+other_reaction_pt
 
 
drug_infos = get_drug_id_by_name(final_suspected_drugs, drug_names, True)
drug_ids = [info["ID"] for info in drug_infos]
id_to_name_suspect = {"suspected": {info["ID"]: info["name"] for info in drug_infos}}
drug_data = check_drug_ids_in_meddra(drug_ids, meddra_freq, reaction_pts, meddra_all_label_se, True)
drug_data_sideeff = get_drug_side_effects(drug_ids, SideEff, True)
merged_data_suspects = merge_drug_data_with_side_effects(drug_data, drug_data_sideeff, id_to_name_suspect)

concomitant_infos = ""
concomitant_ids = ""
id_to_name_concomitant = {"concomitant": {}}
concomitant_data = ""
concomitant_data_sideeff = ""
merged_data_concomitant = ""
if final_concomitant_drugs :
    concomitant_infos = get_drug_id_by_name(final_concomitant_drugs, drug_names, False)
    concomitant_ids = [info["ID"] for info in concomitant_infos]
    id_to_name_concomitant = {"concomitant": {info["ID"]: info["name"] for info in concomitant_infos}}
    concomitant_data = check_drug_ids_in_meddra(concomitant_ids, meddra_freq, reaction_pts, meddra_all_label_se, False)
    concomitant_data_sideeff = get_drug_side_effects(concomitant_ids, SideEff, False)
    merged_data_concomitant = merge_drug_data_with_side_effects(concomitant_data, concomitant_data_sideeff, id_to_name_concomitant)


 
# merge the two jsons into one
final_merged = defaultdict(dict)
 
for dataset in (merged_data_suspects, merged_data_concomitant):
    for entry in dataset:
        for role, data in entry.items():
            final_merged[data["ID"]][role] = data
 
final_merged_list = list(final_merged.values())
 
with open('Output/SideEff.json', 'w', encoding='utf-8') as f:
    json.dump(final_merged_list, f, ensure_ascii=False, indent=2)
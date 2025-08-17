from collections import defaultdict
from rdflib import Graph, Literal
import streamlit as st
import pandas as pd
import json
from streamlit_agraph import agraph, Node, Edge, Config


st.set_page_config(layout="wide")

with open("output/vigiData.json", "r") as f:
    vigi_data = json.load(f)
    
with open("output/ADRData.json", "r") as f:
    processed_data = json.load(f)

with open("output/SideEff.json") as f:
    side_effects_data = json.load(f)
    
processed_data = processed_data[0]

with open("output/atc_hierarchy.json") as f:        
    atc_levels = json.load(f)
    
drug_to_level3 = {}
for item in atc_levels:
    if item.get("level") != 3:
        continue

    names = [n.strip() for n in item["drugNames"].split(",")]
    codes = [c.strip() for c in item["drugIds"].split(",")]

    for name, code in zip(names, codes):
        if name:
            drug_to_level3[name.lower()] = {
                "parentCode":  item["parentCode"],  
                "parentName":  item["parentName"],
                "drugCode":    code                 
            }

# Extract Lareb data from ttl file
g = Graph()
g.parse("output/extractDataFromL.ttl", format="turtle")

query = """
PREFIX ex: <http://example.org/>

CONSTRUCT {
  ?s ex:ATCText ?atcText .
  ?s ex:Concomitant_ATCText ?concomitant .
  ?s ex:Other_Reported_PTs ?otherPTs .
  ?s ex:Reaction_PT ?reactionPT .
  ?s ex:Other_suspect_ATCText ?otherSuspects .
}
WHERE {
  ?s ex:WorldwideUniqueCaseIdentification ?id .
  FILTER (str(?id) != "patient 0")

  OPTIONAL { ?s ex:ATCText ?atcText }
  OPTIONAL { ?s ex:Concomitant_ATCText ?concomitant }
  OPTIONAL { ?s ex:Other_Reported_PTs ?otherPTs }
  OPTIONAL { ?s ex:Reaction_PT ?reactionPT }
  OPTIONAL { ?s ex:Other_suspect_ATCText ?otherSuspects }
}
"""

# Color mapping for node types
ROLE_COLORS = {
        "Suspect": "#FF5733",       
        "Concomitant": "#337AFF",          
        "Reaction": "#31A8D6",       
        "ATC_L3": "#FFC72C",
        "TTL_Suspect": "#EC8703",   
        "TTL_Concomitant": "#AA0BEE",     
        "TTL_Reaction": "#28B463",
        "TTL_ATC_L3": "#796F56",
    }

# Legend mapping of nodes
LEGEND_LABELS = {
    "Suspect": "Suspected drug (VigiLyze)",
    "Concomitant": "Concomitant drug (VigiLyze)",
    "Reaction": "drug reaction (VigiLyze)",
    "ATC_L3": "ATC Level 3 for concomitant drug(s)",
    "TTL_Suspect": "Suspected drug (Lareb)",
    "TTL_Concomitant": "Concomitant drug (Lareb)",
    "TTL_Reaction": "Drug reaction (ADR/Lareb)",
    "TTL_ATC_L3": "ATC Level 3 (Lareb)",
}

DRUG_EDGE_COLOR = "#BBBBBB"   # Drug → Reaction
ATC_EDGE_COLOR  = "#FFD700"   # ATC L3 → Reaction
EDGE_STYLES = {
    "drug_to_reaction": {"color": DRUG_EDGE_COLOR, "label": "Drug → Reaction"},
    "atc_to_reaction":  {"color": ATC_EDGE_COLOR,  "label": "ATC L3 → Reaction"},
}
# Font and style config
DEFAULT_FONT = {"size": 18, "color": "#FFFFFF"}

# Initialize the list of nodes and edges for the graph
nodes = []
edges = []
node_ids = set()
edge_ids = set()

# split and clean text
def split_and_clean(text):
    if isinstance(text, str):
        return [t.strip() for t in text.split(";") if t.strip()]
    return []

def normalize(text):
    return text.strip().lower() if isinstance(text, str) else ""

# Add drug nodes based on processed_data
atc_details = defaultdict(lambda: defaultdict(lambda: {"code": None, "reactions": set()}))

# Temporary storage to group all object values by predicate for each subject
subject_values = defaultdict(lambda: defaultdict(list))

# Group values by subject and predicate
results_graph = g.query(query) 
for s, p, o in results_graph:
    if not isinstance(o, Literal):
        continue

    subj_id = str(s)
    pred = str(p)
    values = [v.strip().lower()  for v in str(o).split(";") if v.strip().lower() != "nan" and v.strip()]
    subject_values[subj_id][pred].extend(values)

# For each subject, connect drugs to reactions
for subj_id, pred_obj_map in subject_values.items():
    # Extract all drugs and reactions from the predicates
    suspect_drugs = pred_obj_map.get("http://example.org/ATCText", []) + \
                    pred_obj_map.get("http://example.org/Other_suspect_ATCText", [])

    concomitant_drugs = pred_obj_map.get("http://example.org/Concomitant_ATCText", [])

    reactions = pred_obj_map.get("http://example.org/Reaction_PT", []) + \
                pred_obj_map.get("http://example.org/Other_Reported_PTs", [])

    # Add nodes and connect suspects to reactions
    for drug in suspect_drugs:
        drug_id = drug.lower()
        if drug_id not in node_ids:
            nodes.append(Node(id=drug_id, label=drug, size=22,
                              color=ROLE_COLORS["TTL_Suspect"], font=DEFAULT_FONT, level=1))
            node_ids.add(drug_id)

        for reaction in reactions:
            reaction_id = reaction.lower()
            if reaction_id not in node_ids:
                nodes.append(Node(id=reaction_id, label=reaction, size=22,
                                  color=ROLE_COLORS["TTL_Reaction"], font=DEFAULT_FONT, level=2))
                node_ids.add(reaction_id)

            edge_key = (drug_id, reaction_id)
            if edge_key not in edge_ids:
                edges.append(Edge(source=drug_id, target=reaction_id, color=DRUG_EDGE_COLOR, width=2, arrows="to"))
                edge_ids.add(edge_key)

    # Connect concomitants
    for drug in concomitant_drugs:
        drug_id = drug.lower()

        # Look up ATC L3 info
        atc = drug_to_level3.get(drug_id)
        if not atc:
            continue  # Skip if not found

        atc_id    = atc["parentCode"]
        atc_label = atc["parentName"]
        atc_code  = atc["drugCode"]
        atc_node  = f"{atc_id}, {atc_label}"

        for reaction in reactions:
            reaction_id = reaction.lower()

            # Update atc_details structure
            entry = atc_details[atc_id][drug_id]
            entry["atc_code"] = atc_code
            entry["reactions"].add(reaction)

            # Add ATC node
            if atc_node not in node_ids:
                nodes.append(Node(id=atc_node, label=atc_label, size=30,
                                color=ROLE_COLORS["TTL_ATC_L3"], font=DEFAULT_FONT, level=3))
                node_ids.add(atc_node)

            # Add Reaction node (if not already present)
            if reaction_id not in node_ids:
                nodes.append(Node(id=reaction_id, label=reaction, size=22,
                                color=ROLE_COLORS["TTL_Reaction"], font=DEFAULT_FONT, level=2))
                node_ids.add(reaction_id)

            # Add edge: ATC to Reaction
            edge_key = (atc_node, reaction_id)
            if edge_key not in edge_ids:
                edges.append(Edge(source=atc_node, target=reaction_id,
                                color=ATC_EDGE_COLOR, width=2, arrows="to"))
                edge_ids.add(edge_key)



all_relevant_reactions = set()
reaction_pts = split_and_clean(processed_data.get("Reaction_PT", ""))
other_reported_pts = split_and_clean(processed_data.get("Other_Reported_PTs", ""))

# Normalize before adding
for r in reaction_pts + other_reported_pts:
    all_relevant_reactions.add(normalize(r))


irrelevant_suspect_drug_reactions = defaultdict(set)
mapped_suspected_drug_reactions = defaultdict(set)
# Iterate through outcomes and add drugs based on their role
for outcome in vigi_data["outcomes"]:
    reaction = outcome.get("reaction", "").strip()
    outcome_ids = outcome.get("ID", [])
    for drug in vigi_data["drugs"]: 
        drug_ids = drug.get("ID", [])
        role = drug.get("role", "").lower()  # suspect or concomitant
        drug_name = drug.get("drug", "").lower()

        # Check if drug IDs match any of the outcome IDs
        if any(drug_id in outcome_ids for drug_id in drug_ids):
            if role == "suspect" and normalize(reaction) not in all_relevant_reactions:
                    irrelevant_suspect_drug_reactions[drug_name].add(reaction)
            
            if normalize(reaction) in all_relevant_reactions:
                
                # Add reaction node
                if not any(node.id == reaction for node in nodes):
                    nodes.append(Node(id=reaction, label=reaction, size=25,
                                    color=ROLE_COLORS["Reaction"], font=DEFAULT_FONT, level=2))

                # Add drug node, color code based on role
                if not any(node.id == drug_name for node in nodes):
                    if role == "suspect":
                        color = ROLE_COLORS["Suspect"]
                        drug_level = 1  # Suspect drugs
                        
                        nodes.append(Node(id=drug_name, label=drug_name, size=25,
                                    color=color, font=DEFAULT_FONT, level=drug_level)) 
                    elif role == "concomitant":
                        atc = drug_to_level3.get(drug_name)   
                        if atc:
                            atc_id    = atc["parentCode"]      
                            atc_label = atc["parentName"]
                            
                            entry = atc_details[atc_id][drug_name]
                            entry["atc_code"] = atc["drugCode"]
                            entry["reactions"].add(reaction)
                            
                            atc_node = f"{atc_id}, {atc_label}"

                            # add the ATC node
                            if not any(node.id == atc_node for node in nodes):
                                nodes.append(Node(id=atc_node, label=atc_label, size=30,
                                                color=ROLE_COLORS["ATC_L3"], font=DEFAULT_FONT,
                                                level=3))

                            # edge: ATC class to reaction 
                            if not any(e.source == atc_node and e.to == reaction for e in edges):
                                edges.append(Edge(source=atc_node, target=reaction,
                                                color=ATC_EDGE_COLOR, width=2, arrows="to"))

                # Add an edge from the drug to the reaction (drug → reaction)
                if role == "suspect":
                    mapped_suspected_drug_reactions[drug_name].add(reaction)
                    edges.append(Edge(source=drug_name, target=reaction, color=DRUG_EDGE_COLOR, width=2, arrows="to")) 




def render_legend():
    st.markdown("### Legend")

    # Node legend (use Streamlit columns like the rest of your UI)
    cols = st.columns(3)
    for i, (role, color) in enumerate(ROLE_COLORS.items()):
        label = LEGEND_LABELS.get(role, role)
        with cols[i % 3]:
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
                    <div style="width:16px;height:16px;border-radius:50%;
                                border:1px solid rgba(255,255,255,0.35);
                                background:{color};"></div>
                    <span style="font-size:14px;">{label}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Edge legend (SVG lines with arrowheads, matching colors)
    st.write("**Edges:**")
    edge_cols = st.columns(len(EDGE_STYLES))
    for i, (key, meta) in enumerate(EDGE_STYLES.items()):
        color = meta["color"]
        label = meta["label"]
        # Unique marker id per item to avoid collisions
        marker_id = f"arrow_{i}"
        svg = f"""
        <svg width="110" height="22" xmlns="http://www.w3.org/2000/svg" style="display:block;">
          <defs>
            <marker id="{marker_id}" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L0,8 L8,4 z" fill="{color}"/>
            </marker>
          </defs>
          <line x1="6" y1="11" x2="98" y2="11" stroke="{color}" stroke-width="3" marker-end="url(#{marker_id})" />
        </svg>
        """
        with edge_cols[i]:
            st.markdown(svg, unsafe_allow_html=True)
            st.markdown(f"<div style='margin-top:-6px;font-size:14px;'>{label}</div>", unsafe_allow_html=True)


# Configure and render the graph
config = Config(
    width=1500,
    height=400,
    directed=True,
    physics=False,        
    hierarchical=True,
    layout={
        "hierarchical": {
            "enabled": True,
            "direction": "UD",
            "sortMethod": "directed",
            "levelSeparation": 290,   # ← default 150
            "nodeSpacing":      170,  # ← default 100
            "treeSpacing":      400   # ← extra room between branches
        }
    },
)

st.title("Drug Graph")
st.subheader("Graph was generated using data from the ADR,Lareb, VigiLyze and Sider databases")
st.write(f"VigiLyze records used {vigi_data['recordsUsed']}")

render_legend() 
graph_result = agraph(nodes=nodes, edges=edges, config=config)

def get_drug_info(drug_name):

    # Loop through the data and find the suspected or concomitant drug information
    for entry in side_effects_data:
        drug_data = entry.get("suspected")
        if drug_data:
            if drug_data["name"].lower() == drug_name.lower():
                
                return drug_data
    return None

if graph_result:
    drug_name = graph_result.split(",")
  
    # Get drug information from the SideEff.json
    drug_info = get_drug_info(drug_name[0])

    if not drug_info:  
        drug_info = {"ID": "XXX", "name": drug_name[0]}

    if drug_info and (len(drug_name) == 1):
         # Display the ID and Name of the drug
        col1, col2, col3 = st.columns([3,1, 1])
        with col1:
            st.write(f"**Drug ID:** {drug_info['ID']}")
            st.write(f"**Drug Name:** {drug_info['name']}")
        with col2:
            table_option = st.radio(
                "Table Type:",
                ("Matched vigiData reactions with ADR", "Unmatched vigiData reactions with ADR" ),
                index=0
            )
        try:
            with col3:
                reaction_filter_option = st.radio(
                    "Match Filter:",
                    ("Show all", "Only found in SIDER", "Only missing in SIDER"),
                    index=0
                )
            st.write("### Side Effects")
            if table_option == "Matched vigiData reactions with ADR":
                vigi_reactions = mapped_suspected_drug_reactions.get(drug_info["name"].lower(), set())
                table_title = "VigiData matched reactions with ADR"
            else:
                vigi_reactions = irrelevant_suspect_drug_reactions.get(drug_info["name"].lower(), set())
                table_title = "Unmatched vigiData Reactions with ADR)"

            # Build side effect lookup
            sider_effects = {
                se["sideEffect"].strip().lower(): se["frequency"]
                for se in drug_info.get("sideEffects", [])
            }

            side_effects_table = []

            for reaction in vigi_reactions:
                normalized = reaction.strip().lower()

                if normalized in sider_effects:
                    side_effects_table.append({
                        "vigiDataReaction": reaction,
                        "siderDataReaction": reaction,
                        "Frequency": sider_effects[normalized]
                    })
                else:
                    side_effects_table.append({
                        "vigiDataReaction": reaction,
                        "siderDataReaction": "missing data from SIDER",
                        "Frequency": "-"})
            
            # Apply filtering logic
            if reaction_filter_option == "Only found in SIDER":
                side_effects_table = [
                    row for row in side_effects_table if row["siderDataReaction"] != "missing data from SIDER"
                ]
            elif reaction_filter_option == "Only missing in SIDER":
                side_effects_table = [
                    row for row in side_effects_table if row["siderDataReaction"] == "missing data from SIDER"
                ]
            st.dataframe(side_effects_table, use_container_width=True)
        except:
            st.write("### No side effects are found")
        
        # Indications table
        try:
            indications = drug_info["indications"]
            st.write("### Indications")
            indications_data = [(ind["indication"],) for ind in indications]
            st.table(indications_data)
        except:
            st.write("### No indications are found")
        
    if drug_name[0] in atc_details:
        st.markdown(f"### ATC code **{drug_name[0]}**, Name {drug_name[1]} ")
        rows = []
        for drug, info in atc_details[drug_name[0]].items():
            rows.append({
                "Drug"      : drug,
                "ATC-5 code": info["atc_code"],
                "Reactions" : ", ".join(sorted(info["reactions"]))
            })
        
        st.table(pd.DataFrame(rows))
                

        
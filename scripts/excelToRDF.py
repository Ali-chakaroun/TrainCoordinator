from pathlib import Path
import pandas as pd
from rdflib import Graph, Literal, Namespace, URIRef

# Load the Excel file
excel_file = "Excel/LDataCustom.xlsx"

# Initialize the base namespace for RDF
BASE = Namespace("http://example.org/")

# Load all sheets into a dictionary of DataFrames
sheets = pd.read_excel(excel_file, sheet_name=None)

# Loop through each sheet and convert to RDF
for sheet_name, df in sheets.items():
    # Initialize RDF graph for each sheet
    g = Graph()
    g.bind("ex", BASE)
    
    # For each row in the current sheet (order preserved)
    for idx, row in df.iterrows():
        subject_uri = URIRef(f"{BASE}{sheet_name}_row/{idx + 1}")
        
        # For each column in the row, add a triple
        for col in df.columns:
            predicate_uri = URIRef(f"{BASE}{col.strip().replace(' ', '_')}")
            value = row[col]
            
            # Add the triple to the RDF graph
            obj = Literal(str(value))
            g.add((subject_uri, predicate_uri, obj))
    
    # Save the RDF graph for the current sheet to a TTL file
    base_name = Path(excel_file).stem
    ttl_filename = f"RDF/{base_name}.ttl"
    g.serialize(destination=ttl_filename, format="turtle")
    print(f"RDF for sheet '{sheet_name}' saved to {ttl_filename}")

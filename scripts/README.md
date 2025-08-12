# Prototype Analysis Scripts 📜

This folder contains the **Python scripts** and **Dockerfile** used in the **prototype Train Coordinator service** for the FAIR Data Train framework.  

These scripts are responsible for:  
- Extracting and processing RDF/TTL datasets.  
- Executing **ODRL policy checks** before running SPARQL queries.  
- Performing data aggregation, filtering, and merging from multiple sources.  
- Integrating with **CWL workflows** to support automated, privacy-preserving data analysis.  

---

## 📂 Contents

| File / Folder | Description |
|---------------|-------------|
| `*.py` | Python scripts for RDF parsing, SPARQL querying, and result aggregation. |
| `Dockerfile` | Container definition to run the scripts in a reproducible environment. |
| `Excel/` | **Dummy Excel data** used for prototype testing (mock data only — the real dataset is under NDA). |

---

## 🔐 Data Disclaimer

Due to **NDA restrictions**, the real datasets used during testing are **not included** in this repository.  
The `Excel/` folder contains mock data with the same schema for demonstration.


---

## 🐳 Running in Docker

To build and run the containerized scripts:
```bash
docker build -t extract-adr .
docker run --network=host extract-adr


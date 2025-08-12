# Train Coordinator 🚆 (Prototype)

This is a **prototype Train Coordinator service** designed for orchestrating workflows and enforcing access control in **privacy-preserving data analysis** for federated healthcare environments.  

This project extends the **FAIR Data Train (FDT)** framework by integrating:  
- **Common Workflow Language (CWL)** for multi-step workflow execution.  
- **Open Digital Rights Language (ODRL)** for fine-grained data access control.  
---

## 📌 Features

- **Automated multi-step analysis** — chain multiple trains with conditional execution.  
- **Policy-based access control** — enforce data retrieval policies usage with ODRL.  
- **Reusable workflows** — built using CWL for portability and reproducibility.



| Endpoint                                          | Method | Description                                                                                                                                                         |
| ------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `http://localhost:6060/api/analysis/execute`      | `POST` | Executes a CWL workflow and returns the result.                                                                                                                     |
| `http://localhost:6060/api/analysis/odrl-execute` | `POST` | Executes an ODRL policy request and returns the corresponding SPARQL query. *(Note: CWL workflows internally call this endpoint when verifying train permissions.)* |

cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python", "/app/extractSideEFF_RDF.py"]

requirements:
  DockerRequirement:
    dockerPull: extract-sideeff-data  # Docker image name
  NetworkAccess:
    networkAccess: true
inputs:
  drug_names:
    type: File
    default:
      class: File
      location: RDF/drug_names.ttl
    inputBinding:
      position: 1
  meddra_freq:
    type: File
    default:
      class: File
      location: RDF/meddra_freq.ttl
    inputBinding:
      position: 2
  meddra_all_label_se:
    type: File
    default:
      class: File
      location: RDF/meddra_all_label_se.ttl
    inputBinding:
      position: 3
  SideEff:
    type: File
    default:
      class: File
      location: RDF/SideEff.ttl
    inputBinding:
      position: 4
  adrData:
    type: File
    inputBinding:
      position: 5
  vigiData:
    type: File
    inputBinding:
      position: 6     
  
outputs:
  sideEffData:
    type: File
    outputBinding:
      glob: "Output/SideEff.json" 
  


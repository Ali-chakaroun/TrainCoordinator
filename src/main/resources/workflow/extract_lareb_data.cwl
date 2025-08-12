cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python", "/app/extractData_RDF.py"]

requirements:
  DockerRequirement:
    dockerPull: extract-lareb-data  # Docker image name
  NetworkAccess:
    networkAccess: true
    
inputs:
  adrData:
    type: File
    inputBinding:
      position: 1
  LData:
    type: File
    default:
      class: File
      location: RDF/LData.ttl
    inputBinding:
      position: 2
  
outputs:
  larebData:
    type: File
    outputBinding:
      glob: "Output/extractDataFromL.ttl"  # Assuming output JSON file name
  
  larebMetadata:
    type: File
    outputBinding:
      glob: "Output/ADRDataRecords.json"  # Assuming output metadata file name

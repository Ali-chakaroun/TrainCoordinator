cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python", "/app/extractADR_RDF.py"]


requirements:
  DockerRequirement:
    dockerPull: extract-adr 
  NetworkAccess:
    networkAccess: true
inputs:
  src:
    type: File
    inputBinding:
      position: 1
    default: 
      class: File
      location: "RDF/ADRCase.ttl" 

outputs:
  data:
    type: File
    outputBinding:
      glob: "Output/ADRData.json"

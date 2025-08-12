cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python", "/app/extractVigi_RDF.py"]

requirements:
  DockerRequirement:
    dockerPull: extract-vigi-data 
  NetworkAccess:
    networkAccess: true
inputs:
  ViData:
    type: File
    default:
      class: File
      location: RDF/ViData.ttl
    inputBinding:
      position: 1
  adrData:
    type: File
    inputBinding:
      position: 2
  atc_hierarchy:
    type: File
    default:
      class: File
      location: RDF/atc_hierarchy.ttl
    inputBinding:
      position: 3

outputs:
  vigiData:
    type: File
    outputBinding:
      glob: "Output/vigiData.json" 
  
  vigiExcel:
    type: File
    outputBinding:
      glob: "Output/vigiDataExcel.json"  

  vigiATC:
    type: File
    outputBinding:
      glob: "Output/atc_hierarchy.json"  
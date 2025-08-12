cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python", "/app/extractADR_RDF.py"]


requirements:
  DockerRequirement:
    dockerPull: extract-adr  # this must match the name you built with: `docker build -t extract-adr .`
  NetworkAccess:
    networkAccess: true
inputs:
  src:
    type: File
    inputBinding:
      position: 1
    default: 
      class: File
      location: "RDF/ADRCase.ttl"  # Default RDF file path inside the Docker container
      basename: "ADRCase.ttl"  # Specify a basename for the file
      contents: "This is the RDF file"  # You can leave it blank if it's only the file path that matters

outputs:
  data:
    type: File
    outputBinding:
      glob: "Output/ADRData.json"

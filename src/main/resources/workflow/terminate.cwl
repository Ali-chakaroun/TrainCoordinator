cwlVersion: v1.2
class: CommandLineTool
baseCommand: [bash, -lc]

inputs:
  records: int

arguments:
  - valueFrom: |
      printf '{"status":"terminated, Lareb database contains enough records on the specified ADR","records":%s}\n' $(inputs.records) > terminate.json
    shellQuote: false

outputs:
  terminateData: 
    type: File
    outputBinding:
      glob: terminate.json

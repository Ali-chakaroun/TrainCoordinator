cwlVersion: v1.2
class: Workflow
#cwltool --custom-net=host --outdir output main.cwl  the command to run the script
requirements:
  InlineJavascriptRequirement: {}
  MultipleInputFeatureRequirement: {}
  StepInputExpressionRequirement: {}
  SubworkflowFeatureRequirement: {}

inputs: []

steps:
  extractADR:
    run: extract_adr.cwl
    in: []
    out:
      - data

  extractLarebData:
    run: extract_lareb_data.cwl
    in:  
      adrData: 
        source: extractADR/data
    out:
      - larebData
      - larebMetadata

  terminate:
    in:
      records:
        source: extractLarebData/larebMetadata
        loadContents: true
        valueFrom: $(JSON.parse(self.contents).records)
    when: $(inputs.records > 5)
    run: terminate.cwl
    out: 
      - terminateData

  data_analysis:
    in:
      adrData:
        source: extractADR/data
      records:
        source: extractLarebData/larebMetadata
        loadContents: true
        valueFrom: $(JSON.parse(self.contents).records)
    when: $(inputs.records <= 5)
    run: vigi_analysis.cwl
    out: [vigiData, vigiExcel, vigiATC, sideEffData]


outputs:
  data:
    type: ["null","File"]
    outputSource: extractADR/data
  larebData:
    type: ["null","File"]
    outputSource: extractLarebData/larebData
  larebMetadata:
    type: ["null","File"]
    outputSource: extractLarebData/larebMetadata
  terminateData:
    type: ["null","File"]
    outputSource: terminate/terminateData
  vigiData:
    type: ["null","File"]
    outputSource: data_analysis/vigiData
  vigiExcel:
    type: ["null","File"]
    outputSource: data_analysis/vigiExcel
  vigiATC:
    type: ["null","File"]
    outputSource: data_analysis/vigiATC
  sideEffData:
    type: ["null","File"]
    outputSource: data_analysis/sideEffData
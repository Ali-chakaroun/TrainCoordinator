cwlVersion: v1.2
class: Workflow

requirements:
  InlineJavascriptRequirement: {}
  MultipleInputFeatureRequirement: {}
  StepInputExpressionRequirement: {}

inputs:
  adrData:
    type: File

steps:
  extractVigiData:
    run: extract_vigi_data.cwl
    in:
      adrData: adrData
    out: [vigiData, vigiExcel, vigiATC]

  extractSideEffData:
    run: extract_sideeff_data.cwl
    in:
      adrData: adrData
      vigiData: extractVigiData/vigiData
    out: [sideEffData]

outputs:
  vigiData:
    type: File
    outputSource: extractVigiData/vigiData
  vigiExcel:
    type: File
    outputSource: extractVigiData/vigiExcel
  vigiATC:
    type: File
    outputSource: extractVigiData/vigiATC
  sideEffData:
    type: File
    outputSource: extractSideEffData/sideEffData

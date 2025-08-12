package com.example.traincoordinator;


import com.example.traincoordinator.service.ConditionalAnalysisService;
import com.example.traincoordinator.service.ODRLService;

import org.springframework.web.bind.annotation.*;

import java.util.Map;

import org.springframework.http.ResponseEntity;

@RestController
@RequestMapping("/api/analysis")
public class ConditionalAnalysisController {

    private final ConditionalAnalysisService analysisService;
    private final ODRLService odrlService;
    public ConditionalAnalysisController(ConditionalAnalysisService analysisService,  ODRLService odrlService) {
        this.analysisService = analysisService;
        this.odrlService = odrlService;
    }

    @PostMapping("/execute")
    public ResponseEntity<?> executeAnalysis() {
        try {
            Map<String, Object> result = analysisService.executeAnalysis();
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                .body(Map.of(
                    "error", "Analysis failed",
                    "details", e.getMessage().replaceAll("\\x1B\\[[0-?]*[ -/]*[@-~]", "")
                ));
        }
    }
    @PostMapping("/odrl-execute")
    public ResponseEntity<?> executeODRL(@RequestBody String odrlPolicyTurtle) {
        try {
            String result = odrlService.executeODRLPolicy(odrlPolicyTurtle);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                .body(Map.of(
                    "error", "ODRL policy enforcement failed",
                    "details", e.getMessage().replaceAll("\\x1B\\[[0-?]*[ -/]*[@-~]", "")
                ));
        }
    }

}
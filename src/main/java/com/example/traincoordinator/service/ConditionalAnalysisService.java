package com.example.traincoordinator.service;

import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class ConditionalAnalysisService {
    
    private final ObjectMapper objectMapper = new ObjectMapper();
    public Map<String, Object> executeAnalysis() {
        try {
            Path workflowPath = new ClassPathResource("workflow/main.cwl")
                .getFile().toPath();
            
            ProcessOutput output = executeCwlTool(workflowPath);
            
            if (output.exitCode == 0) {
                return parseValidJson(output.stdout);
            } else {
                throw new RuntimeException("CWL Execution Failed:\n" + output.stderr);
            }
            
        } catch (Exception e) {
            throw new RuntimeException("Analysis failed: " + cleanErrorMessage(e.getMessage()));
        }
    }

    private ProcessOutput executeCwlTool(Path workflowPath) 
            throws IOException, InterruptedException {
        
        ProcessBuilder pb = new ProcessBuilder(
            "cwltool",
            "--custom-net=host",
            "--outdir=output",
            workflowPath.toString()
        );

        Process process = pb.start();
        
        String stdout = readStream(process.getInputStream());
        String stderr = readStream(process.getErrorStream());
        int exitCode = process.waitFor();
        
        return new ProcessOutput(exitCode, stdout, stderr);
    }
    // Add the missing readStream method
    private String readStream(InputStream stream) throws IOException {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream))) {
            return reader.lines().collect(java.util.stream.Collectors.joining("\n"));
        }
    }

    private Map<String, Object> parseValidJson(String rawOutput) throws IOException {
        int jsonStart = rawOutput.indexOf("{");
        int jsonEnd = rawOutput.lastIndexOf("}") + 1;
        
        if (jsonStart == -1 || jsonEnd == -1) {
            throw new IOException("No valid JSON found in output");
        }
        
        String json = rawOutput.substring(jsonStart, jsonEnd);
        return objectMapper.readValue(json, Map.class);
    }

    private String cleanErrorMessage(String message) {
        return message.replaceAll("\\x1B\\[[0-?]*[ -/]*[@-~]", "")
                      .replaceAll("\\bINFO\\b", "")
                      .replaceAll("\\bWARNING\\b", "")
                      .trim();
    }

    // Process output handling
    private static class ProcessOutput {
        final int exitCode;
        final String stdout;
        final String stderr;

        ProcessOutput(int exitCode, String stdout, String stderr) {
            this.exitCode = exitCode;
            this.stdout = stdout;
            this.stderr = stderr;
        }
    }
}

package com.example.traincoordinator.service;

import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.file.Path;

@Service
public class ODRLService {

    public String executeODRLPolicy(String odrlTurtleString) throws IOException, InterruptedException {
        Path odrlPath = new ClassPathResource("ODRL/main.py")
                .getFile().toPath();
        ProcessBuilder pb = new ProcessBuilder("python", odrlPath.toString());

        Process process = pb.start();

        // Send the user request to the odrl engine
        BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(process.getOutputStream()));
        writer.write(odrlTurtleString);
        writer.flush();
        writer.close();

        // Read output
        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        StringBuilder output = new StringBuilder();
        System.out.println(output);
        String line;
        while ((line = reader.readLine()) != null) {
            output.append(line).append("\n");
        }
        BufferedReader errorReader = new BufferedReader(new InputStreamReader(process.getErrorStream()));
        StringBuilder errorOutput = new StringBuilder();
        while ((line = errorReader.readLine()) != null) {
            errorOutput.append(line).append("\n");
        }
        if (errorOutput.length() > 0) {
            System.err.println("Python error output:\n" + errorOutput);
        }

        int exitCode = process.waitFor();
        if (exitCode != 0) {
            throw new RuntimeException("Python process failed with exit code " + exitCode);
        }

        String result = (output.toString().trim());
        return result;
    }
}

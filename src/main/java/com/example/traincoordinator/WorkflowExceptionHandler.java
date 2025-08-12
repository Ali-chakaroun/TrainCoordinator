package com.example.traincoordinator;

import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.http.ResponseEntity;
import java.util.Map;

@RestControllerAdvice
public class WorkflowExceptionHandler {
    
    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<Map<String, String>> handleWorkflowException(RuntimeException ex) {
        return ResponseEntity.badRequest()
            .body(Map.of(
                "error", "Workflow execution error",
                "message", ex.getMessage()
            ));
    }
}
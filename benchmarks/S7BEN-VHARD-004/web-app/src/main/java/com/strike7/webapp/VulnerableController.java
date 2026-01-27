package com.strike7.webapp;

import org.apache.commons.codec.binary.Base64;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

@RestController
public class VulnerableController {

    @GetMapping("/")
    public Map<String, Object> home() {
        Map<String, Object> response = new HashMap<>();
        response.put("application", "Strike7 Enterprise Portal");
        response.put("version", "1.0.0");
        response.put("endpoints", new String[]{
            "GET /health",
            "POST /login",
            "GET /profile",
            "POST /api/process",
            "GET /api/session"
        });
        return response;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "healthy");
        response.put("service", "web-app");
        return response;
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(
            @RequestBody Map<String, String> credentials,
            HttpServletResponse response) {

        String username = credentials.get("username");
        String password = credentials.get("password");

        Map<String, Object> result = new HashMap<>();

        // Simple authentication (intentionally weak)
        if ("admin".equals(username) && "admin123".equals(password)) {
            // Create session object
            UserSession session = new UserSession(username, "admin", true);

            try {
                // VULNERABLE: Serialize session object to cookie
                String serialized = serializeObject(session);
                Cookie sessionCookie = new Cookie("SESSION", serialized);
                sessionCookie.setPath("/");
                sessionCookie.setMaxAge(3600);
                response.addCookie(sessionCookie);

                result.put("success", true);
                result.put("message", "Login successful");
                result.put("username", username);
                result.put("session", serialized);
                result.put("hint", "Session data is serialized. Check the SESSION cookie!");

                return ResponseEntity.ok(result);
            } catch (Exception e) {
                result.put("success", false);
                result.put("error", e.getMessage());
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(result);
            }
        }

        result.put("success", false);
        result.put("error", "Invalid credentials");
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(result);
    }

    @GetMapping("/profile")
    public ResponseEntity<Map<String, Object>> profile(HttpServletRequest request) {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(new HashMap<String, Object>() {{ put("error", "No session found"); }});
        }

        for (Cookie cookie : cookies) {
            if ("SESSION".equals(cookie.getName())) {
                try {
                    // VULNERABLE: Deserialize user-controlled data without validation
                    Object sessionObj = deserializeObject(cookie.getValue());

                    if (sessionObj instanceof UserSession) {
                        UserSession session = (UserSession) sessionObj;

                        Map<String, Object> profile = new HashMap<>();
                        profile.put("username", session.getUsername());
                        profile.put("role", session.getRole());
                        profile.put("isAdmin", session.isAdmin());

                        return ResponseEntity.ok(profile);
                    }
                } catch (Exception e) {
                    Map<String, Object> error = new HashMap<>();
                    error.put("error", "Session deserialization failed");
                    error.put("message", e.getMessage());
                    return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
                }
            }
        }

        return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
            .body(new HashMap<String, Object>() {{ put("error", "Invalid session"); }});
    }

    @PostMapping("/api/process")
    public ResponseEntity<Map<String, Object>> processData(@RequestBody Map<String, String> payload) {
        String data = payload.get("data");

        if (data == null || data.isEmpty()) {
            return ResponseEntity.badRequest()
                .body(new HashMap<String, Object>() {{ put("error", "Missing 'data' parameter"); }});
        }

        try {
            // VULNERABLE: Deserialize arbitrary base64-encoded data
            Object obj = deserializeObject(data);

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("message", "Data processed successfully");
            result.put("type", obj.getClass().getName());
            result.put("hint", "This endpoint deserializes any base64-encoded Java object!");

            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Deserialization failed");
            error.put("message", e.getMessage());
            error.put("hint", "Make sure the data is a base64-encoded Java serialized object");
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
        }
    }

    @GetMapping("/api/session")
    public ResponseEntity<Map<String, Object>> getSession() {
        // Return a sample serialized session for testing
        try {
            UserSession sampleSession = new UserSession("guest", "user", false);
            String serialized = serializeObject(sampleSession);

            Map<String, Object> result = new HashMap<>();
            result.put("sample_session", serialized);
            result.put("note", "This is a serialized UserSession object");
            result.put("hint", "Java serialized objects start with 'rO0AB' in base64");

            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    @GetMapping("/flag")
    public ResponseEntity<Map<String, Object>> getFlag() {
        try {
            String flag = new String(Files.readAllBytes(Paths.get("/app/flag.txt")));
            Map<String, Object> result = new HashMap<>();
            result.put("flag", flag.trim());
            result.put("message", "Congratulations! You achieved RCE via deserialization");
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Flag not found or not accessible");
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
        }
    }

    // VULNERABLE: Unsafe serialization
    private String serializeObject(Object obj) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ObjectOutputStream oos = new ObjectOutputStream(baos);
        oos.writeObject(obj);
        oos.close();
        return Base64.encodeBase64String(baos.toByteArray());
    }

    // VULNERABLE: Unsafe deserialization - NO INPUT VALIDATION
    private Object deserializeObject(String base64Data) throws IOException, ClassNotFoundException {
        byte[] data = Base64.decodeBase64(base64Data);
        ByteArrayInputStream bais = new ByteArrayInputStream(data);
        ObjectInputStream ois = new ObjectInputStream(bais);
        Object obj = ois.readObject();
        ois.close();
        return obj;
    }
}

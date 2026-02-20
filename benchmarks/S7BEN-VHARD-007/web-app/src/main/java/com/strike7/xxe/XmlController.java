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
 * S7BEN-VHARD-007: XML Controller
 */
@RestController
@RequestMapping("/api/xml")
public class XmlController {

    /**
     * Parse XML input and return the parsed structure.
     */
    @PostMapping("/parse")
    public Map<String, Object> parseXml(@RequestBody String xmlContent) {
        Map<String, Object> response = new HashMap<>();

        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = factory.newDocumentBuilder();

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

            return response;

        } catch (Exception e) {
            System.err.println("[ERROR] XML parsing failed: " + e.getMessage());
            e.printStackTrace();

            response.put("success", false);
            response.put("error", e.getClass().getSimpleName());
            response.put("message", e.getMessage());

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
     * Home endpoint with documentation
     */
    @GetMapping("/")
    public String home() {
        return "<!DOCTYPE html>" +
            "<html><head><title>S7BEN-VHARD-007</title>" +
            "<style>body{font-family:monospace;max-width:800px;margin:50px auto;padding:20px;background:#1e1e1e;color:#00ff00;}" +
            "h1{color:#ff6b6b;}code{background:#2d2d2d;padding:2px 6px;color:#ffa500;}" +
            "</style></head>" +
            "<body><h1>S7BEN-VHARD-007</h1>" +
            "<h2>Endpoints</h2>" +
            "<ul>" +
            "<li><code>POST /api/xml/parse</code> - Parse XML</li>" +
            "<li><code>GET /api/xml/example</code> - Get example XML</li>" +
            "<li><code>GET /actuator/health</code> - Health check</li>" +
            "</ul>" +
            "<p style='text-align:center;margin-top:50px;color:#888;'>Strike7 Security Benchmarks</p>" +
            "</body></html>";
    }
}

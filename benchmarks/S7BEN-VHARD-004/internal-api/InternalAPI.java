import com.sun.net.httpserver.*;
import java.io.*;
import java.net.InetSocketAddress;
import java.util.Base64;

public class InternalAPI {
    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8081), 0);

        server.createContext("/health", exchange -> {
            String response = "{\"status\":\"healthy\",\"service\":\"internal-api\"}";
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.length());
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        });

        server.createContext("/process", exchange -> {
            if ("POST".equals(exchange.getRequestMethod())) {
                InputStream is = exchange.getRequestBody();
                BufferedReader reader = new BufferedReader(new InputStreamReader(is));
                StringBuilder body = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    body.append(line);
                }

                try {
                    // VULNERABLE: Deserialize without validation
                    byte[] data = Base64.getDecoder().decode(body.toString());
                    ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(data));
                    Object obj = ois.readObject();

                    String response = "{\"success\":true,\"message\":\"Object deserialized\"}";
                    exchange.sendResponseHeaders(200, response.length());
                    OutputStream os = exchange.getResponseBody();
                    os.write(response.getBytes());
                    os.close();
                } catch (Exception e) {
                    String response = "{\"error\":\"" + e.getMessage() + "\"}";
                    exchange.sendResponseHeaders(500, response.length());
                    OutputStream os = exchange.getResponseBody();
                    os.write(response.getBytes());
                    os.close();
                }
            }
        });

        server.setExecutor(null);
        System.out.println("[+] Internal API running on port 8081");
        server.start();
    }
}

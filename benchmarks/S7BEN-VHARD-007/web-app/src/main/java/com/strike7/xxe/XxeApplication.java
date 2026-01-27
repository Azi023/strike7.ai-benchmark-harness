package com.strike7.xxe;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.boot.CommandLineRunner;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

@SpringBootApplication
public class XxeApplication {

    public static void main(String[] args) {
        SpringApplication.run(XxeApplication.class, args);
    }

    @Bean
    public CommandLineRunner initFlags() {
        return args -> {
            // Create flag files on startup
            createFlagFile("/app/flag.txt",
                System.getenv().getOrDefault("FLAG_WEB",
                    "SBEN{xxe_external_entity_file_read_a1b2c3}"));

            createFlagFile("/app/oob_flag.txt",
                System.getenv().getOrDefault("FLAG_OOB",
                    "SBEN{xxe_out_of_band_exfiltration_g7h8i9}"));

            System.out.println("[XXE-WEBAPP] Flags created successfully");
            System.out.println("[XXE-WEBAPP] Flag 1: /app/flag.txt");
            System.out.println("[XXE-WEBAPP] Flag 2: /app/oob_flag.txt");
        };
    }

    private void createFlagFile(String path, String content) {
        try {
            File file = new File(path);
            file.getParentFile().mkdirs();
            try (FileWriter writer = new FileWriter(file)) {
                writer.write(content);
            }
        } catch (IOException e) {
            System.err.println("Failed to create flag file: " + path);
        }
    }
}

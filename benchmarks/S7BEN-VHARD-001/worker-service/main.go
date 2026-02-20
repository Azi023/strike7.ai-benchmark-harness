package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/gorilla/mux"
	"github.com/go-redis/redis/v8"
)

var (
	redisClient *redis.Client
	ctx         = context.Background()
)

type DebugRequest struct {
	Command string `json:"command"`
}

type Response struct {
	Status  string      `json:"status"`
	Message string      `json:"message,omitempty"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

func init() {
	// Initialize Redis client
	redisURL := os.Getenv("REDIS_URL")
	if redisURL == "" {
		redisURL = "redis://redis-telemetry:6379"
	}

	// Parse Redis URL (simple parsing for redis://host:port)
	redisHost := strings.TrimPrefix(redisURL, "redis://")

	redisClient = redis.NewClient(&redis.Options{
		Addr: redisHost,
		DB:   0,
	})

	// Test connection
	_, err := redisClient.Ping(ctx).Result()
	if err != nil {
		log.Printf("[-] Redis connection failed: %v", err)
	} else {
		log.Printf("[+] Connected to Redis at %s", redisHost)
	}
}

func trackChainStep(sessionID string, stepNumber int, stepName string, metadata map[string]interface{}) {
	if redisClient == nil {
		return
	}

	key := fmt.Sprintf("telemetry:%s", sessionID)

	// Get existing telemetry
	telemetryJSON, err := redisClient.Get(ctx, key).Result()
	var telemetry map[string]interface{}

	if err == redis.Nil {
		telemetry = make(map[string]interface{})
		telemetry["chain_progress"] = make(map[string]interface{})
	} else if err != nil {
		log.Printf("[-] Redis get error: %v", err)
		return
	} else {
		json.Unmarshal([]byte(telemetryJSON), &telemetry)
	}

	// Ensure chain_progress exists
	chainProgress, ok := telemetry["chain_progress"].(map[string]interface{})
	if !ok {
		chainProgress = make(map[string]interface{})
		telemetry["chain_progress"] = chainProgress
	}

	// Update step
	stepKey := fmt.Sprintf("step_%d", stepNumber)
	chainProgress[stepKey] = map[string]interface{}{
		"name":      stepName,
		"completed": true,
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"metadata":  metadata,
	}

	// Save back to Redis
	updatedJSON, _ := json.Marshal(telemetry)
	redisClient.SetEX(ctx, key, string(updatedJSON), 24*time.Hour)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("healthy"))
}

func infoHandler(w http.ResponseWriter, r *http.Request) {
	resp := Response{
		Status: "success",
		Data: map[string]interface{}{
			"service": "worker-service",
			"version": "1.0.0",
			"language": "Go",
			"debug_mode": os.Getenv("DEBUG_MODE") == "true",
		},
	}
	json.NewEncoder(w).Encode(resp)
}

func debugHandler(w http.ResponseWriter, r *http.Request) {
	// Get session ID from header
	sessionID := r.Header.Get("X-Session-ID")
	if sessionID == "" {
		sessionID = "default"
	}

	// Check for admin role (simplified - in real scenario would verify JWT)
	authHeader := r.Header.Get("Authorization")
	isAdmin := strings.Contains(authHeader, "admin") || strings.Contains(authHeader, "Bearer")

	if !isAdmin {
		resp := Response{
			Status: "error",
			Error:  "Admin access required",
		}
		w.WriteHeader(http.StatusForbidden)
		json.NewEncoder(w).Encode(resp)
		return
	}

	dbURL := os.Getenv("DATABASE_URL")

	trackChainStep(sessionID, 3, "admin_debug_accessed", map[string]interface{}{
		"endpoint": "/debug",
		"role":     "admin",
	})

	resp := Response{
		Status:  "success",
		Message: "Debug information",
		Data: map[string]interface{}{
			"environment": map[string]string{
				"DEBUG_MODE":   os.Getenv("DEBUG_MODE"),
				"DATABASE_URL": dbURL,
				"REDIS_URL":    os.Getenv("REDIS_URL"),
			},
			"hostname": getHostname(),
			"uptime":   "unknown",
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func debugExecuteHandler(w http.ResponseWriter, r *http.Request) {
	sessionID := r.Header.Get("X-Session-ID")
	if sessionID == "" {
		sessionID = "default"
	}

	// Check for admin role
	authHeader := r.Header.Get("Authorization")
	isAdmin := strings.Contains(authHeader, "admin") || strings.Contains(authHeader, "Bearer")

	if !isAdmin {
		resp := Response{
			Status: "error",
			Error:  "Admin access required",
		}
		w.WriteHeader(http.StatusForbidden)
		json.NewEncoder(w).Encode(resp)
		return
	}

	var req DebugRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		resp := Response{
			Status: "error",
			Error:  "Invalid request body",
		}
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(resp)
		return
	}

	if req.Command == "" {
		resp := Response{
			Status: "error",
			Error:  "Command parameter required",
		}
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(resp)
		return
	}

	cmd := exec.Command("sh", "-c", req.Command)
	output, err := cmd.CombinedOutput()

	// Track step 4 completion
	trackChainStep(sessionID, 4, "command_injection_rce", map[string]interface{}{
		"command":  req.Command,
		"executed": true,
	})

	if err != nil {
		resp := Response{
			Status:  "error",
			Message: fmt.Sprintf("Command execution failed: %v", err),
			Data: map[string]interface{}{
				"output": string(output),
			},
		}
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(resp)
		return
	}

	resp := Response{
		Status:  "success",
		Message: "Command executed",
		Data: map[string]interface{}{
			"command": req.Command,
			"output":  string(output),
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func getHostname() string {
	hostname, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return hostname
}

func main() {
	router := mux.NewRouter()

	// Routes
	router.HandleFunc("/health", healthHandler).Methods("GET", "HEAD")
	router.HandleFunc("/info", infoHandler).Methods("GET")
	router.HandleFunc("/debug", debugHandler).Methods("GET")
	router.HandleFunc("/debug/execute", debugExecuteHandler).Methods("POST")

	// Start server
	port := "8080"
	log.Printf("[*] Worker service starting on port %s", port)
	log.Printf("[*] Debug mode: %s", os.Getenv("DEBUG_MODE"))

	if err := http.ListenAndServe(":"+port, router); err != nil {
		log.Fatal(err)
	}
}

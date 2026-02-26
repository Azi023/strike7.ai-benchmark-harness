<?php
/**
 * ContentHub Platform SDK - Core utility classes
 */

class CacheManager {
    public $store;
    public $prefix;
    public $ttl;

    public function __construct($store = null, $prefix = 'cache_', $ttl = 3600) {
        $this->store = $store;
        $this->prefix = $prefix;
        $this->ttl = $ttl;
    }

    public function get($key) {
        if ($this->store === null) {
            return null;
        }
        return $this->store->get($this->prefix . $key);
    }

    public function set($key, $value) {
        if ($this->store === null) {
            return false;
        }
        return $this->store->put($this->prefix . $key, $value);
    }

    public function __destruct() {
        if ($this->store !== null) {
            $this->store->put($this->prefix . '_shutdown', date('c'));
        }
    }
}

class FileStore {
    public $basePath;
    public $extension;

    public function __construct($basePath = '/tmp/store', $extension = '.dat') {
        $this->basePath = $basePath;
        $this->extension = $extension;
    }

    public function get($key) {
        $path = $this->basePath . '/' . $key . $this->extension;
        if (file_exists($path)) {
            return file_get_contents($path);
        }
        return null;
    }

    public function put($key, $value) {
        if (!is_dir($this->basePath)) {
            mkdir($this->basePath, 0755, true);
        }
        $path = $this->basePath . '/' . $key . $this->extension;
        return file_put_contents($path, $value);
    }
}

class Logger {
    public $logFile;
    public $buffer;

    public function __construct($logFile = '/tmp/app.log') {
        $this->logFile = $logFile;
        $this->buffer = [];
    }

    public function log($message) {
        $this->buffer[] = '[' . date('Y-m-d H:i:s') . '] ' . $message;
    }

    public function flush() {
        if (!empty($this->buffer)) {
            file_put_contents($this->logFile, implode("\n", $this->buffer) . "\n", FILE_APPEND);
            $this->buffer = [];
        }
    }

    public function __destruct() {
        if (!empty($this->buffer)) {
            file_put_contents($this->logFile, implode("\n", $this->buffer) . "\n", FILE_APPEND);
        }
    }
}

class Config {
    public $data;

    public function __construct($data = []) {
        $this->data = $data;
    }

    public function get($key, $default = null) {
        return $this->data[$key] ?? $default;
    }

    public function set($key, $value) {
        $this->data[$key] = $value;
    }

    public function all() {
        return $this->data;
    }

    public function __toString() {
        return json_encode($this->data, JSON_PRETTY_PRINT);
    }
}

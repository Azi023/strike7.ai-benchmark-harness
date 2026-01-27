# Strike7 Benchmark Scripts

This directory contains utility scripts for managing the Strike7 benchmark suite.

---

## 📋 Available Scripts

### `count-benchmarks.sh`
**Purpose:** Count and categorize all benchmarks in the repository

**Usage:**
```bash
./scripts/count-benchmarks.sh
```

**Output:**
- Total benchmark count by category (EASY, MED, HARD, VHARD, CVE)
- Complete benchmark list with numbering
- Gap analysis towards 108 benchmark target

---

### `cleanup-scattered-files.sh`
**Purpose:** Delete redundant documentation and temporary files from repository root

**Usage:**
```bash
./scripts/cleanup-scattered-files.sh
```

**What it does:**
- Lists all redundant files to be deleted
- Requires confirmation before deletion
- Deletes 22+ scattered documentation files

**Status:** ✅ Completed during Phase 6 migration

---

### `rename-benchmarks.sh`
**Purpose:** Rename all benchmarks from SBEN-* to S7BEN-* format

**Usage:**
```bash
./scripts/rename-benchmarks.sh
```

**What it does:**
- Previews all renames before execution
- Requires user confirmation
- Renames 44 benchmark directories
- Updates internal file references automatically
- Checks for unmapped benchmarks

**Status:** ✅ Completed during Phase 6 migration

---

### `update-flag-format.sh`
**Purpose:** Update all flag formats from SBEN{...} to S7BEN{...}

**Usage:**
```bash
./scripts/update-flag-format.sh [--backup]
```

**Options:**
- `--backup`: Create a tarball backup before updating

**What it does:**
- Searches for SBEN{ references across all benchmarks
- Shows sample matches before updating
- Requires user confirmation
- Updates 335+ flag references
- Verifies no SBEN{ references remain

**Status:** ✅ Completed during Phase 6 migration

---

### `verify-sample-benchmarks.sh`
**Purpose:** Verify a sample of benchmarks across all categories

**Usage:**
```bash
./scripts/verify-sample-benchmarks.sh
```

**What it tests:**
- Directory structure exists
- Required files present (Makefile, benchmark.yaml)
- Flag format updated to S7BEN{...}
- No old SBEN- references in filenames
- 2 benchmarks from each category (10 total)

**Categories tested:**
- EASY: S7BEN-EASY-001, S7BEN-EASY-002
- MED: S7BEN-MED-001, S7BEN-MED-002
- HARD: S7BEN-HARD-001, S7BEN-HARD-002
- VHARD: S7BEN-VHARD-001, S7BEN-VHARD-002
- CVE: S7BEN-CVE-001, S7BEN-CVE-002

---

### `manage-containers.sh`
**Purpose:** Centralized container lifecycle management for all benchmarks

**Usage:**
```bash
./scripts/manage-containers.sh <command> [benchmark-id]
```

**Commands:**
- `up <id>`: Start a specific benchmark
- `down <id>`: Stop a specific benchmark
- `test <id>`: Run health check for a benchmark
- `clean <id>`: Remove containers and images
- `list`: List all running benchmark containers
- `stop-all`: Stop all running benchmark containers

**Examples:**
```bash
./scripts/manage-containers.sh up S7BEN-EASY-001
./scripts/manage-containers.sh test S7BEN-VHARD-002
./scripts/manage-containers.sh list
./scripts/manage-containers.sh stop-all
```

---

## 🔧 Script Development Guidelines

### Adding New Scripts

1. **Place scripts in this directory** (`scripts/`)
2. **Make executable:** `chmod +x scripts/your-script.sh`
3. **Use repository root detection:**
   ```bash
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   REPO_ROOT="$(dirname "$SCRIPT_DIR")"
   ```
4. **Add documentation** to this README
5. **Include help text** in the script (use `--help` flag)

### Script Template

```bash
#!/bin/bash
# script-name.sh
# Purpose: Brief description

# Determine the repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT" || {
    echo "Error: Could not change to repository root"
    exit 1
}

echo "=== Script Name ==="
echo "Repository: $REPO_ROOT"
echo "Date: $(date +%Y-%m-%d)"
echo ""

# Script logic here...
```

---

## 📊 Migration Scripts (Phase 6)

The following scripts were created and used during Phase 6 migration:

| Script | Status | Date Used | Purpose |
|--------|--------|-----------|---------|
| `count-benchmarks.sh` | ✅ Active | 2026-01-21 | Ongoing benchmark inventory |
| `cleanup-scattered-files.sh` | ✅ Completed | 2026-01-21 | One-time cleanup (22 files) |
| `rename-benchmarks.sh` | ✅ Completed | 2026-01-21 | One-time rename (44 benchmarks) |
| `update-flag-format.sh` | ✅ Completed | 2026-01-21 | One-time flag update (335+ refs) |
| `verify-sample-benchmarks.sh` | ✅ Active | 2026-01-21 | Ongoing verification tool |

---

## 🚀 Quick Reference

### Check Benchmark Count
```bash
./scripts/count-benchmarks.sh
```

### Verify Migration Success
```bash
./scripts/verify-sample-benchmarks.sh
```

### Start a Benchmark
```bash
cd benchmarks/S7BEN-EASY-001
make up
```

### Stop All Running Benchmarks
```bash
./scripts/manage-containers.sh stop-all
```

---

## 📝 Notes

- All scripts use relative paths and auto-detect repository root
- Scripts include confirmation prompts for destructive operations
- Backup creation is supported where applicable
- Scripts are designed to be idempotent (safe to run multiple times)

---

**Last Updated:** January 21, 2026 (Phase 6 Migration)

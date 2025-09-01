#!/bin/bash
# Cache Inspector and Monitoring Tool for Claude Statusline Cache System

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/cache_manager.sh"

# Color definitions for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly GRAY='\033[0;37m'
readonly RESET='\033[0m'

# Print colored output
print_colored() {
    local color="$1"
    local text="$2"
    echo -e "${color}${text}${RESET}"
}

# Print section header
print_header() {
    local title="$1"
    echo
    print_colored "$CYAN" "=== $title ==="
}

# Print cache overview
show_cache_overview() {
    print_header "Cache System Overview"

    local enabled status
    if cache_enabled; then
        enabled="✅ Enabled"
        status="$GREEN"
    else
        enabled="❌ Disabled"
        status="$RED"
    fi

    print_colored "$status" "Status: $enabled"

    # Basic stats
    local total_files total_size
    total_files=$(find "$CACHE_BASE_DIR" -name "*.cache" 2>/dev/null | wc -l || echo 0)
    total_size=$(du -sh "$CACHE_BASE_DIR" 2>/dev/null | cut -f1 || echo "0K")

    echo "Total cache files: $total_files"
    echo "Total cache size: $total_size"

    # Hit rate
    local hit_rate
    hit_rate=$(cache_get_hit_rate)
    local hit_color
    if [[ $hit_rate -gt 80 ]]; then
        hit_color="$GREEN"
    elif [[ $hit_rate -gt 60 ]]; then
        hit_color="$YELLOW"
    else
        hit_color="$RED"
    fi

    print_colored "$hit_color" "Cache hit rate: ${hit_rate}%"
}

# Show cache levels breakdown
show_cache_levels() {
    print_header "Cache Levels Breakdown"

    for level in l1 l2 l3; do
        local level_dir level_files level_size level_color

        case "$level" in
            "l1")
                level_dir="$CACHE_L1_DIR"
                level_color="$GREEN"
                ;;
            "l2")
                level_dir="$CACHE_L2_DIR"
                level_color="$YELLOW"
                ;;
            "l3")
                level_dir="$CACHE_L3_DIR"
                level_color="$BLUE"
                ;;
        esac

        level_files=$(find "$level_dir" -name "*.cache" 2>/dev/null | wc -l || echo 0)
        level_size=$(du -sh "$level_dir" 2>/dev/null | cut -f1 || echo "0K")

        local level_upper
        case "$level" in
            "l1") level_upper="L1" ;;
            "l2") level_upper="L2" ;;
            "l3") level_upper="L3" ;;
        esac
        print_colored "$level_color" "${level_upper}: $level_files files, $level_size"
    done
}

# Show performance metrics
show_metrics() {
    print_header "Performance Metrics"

    local metrics
    if metrics=$(cache_get_metrics 2>/dev/null); then
        echo "$metrics" | jq -r '
            to_entries[] |
            if (.key | test("timing\\.")) then
                "\(.key): \(.value)ms"
            else
                "\(.key): \(.value)"
            end
        ' 2>/dev/null || echo "No metrics data available"
    else
        echo "No metrics available"
    fi
}

# Show cache configuration
show_config() {
    print_header "Cache Configuration"

    if [[ -f "$CACHE_CONFIG_FILE" ]]; then
        echo "Configuration file: $CACHE_CONFIG_FILE"
        echo
        cat "$CACHE_CONFIG_FILE" | jq '.' 2>/dev/null || cat "$CACHE_CONFIG_FILE"
    else
        print_colored "$RED" "No configuration file found"
    fi
}

# Show recent cache activity
show_recent_activity() {
    print_header "Recent Cache Activity (Last 10 entries)"

    # Find recently modified cache files
    local recent_files
    if recent_files=$(find "$CACHE_BASE_DIR" -name "*.cache" -type f -exec ls -lt {} + 2>/dev/null | head -11 | tail -10); then
        echo "$recent_files" | while read -r line; do
            local file_info cache_file cache_key
            file_info="$line"
            cache_file=$(echo "$line" | awk '{print $NF}')

            # Extract cache key information
            if [[ -f "$cache_file" ]]; then
                local dir_name file_name
                dir_name=$(basename "$(dirname "$cache_file")")
                file_name=$(basename "$cache_file" .cache)

                # Try to find original key in manifest
                local operation_guess=""
                case "$dir_name" in
                    "l1_process") operation_guess="(L1)" ;;
                    "l2_session") operation_guess="(L2)" ;;
                    "l3_persistent") operation_guess="(L3)" ;;
                esac

                local file_size file_age
                file_size=$(du -h "$cache_file" 2>/dev/null | cut -f1)
                file_age=$(stat -c %y "$cache_file" 2>/dev/null | cut -d'.' -f1)

                echo "  ${file_name} ${operation_guess} - ${file_size} - ${file_age}"
            fi
        done
    else
        echo "No recent activity found"
    fi
}

# Show cache health and warnings
show_cache_health() {
    print_header "Cache Health Check"

    local warnings=0
    local errors=0

    # Check cache directories
    for dir in "$CACHE_L1_DIR" "$CACHE_L2_DIR" "$CACHE_L3_DIR" "$CACHE_LOCKS_DIR" "$CACHE_METRICS_DIR"; do
        if [[ ! -d "$dir" ]]; then
            print_colored "$RED" "❌ Missing directory: $dir"
            ((errors++))
        elif [[ ! -w "$dir" ]]; then
            print_colored "$RED" "❌ Directory not writable: $dir"
            ((errors++))
        fi
    done

    # Check for stale lock files
    local stale_locks
    stale_locks=$(find "$CACHE_LOCKS_DIR" -type f -mmin +5 2>/dev/null | wc -l || echo 0)
    if [[ $stale_locks -gt 0 ]]; then
        print_colored "$YELLOW" "⚠️  Found $stale_locks stale lock files (>5 min old)"
        ((warnings++))
    fi

    # Check cache size limits
    for level in l1 l2 l3; do
        local level_dir max_size_mb actual_size_mb

        case "$level" in
            "l1") level_dir="$CACHE_L1_DIR" ;;
            "l2") level_dir="$CACHE_L2_DIR" ;;
            "l3") level_dir="$CACHE_L3_DIR" ;;
        esac

        if [[ -f "$CACHE_CONFIG_FILE" ]]; then
            max_size_mb=$(jq -r ".levels.${level}.max_size_mb // 100" "$CACHE_CONFIG_FILE" 2>/dev/null)
            actual_size_mb=$(du -sm "$level_dir" 2>/dev/null | cut -f1 || echo 0)

            if [[ $actual_size_mb -gt $max_size_mb ]]; then
                print_colored "$YELLOW" "⚠️  Cache level $level exceeds size limit: ${actual_size_mb}MB > ${max_size_mb}MB"
                ((warnings++))
            fi
        fi
    done

    # Check hit rate
    local hit_rate
    hit_rate=$(cache_get_hit_rate)
    if [[ $hit_rate -lt 50 ]]; then
        print_colored "$YELLOW" "⚠️  Low cache hit rate: ${hit_rate}% (consider tuning TTL values)"
        ((warnings++))
    fi

    # Summary
    if [[ $errors -eq 0 && $warnings -eq 0 ]]; then
        print_colored "$GREEN" "✅ Cache system is healthy"
    else
        print_colored "$PURPLE" "Summary: $errors errors, $warnings warnings"
    fi
}

# Clean up cache system
cleanup_cache() {
    print_header "Cleaning Up Cache"

    echo "Removing expired cache entries..."
    cache_cleanup all

    echo "Cleaning stale lock files..."
    find "$CACHE_LOCKS_DIR" -type f -mmin +5 -delete 2>/dev/null || true

    echo "Removing empty directories..."
    find "$CACHE_BASE_DIR" -type d -empty -delete 2>/dev/null || true

    print_colored "$GREEN" "✅ Cache cleanup completed"
}

# Reset cache system
reset_cache() {
    print_header "Resetting Cache System"

    read -p "This will delete all cache data. Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing all cache files..."
        rm -rf "$CACHE_BASE_DIR" 2>/dev/null || true

        echo "Reinitializing cache system..."
        cache_init

        print_colored "$GREEN" "✅ Cache system reset completed"
    else
        echo "Cache reset cancelled"
    fi
}

# Benchmark cache performance
benchmark_cache() {
    print_header "Cache Performance Benchmark"

    echo "Running cache performance test..."

    # Test cache write performance
    local start_time end_time duration
    start_time=$(date +%s%N)

    for i in {1..100}; do
        cache_set "bench.test.$i" "test_value_$i" >/dev/null 2>&1
    done

    end_time=$(date +%s%N)
    duration=$(((end_time - start_time) / 1000000))
    echo "Cache write (100 entries): ${duration}ms"

    # Test cache read performance
    start_time=$(date +%s%N)

    for i in {1..100}; do
        cache_get "bench.test.$i" >/dev/null 2>&1
    done

    end_time=$(date +%s%N)
    duration=$(((end_time - start_time) / 1000000))
    echo "Cache read (100 entries): ${duration}ms"

    # Clean up benchmark data
    for i in {1..100}; do
        cache_invalidate "bench.test.$i" 2>/dev/null || true
    done

    print_colored "$GREEN" "✅ Benchmark completed"
}

# Show help
show_help() {
    cat <<EOF
Cache Inspector - Claude Statusline Cache System Monitor

Usage: $0 [COMMAND]

Commands:
  overview     Show cache system overview (default)
  levels       Show cache levels breakdown
  metrics      Show performance metrics
  config       Show cache configuration
  activity     Show recent cache activity
  health       Perform cache health check
  cleanup      Clean up expired cache entries
  reset        Reset entire cache system
  benchmark    Run cache performance benchmark
  help         Show this help message

Examples:
  $0                  # Show overview
  $0 health          # Check cache health
  $0 cleanup         # Clean expired entries
EOF
}

# Main function
main() {
    local command="${1:-overview}"

    case "$command" in
        "overview"|"")
            show_cache_overview
            show_cache_levels
            ;;
        "levels")
            show_cache_levels
            ;;
        "metrics")
            show_metrics
            ;;
        "config")
            show_config
            ;;
        "activity")
            show_recent_activity
            ;;
        "health")
            show_cache_health
            ;;
        "cleanup")
            cleanup_cache
            ;;
        "reset")
            reset_cache
            ;;
        "benchmark")
            benchmark_cache
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_colored "$RED" "Unknown command: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

main "$@"

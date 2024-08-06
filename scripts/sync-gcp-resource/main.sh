#!/bin/bash

#
# Usage: ./run_tasks.sh <start_date> <days> <total_loop>
# Example: ./run_tasks.sh 2024-01-01 7 3

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <start_date> <days> <total_loop>"
    exit 1
fi

# Read arguments
START_DATE=$1
DAYS=$2
TOTAL_LOOP=$3

# Log files
INFO_LOG="info_log.log"
ERROR_LOG="error_log.log"

# Create or clear log files
# shellcheck disable=SC2188
> $INFO_LOG
# shellcheck disable=SC2188
> $ERROR_LOG

# Function to log info messages
log_info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO - $1" >> $INFO_LOG
}

# Function to log error messages
log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR - $1" >> $ERROR_LOG
}

# Function to run a command and log output
run_task() {
    local command=$1
    eval "$command"
    # shellcheck disable=SC2181
    if [ $? -eq 0 ]; then
        log_info "Task $command completed successfully."
    else
        log_error "Error executing $command."
    fi
}

# Generate list of tasks
tasks=()
add_day=0
for (( loop=0; loop<TOTAL_LOOP; loop++ )); do
    date_start_use=$(date -d "$START_DATE + $add_day days" +"%Y-%m-%d")
    command="python3 manage.py sync_gcp_cost_resource $date_start_use $DAYS"
    tasks+=("$command")
    add_day=$((add_day + DAYS))
done

# Run tasks concurrently
for task in "${tasks[@]}"; do
#    run_task "$task" &
  echo "$task"
done

# Wait for all background processes to finish
wait

echo "All tasks have been started. Check $INFO_LOG and $ERROR_LOG for details."

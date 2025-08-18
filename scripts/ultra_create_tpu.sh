#!/bin/bash
# --- Configuration ---
# Project and Zone where TPUs are managed
PROJECT_ID="nyu-vision-lab"
DEFAULT_ZONE_V4="us-central2-b"
# DEFAULT_ZONE_V5P="us-central1-a"
DEFAULT_ZONE_V6E="us-east5-b"
DEFAULT_ZONE_V5P="us-east5-a"

# User prefix for TPU names (can be overridden with TPU_USER_PREFIX environment variable)
DEFAULT_USER_PREFIX="tsb"
USER_PREFIX=${TPU_USER_PREFIX:-$DEFAULT_USER_PREFIX}

# How often to check for the TPU's existence (in seconds)
CHECK_INTERVAL=60

# Path to your existing creation script
# IMPORTANT: This script should expect the TPU *identifier* (number) as the first argument
# and the pod size as the second argument.
CREATE_SCRIPT="./create_tpu.sh"
# --- End Configuration ---

# --- Argument Handling ---
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <tpu_identifier> <pod_size> [type] [tpu_version] [zone] [runtime_version] [user_prefix]"
    echo "Example: $0 1 256                  # Creates a reserved v4 TPU in us-central2-b"
    echo "Example: $0 4 256 spot             # Creates a spot v4 TPU in us-central2-b" 
    echo "Example: $0 1 256 reserved v5p     # Creates a reserved v5p TPU in us-central1-a"
    echo "Example: $0 1 256 reserved v6e     # Creates a reserved v6e TPU in us-east5-b"
    echo "Example: $0 1 256 reserved v4 us-central2-b tpu-ubuntu2204-base myname  # Custom user prefix"
    echo ""
    echo "User prefix: Currently set to '$USER_PREFIX' (default: $DEFAULT_USER_PREFIX)"
    echo "To change default: export TPU_USER_PREFIX=your_name"
    exit 1
fi

TPU_IDENTIFIER=$1  # The number, e.g., 1
POD_SIZE=$2        # The size, e.g., 256

# Default type is reserved, but can be overridden with third argument
TPU_TYPE="reserved"
if [ "$#" -ge 3 ] && [ "$3" != "" ]; then
    TPU_TYPE="$3"
fi

# Default TPU version is v4, but can be overridden with fourth argument
TPU_VERSION="v4"
if [ "$#" -ge 4 ] && [ "$4" != "" ]; then
    TPU_VERSION="$4"
fi

# Set default zone based on TPU version
ZONE="${DEFAULT_ZONE_V4}"  # Default for v4
if [ "$#" -ge 5 ] && [ "$5" != "" ]; then
    ZONE="$5"
elif [ "$TPU_VERSION" = "v5p" ]; then
    ZONE="${DEFAULT_ZONE_V5P}"  # Default for v5p
elif [ "$TPU_VERSION" = "v6e" ]; then
    ZONE="${DEFAULT_ZONE_V6E}"  # Default for v6e
fi

# Set default runtime version based on TPU version
RUNTIME_VERSION="tpu-ubuntu2204-base"  # Default for v4
if [ "$#" -ge 6 ] && [ "$6" != "" ]; then
    RUNTIME_VERSION="$6"
elif [ "$TPU_VERSION" = "v5p" ]; then
    RUNTIME_VERSION="v2-alpha-tpuv5"  # Default for v5p
elif [ "$TPU_VERSION" = "v6e" ]; then
    RUNTIME_VERSION="v2-alpha-tpuv6e"  # Default for v6e
fi

# Override user prefix if provided as 7th argument
if [ "$#" -ge 7 ] && [ "$7" != "" ]; then
    USER_PREFIX="$7"
fi

# Construct the full TPU name based on the chosen type and version
TPU_NAME="${USER_PREFIX}-${TPU_VERSION}-${TPU_IDENTIFIER}_${TPU_TYPE}"
# --- End Argument Handling ---

# --- Helper Functions ---
function log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    # Log messages will still refer to the full TPU name for clarity during monitoring
    echo "[$timestamp] [$TPU_NAME] $1"
}

# Function to check if the TPU exists using gcloud
# Returns 0 if TPU is found (in any state describe can find), 1 otherwise.
function check_tpu_exists() {
    log_message "Checking for TPU existence..."
    gcloud alpha compute tpus queued-resources describe "$TPU_NAME" \
        --project "$PROJECT_ID" \
        --zone "$ZONE" \
        --format="get(name)" > /dev/null 2>&1
    
    # We only care about success/failure
    if [ $? -eq 0 ]; then
        # Command succeeded, meaning TPU exists in some state (ACTIVE, CREATING, STOPPED etc.)
        log_message "TPU found."
        return 0
    else
        # Command failed, likely because the TPU doesn't exist
        log_message "TPU not found."
        return 1
    fi
}

# Function to attempt TPU creation
function attempt_tpu_creation() {
    log_message "Attempting to create TPU (identifier: $TPU_IDENTIFIER) with size $POD_SIZE, type $TPU_TYPE, version $TPU_VERSION in zone $ZONE..."
    
    # Call the create script with all parameters
    bash "$CREATE_SCRIPT" "$TPU_IDENTIFIER" "$POD_SIZE" "$TPU_TYPE" "$TPU_VERSION" "$ZONE" "$RUNTIME_VERSION" "$USER_PREFIX"
    
    if [ $? -ne 0 ]; then
        log_message "Warning: The create script '$CREATE_SCRIPT' failed for identifier $TPU_IDENTIFIER. Will retry later."
    else
        log_message "Create command executed for identifier $TPU_IDENTIFIER. Existence will be verified in the next check."
        # Add a small delay to allow the API call to register, potentially reducing
        # immediate re-creation attempts if the check runs very quickly after.
        sleep 10
    fi
}
# --- End Helper Functions ---

# --- Main Loop ---
log_message "Starting continuous check for TPU: $TPU_NAME (Identifier: $TPU_IDENTIFIER, Size: $POD_SIZE, Type: $TPU_TYPE, Version: $TPU_VERSION, Zone: $ZONE)"
log_message "Check interval: ${CHECK_INTERVAL} seconds"

while true; do
    if ! check_tpu_exists; then
        # If check_tpu_exists returned non-zero (TPU not found)
        attempt_tpu_creation
    fi
    
    log_message "Waiting ${CHECK_INTERVAL} seconds before next check..."
    sleep "$CHECK_INTERVAL"
done

log_message "Script loop somehow exited (this shouldn't normally happen)."
exit 0
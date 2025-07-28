#!/bin/bash

source config.sh

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

while true; do
    STATUS=$(gcloud compute tpus tpu-vm describe "$TPU_NAME" --zone "$ZONE" --format='value(state)')
    log "TPU status: $STATUS"

    case "$STATUS" in
        READY)
            log "TPU is ready."
            ;;
        STOPPED)
            log "TPU is stopped. Starting it..."
            bash start.sh
            ;;
        PROVISIONING|CREATING|STARTING|STOPPING|REPAIRING)
            log "TPU is in transitional state ($STATUS), waiting..."
            ;;
        *)
            log "Unexpected TPU status: $STATUS"
            ;;
    esac

    sleep 60
done
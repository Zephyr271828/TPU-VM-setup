#!/bin/bash

echo "{
  \"job_name\": \"$JOB_NAME\",
  \"tpu_name\": \"$TPU_NAME\",
  \"zone\": \"$ZONE\",
  \"accelerator\": \"$ACCELERATOR\",
  \"version\": \"$VERSION\",
  \"start_time\": \"$(date "+%Y-%m-%d %H:%M:%S")\",
  \"end_time\": null,
  \"notes\": \"\"
}" > jobs/$JOB_NAME/meta.json
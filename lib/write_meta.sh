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

required_vars=(
    "ACCELERATOR" 
    "BUCKET_DIR"
    "BUCKET_NAME"
    "COMMAND"
    "JOB_NAME" 
    "NUM_WORKERS" 
    "TPU_NAME" 
    "VERSION"
    "WORK_DIR"
    "ZONE" 
)
echo "#!/bin/bash" > jobs/$JOB_NAME/config.sh
for var in "${required_vars[@]}"; do
    echo "export $var=\"${!var:-}\"" >> jobs/$JOB_NAME/config.sh
done

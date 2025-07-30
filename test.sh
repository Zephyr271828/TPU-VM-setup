source config.sh

# gcloud alpha compute tpus tpu-vm scp setup_maxtext.sh $TPU_NAME:~/ \
#   --zone=$ZONE --ssh-key-file='~/.ssh/id_rsa' --worker=all

gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
  --zone=$ZONE \
  --ssh-key-file='~/.ssh/id_rsa' \
  --worker=all \
  --command "
  pkill -f python 
  "
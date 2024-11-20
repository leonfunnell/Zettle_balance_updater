# if called with --destroy, it will destroy the infrastructure
# if called with --recreate, it will destroy and recreate the infrastructure

if [ "$1" == "--destroy" ]; then
    destroy=true
    create=false
else
    destroy=false
fi

if [ "$1" == "--recreate" ]; then
    destroy=true
    create=true
else
    create=false
fi

# if no parameters are passed, it will only deploy the infrastructure
if [ "$1" == "" ]; then
    destroy=false
    create=true
fi

# If the variable 'destroy' is set to true, it will destroy the infrastructure.
if [ "$destroy" = true ]; then
  echo "Destroying the infrastructure"
  terraform destroy -auto-approve
  rm -f izettleminbal.zip
fi

# If the variable 'create' is set to true, it will deploy the infrastructure.
if [ "$create" = true ]; then
  echo "Deploying the infrastructure"
  sudo ./zip_lambda.sh
  terraform init
  terraform apply -auto-approve
fi

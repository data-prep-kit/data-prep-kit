#########################################################################
#
# Apply secrets used for running in kind environment
# s3-secret
#########################################################################


if [ -f .env ]; then
  source .env
fi

if [[ -z "${S3_ACCESS_KEY}" ]] || [[ -z "${S3_SECRET_KEY}" ]] || [[ -z "${S3_ENDPOINT}" ]]; then
  echo "Cannot set S3 secret- Environment Variables S3_ACCESS_KEY , S3_SECRET_KEY and S3_ENDPOINT must be set first"
else
  echo "#######################################################################"
  echo "Creating Opaque secret lh-secret-s3"
  echo "#######################################################################"

  S3_ENDPOINT_BASE64=`echo -n ${S3_ENDPOINT}| base64 --wrap 0`
  S3_ACCESS_KEY_BASE64=`echo -n ${S3_ACCESS_KEY}| base64 --wrap 0`
  S3_SECRET_KEY_BASE64=`echo -n ${S3_SECRET_KEY}| base64 --wrap 0`



  cat << EOF | kubectl apply -f -
  apiVersion: v1
  metadata:
      name: s3-secret
  data:
      S3_ENDPOINT: "${S3_ENDPOINT_BASE64}"
      S3_ACCESS_KEY: "${S3_ACCESS_KEY_BASE64}"
      S3_SECRET_KEY: "${S3_SECRET_KEY_BASE64}"
  kind: Secret
  type: Opaque
EOF
  
fi


if [[ -z "${HF_READ_ACCESS_TOKEN}" ]]; then
  echo "Cannot set Hugging Face Token- Environment Variable HF_READ_ACCESS_TOKEN  must be set first"
else
  echo "#######################################################################"
  echo "Creating Opaque secret hf-secret"
  echo "#######################################################################" 

  cat << EOF | kubectl apply -f -
  apiVersion: v1
  kind: Secret
  metadata:
    name: hf-secret
  type: Opaque
  stringData:
        hf-token: "${HF_READ_ACCESS_TOKEN}"
EOF
fi

#########################################################################
#
# Apply secrets used for running in kind environment
# s3-secret
#########################################################################


if [ -f .env ]; then
  source .env
fi

if [[ -n "${S3_ACCESS_KEY}" ]] && [[ -n "${S3_SECRET_KEY}" ]] && [[ -n "${S3_ENDPOINT}" ]]; then
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
      namespace: kubeflow
  data:
      s3-endpoint: "${S3_ENDPOINT_BASE64}"
      s3-key: "${S3_ACCESS_KEY_BASE64}"
      s3-secret: "${S3_SECRET_KEY_BASE64}"
  kind: Secret
  type: Opaque
EOF
  
fi


if [[ -n "${HF_READ_ACCESS_TOKEN}" ]]; then
  echo "#######################################################################"
  echo "Creating Opaque secret hf-secret"
  echo "#######################################################################" 

  cat << EOF | kubectl apply -f -
  apiVersion: v1
  kind: Secret
  metadata:
    name: hf-secret
    namespace: kubeflow
  type: Opaque
  stringData:
        hf-token: "${HF_READ_ACCESS_TOKEN}"
EOF
fi

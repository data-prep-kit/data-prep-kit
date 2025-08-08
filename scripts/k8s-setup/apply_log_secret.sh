#########################################################################
# Apply s3-secret used for running in kind environment
#########################################################################


if [[ -z "${LOG_ACCESS_KEY_BASE64}" ]] || [[ -z "${LOG_SECRET_KEY_BASE64}" ]] || [[ -z "${LOG_ENDPOINT_BASE64}" ]]; then
  echo "Cannot set S3 secret- Environment Variables LOG_ACCESS_KEY_BASE64 , LOG_SECRET_KEY_BASE64 and LOG_ENDPOINT_BASE64 must be set first"
  echo "Values must be base64 encoded. use `echo -n ${v}|base64 --wrap 0`"
  exit 1
fi
echo #######################################################################
echo Creating Opaque secret s3-secret in current namespace
echo #######################################################################

cat << EOF | kubectl apply -f -
apiVersion: v1
metadata:
    name: s3-logs
data:
    AWS_ENDPOINT_URL: "${LOG_ENDPOINT_BASE64}"
    AWS_ACCESS_KEY_ID: "${LOG_ACCESS_KEY_BASE64}"
    AWS_SECRET_ACCESS_KEY: "${LOG_SECRET_KEY_BASE64}"
kind: Secret
type: Opaque
EOF

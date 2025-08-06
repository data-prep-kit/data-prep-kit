#########################################################################
# Apply s3-secret used for running in kind environment
#########################################################################


if [[ -z "${S3_ACCESS_KEY_BASE64}" ]] || [[ -z "${S3_SECRET_KEY_BASE64}" ]] || [[ -z "${S3_ENDPOINT_BASE64}" ]]; then
  echo "Cannot set S3 secret- Environment Variables S3_ACCESS_KEY , S3_SECRET_KEY and S3_ENDPOINT must be set first"
  echo "Values must be base64 encoded. use `echo -n ${v}|base64 --wrap 0`"
  exit 1
fi
echo #######################################################################
echo Creating Opaque secret s3-secret in current namespace
echo #######################################################################

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

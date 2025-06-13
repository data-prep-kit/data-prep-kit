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

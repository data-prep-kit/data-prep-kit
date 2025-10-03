## Usage
## docker build --platform linux/amd64 -t kubectl .
## docker tag kubectl:latest quay.io/dataprep1/data-prep-kit/kubectl:latest
## docker push quay.io/dataprep1/data-prep-kit/kubectl:latest 
##

FROM ubuntu:22.04

# Set environment variables to non-interactive to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set environment variables for kubectl and oc installation
ENV KUBECTL_VERSION="v1.28.0" \
    OC_VERSION="4.14.0"

    # Install dependencies and curl
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    tar \
    gzip \
    ca-certificates \
    gnupg \
    lsb-release \
    apt-transport-https \
    wget \
    git \
    gettext \
    && rm -rf /var/lib/apt/lists/*


RUN wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 && \
    chmod a+x /usr/local/bin/yq

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/

# Install oc
RUN curl -LO "https://mirror.openshift.com/pub/openshift-v4/clients/oc/latest/linux/oc.tar.gz" && \
    tar -xzf oc.tar.gz && \
    mv oc /usr/local/bin/ && \
    rm oc.tar.gz   

    # Verify installation
RUN kubectl version --client
RUN oc version

# Set the default command to bash for interactive use
CMD ["bash"]

#!/bin/bash
# Check if user is allowed to run priviledge workflows
actor=$1                # user triggering the workflow ${{ github.triggering_actor }}
restricted_access=$2    # restricted_access is set to true for forks

allowed_list=("touma-I" "revit13" "roytman")
for user in "${allowed_list[@]}"; do
    if [ "$user" ==  "${{ github.triggering_actor }}" ]; then
        restricted_access=false
        break
    fi
done
if $restricted_access; then
    # Explain and force-fail workflows
    echo "User $actor is not allowed to trigger this workflow."
    echo "$actor is not in list: $allowed_list "
    exit 1
else
    echo "Checking $actor permissions."
    echo "Only select users will be able to trigger this workflow from a fork"
    echo "This prevents the secret from being exposed to all public users"
fi

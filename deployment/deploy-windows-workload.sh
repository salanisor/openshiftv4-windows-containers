#!/bin/bash
# Script written to deploy Windows container workload on OpenShift 4.6

# Set KUBECONFIG: A kubeconfig file is a file used to configure access
# to Kubernetes when used in conjunction with the kubectl commandline tool (or other clients).
export KUBECONFIG=/home/salanis/FAA/aws/auth/kubeconfig

oc project

echo $?

echo "Connecting to your Windows application.."
echo ""
firefox winhttp.apps.ocp4.freebsd.tv 2>/dev/null

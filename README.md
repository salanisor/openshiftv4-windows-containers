How to deploy a Windows Server 2019 compute node on OpenShift 4.6.9

## Prerequisites

1) OpenShift Cluster 4.6.8 configured with HybridOverlay using [OVNKubernetes](https://docs.openshift.com/container-platform/4.6/installing/installing_aws/installing-aws-network-customizations.html#configuring-hybrid-ovnkubernetes_installing-aws-network-customizations) network plugin. 

2) [Windows Machine Config Operator](https://docs.openshift.com/container-platform/4.6/windows_containers/enabling-windows-container-workloads.html#installing-wmco-using-web-console_enabling-windows-container-workloads) (WMCO) installed.

## Preparation

1) Obtain the infrastructure ID from your OpenShift Cluster to apply to your Windows Server 2019 [machineset](https://github.com/salanisor/openshiftv4-windows-containers/blob/793b54fe278a4e38b8615bad70f24105b9e7609a/deployment/000-windows-server-machineset.yaml#L5-L6) yaml file.

```
oc get -o jsonpath='{.status.infrastructureName}{"\n"}' infrastructure cluster
```

2) Search for the latest Windows Server 2019 w/ container support AMI to apply to your Windows Server 2019 [machineset](https://github.com/salanisor/openshiftv4-windows-containers/blob/793b54fe278a4e38b8615bad70f24105b9e7609a/deployment/000-windows-server-machineset.yaml#L29) yaml file.

```
Windows_Server-2019-English-Full-ContainersLatest-
```
![ami-search](/images/ami-search.png)


3) Obtain your cluster's availability zone and region to be applied to your Windows Server 2019 [machineset](https://github.com/salanisor/openshiftv4-windows-containers/blob/793b54fe278a4e38b8615bad70f24105b9e7609a/deployment/000-windows-server-machineset.yaml#L44-L45) yaml file.

4) Create an SSH key to manage your Windows Server 2019 compute nodes, that is seperate from the rest of your OpenShift infrastructure.

```
oc create secret generic cloud-private-key --from-file=private-key.pem=${HOME}/.ssh/<key> \
    -n openshift-windows-machine-config-operator 
```

*Example*:
![windows-machine-ssh-key](/images/prez-secret-ssh-key.png)

## Windows MachineSet

5) Configure the Windows Server 2019 machineset yaml for your cluster: 
- A) **Infrastructure ID**
- B) **Region**
- C) **Availability Zone**

```
apiVersion: machine.openshift.io/v1beta1
kind: MachineSet
metadata:
  labels:
    machine.openshift.io/cluster-api-cluster: <infrastructure-id>
  name: <infrastructure-id>-windows-worker-us-east-2b
  namespace: openshift-machine-api
spec:
  replicas: 1
  selector:
    matchLabels:
      machine.openshift.io/cluster-api-cluster: <infrastructure-id>
      machine.openshift.io/cluster-api-machineset: <infrastructure-id>-windows-worker-us-east-2b
  template:
    metadata:
      labels:
        machine.openshift.io/cluster-api-cluster: <infrastructure-id>
        machine.openshift.io/cluster-api-machine-role: worker
        machine.openshift.io/cluster-api-machine-type: worker
        machine.openshift.io/cluster-api-machineset: <infrastructure-id>-windows-worker-us-east-2b
        machine.openshift.io/os-id: Windows 
    spec:
      metadata:
        labels:
          node-role.kubernetes.io/worker: "" 
      providerSpec:
        value:
          ami:
            id: ami-0710f0d84bb7d9df1
          apiVersion: awsproviderconfig.openshift.io/v1beta1
          blockDevices:
            - ebs:
                iops: 0
                volumeSize: 120
                volumeType: gp2
          credentialsSecret:
            name: aws-cloud-credentials
          deviceIndex: 0
          iamInstanceProfile:
            id: ocp4-pb9pp-worker-profile 
          instanceType: m5a.xlarge #minimum size that doesn't stall pulling container images.
          kind: AWSMachineProviderConfig
          placement:
            availabilityZone: us-east-2b
            region: us-east-2
          securityGroups:
            - filters:
                - name: tag:Name
                  values:
                    - <infrastructure-id>-worker-sg 
          subnet:
            filters:
              - name: tag:Name
                values:
                  - <infrastructure-id>-private-us-east-2b
          tags:
            - name: kubernetes.io/cluster/<infrastructure-id>
              value: owned
          userDataSecret:
            name: windows-user-data 
            namespace: openshift-machine-api
```

###### Applied taint & toleration
<img src="https://github.com/salanisor/openshiftv4-windows-containers/blob/main/images/taint-toleration.png" height="100" width="500"/>

## RuntimeClass

```
apiVersion: node.k8s.io/v1beta1
kind: RuntimeClass
metadata:
  name: windows-k8s-aws
handler: 'docker'
scheduling:
  nodeSelector: 
    kubernetes.io/os: 'windows'
    kubernetes.io/arch: 'amd64'
    node.kubernetes.io/windows-build: '10.0.17763'
  tolerations: 
  - effect: NoSchedule
    key: os
    operator: Equal
    value: "Windows"
```
    
## Windows Service

```
apiVersion: v1
kind: Service
metadata:
  name: win-webserver
  labels:
    app: win-webserver
spec:
  ports:
    # the port that this service should serve on
  - port: 80
    targetPort: 80
  selector:
    app: win-webserver
  type: LoadBalancer
```
  
## Route exposing the service
```
apiVersion: v1
items:
- apiVersion: route.openshift.io/v1
  kind: Route
  metadata:
    labels:
      app: win-webserver
    name: windows-route
    namespace: windows-workload
  spec:
    host: winhttp.apps.ocp4.freebsd.tv
    port:
      targetPort: 80
    to:
      kind: Service
      name: win-webserver
      weight: 100
    wildcardPolicy: None
  status: {}
```

## Windows HTTP Server deployment

```
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: win-webserver
  name: win-webserver
  namespace: windows-workload
spec:
  selector:
    matchLabels:
      app: win-webserver
  replicas: 1
  template:
    metadata:
      labels:
        app: win-webserver
      name: win-webserver
    spec:
      tolerations:
      - key: "os"
        value: "Windows"
        Effect: "NoSchedule"
      containers:
      - name: windowswebserver
        image: mcr.microsoft.com/windows/servercore:ltsc2019
        imagePullPolicy: IfNotPresent
        command:
        - powershell.exe
        - -command
        - $listener = New-Object System.Net.HttpListener; $listener.Prefixes.Add('http://*:80/'); $listener.Start();Write-Host('Listening at http://*:80/'); while ($listener.IsListening) { $context = $listener.GetContext(); $response = $context.Response; $content='<html><body><H1>Red Hat OpenShift + Windows Container Workloads</H1></body></html>'; $buffer = [System.Text.Encoding]::UTF8.GetBytes($content); $response.ContentLength64 = $buffer.Length; $response.OutputStream.Write($buffer, 0, $buffer.Length); $response.Close(); };
        securityContext:
          windowsOptions:
            runAsUserName: "ContainerAdministrator"
      nodeSelector:
        beta.kubernetes.io/os: windows
```

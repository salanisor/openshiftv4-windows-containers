#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, canit00 <[email protected]>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import sys,subprocess,os,time

# Set KUBECONFIG: A kubeconfig file is a file used to configure access
# to Kubernetes when used in conjunction with the kubectl command line tool (or other clients).
os.environ['KUBECONFIG'] = '/home/salanis/FAA/aws/auth/kubeconfig'

# Check that you're able to list the current project - thus logged in to the cluster.
check_project = subprocess.call(['oc', 'project'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if check_project == 0:
    print("")
    # A MachineSet is an immutable abstraction over Machines.
    print("Deploying windows machineset")
    print("executing: oc apply -f 000-windows-server-machineset.yaml")
    for I in range(30):
        sys.stdout.write('.')
        sys.stdout.flush() 
        time.sleep(.1)
    print("")
    print("")
    # Namespaces are a way to divide cluster resources between multiple tenants (via resource quota).
    print("Creating windows-workload namespace")
    print("executing: oc apply -f 001-windows-workload-namespace.yaml")
    for I in range(30):
        sys.stdout.write('.')
        sys.stdout.flush() 
        time.sleep(.1)
    print("")
    print("")
    # An abstract way to expose an application running on a set of Pods as a network service.
    print("Creating a new service for the windows application on port 80")
    print("executing: oc apply -f 002-windows-service.yaml")
    for I in range(30):
        sys.stdout.write('.')
        sys.stdout.flush() 
        time.sleep(.1)
    print("")
    print("")
    # An abstract way to expose an application running on a set of Pods as a network service.
    print("Creating a new service for the windows application on port 80")
    print("executing: oc apply -f 002-windows-service.yaml")
    for I in range(30):
        sys.stdout.write('.')
        sys.stdout.flush() 
        time.sleep(.1)
    print("")
    print("")
else:
    exit(1)

#FINAL VERSION
from typing import Protocol
import boto3
import os
import paramiko
import time
import requests


def create_instance(instance_type: str, number_of_instance=1):
    """
    Creates {number_of_instance} EC2 instances based on the given instance type 

    Args:
        instance_type ([string]): [instance image id]
        number_of_instance (int, optional): [number of copies of instance]. Defaults to 1.

    Returns:
        [ec2.instance]: [an EC2 instance object which contains information about the instances]
    """

    # create a new EC2 instance
    ec2 = boto3.client('ec2', region_name='us-east-1')

    instances = ec2.run_instances(
        ImageId='ami-0525587ae81868bfa',  # Ubuntu Server image
        MinCount=1,
        MaxCount=number_of_instance,
        InstanceType=instance_type,
        KeyName='marwanekey2'  # key-pair value
    )

    ec2 = boto3.resource('ec2')
    for instance in instances['Instances']:
        instance_ = ec2.Instance(id=instance['InstanceId'])
        instance_.wait_until_running()  # wait until the instance is up and running
        print(
            f"--> Instance {instance['InstanceId']} of type {instance_type} is up and running")

    return instances


def terminate_instance(instance_information):
    """
    Terminates an instance

    Args:
        instance_information ([EC2 instance info]): [information regarding a single instance]
    """
    ec2_client = boto3.client("ec2")
    response = ec2_client.terminate_instances(
        InstanceIds=[instance_information['InstanceId']])
    print(f"Instance {instance_information['InstanceId']} Terminated")


def get_public_ip(instance_id):
    ec2_client = boto3.client("ec2")
    reservations = ec2_client.describe_instances(
        InstanceIds=[instance_id]).get("Reservations")

    for reservation in reservations:
        for instance in reservation['Instances']:
            print(instance.get("PublicIpAddress"))


def run_ssh_commands(instance):
    """
    Runs SSH commands one by one on a given instance

    Args:
        instance ([EC2 Intance]): [an EC2 intance]
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    privkey = paramiko.RSAKey.from_private_key_file(
        f'/home/alex/.ssh/marwanekey2.pem')

    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(id=instance['InstanceId'])
    # double check that instance is running before running commands
    instance.wait_until_running()
    ip_address = instance.public_ip_address
    time.sleep(10)
    try:
        ssh.connect(hostname=ip_address, username='ubuntu', pkey=privkey)
        print(f'SSH connection to {ip_address} successful')
    except Exception as e:
        print(e)
    # install flask and deploy a simple script on each instance
    commands = ['sudo apt-get update',
                'yes | sudo apt install python3-pip',
                'sudo pip install Flask',
                'git clone "https://github.com/CommissarSilver/cloud-computing-tp1.git"',
                'cd cloud-computing-tp1 && sudo python3 hello.py']
    try:
        for command in commands[:-1]:
            print(command)
            stdin, stdout, stderr = ssh.exec_command(command)
            stdout.read()
            stderr.read()

        stdin, stdout, stderr = ssh.exec_command(commands[-1])
        print('--> Commands executed successfully')
    except Exception as e:
        print(e)


def create_load_balancer(name, s):
    """
    creates an application load balancer

    Args:
        name ([str]): [load balancer's name]
        subnets ([type]): [availability zones for the load balancer]

    Returns:
        [load balancer response object]
    """
    client = boto3.client('elbv2')
    load_balancer_response = client.create_load_balancer(
        Name=name, Subnets=subnets)
    print('Load Balancer initialized successfully')
    return load_balancer_response


def create_target_group(name, load_balancer_response):
    """
    creatse a target group given a load balancer

    Args:
        name ([str]): [target group name]
        load_balancer_response : [load balancer response object]

    Returns:
        target_group: target group reponse object 
    """
    client = boto3.client('elbv2')
    target_group = client.create_target_group(
        Name=name, Protocol='HTTP', Port=80, VpcId=load_balancer_response['LoadBalancers'][0]['VpcId'])
    print('Target Group initialized successfully')
    return target_group


def create_listener(target_group_response, load_balancer_response):
    """
    creates a listener and binds it to the given target group and load balancer

    Args:
        target_group_response 
        load_balancer_response 

    Returns:
        listener object
    """
    response = client.create_listener(DefaultActions=[{'TargetGroupArn': target_group_response['TargetGroups'][0]['TargetGroupArn'], 'Type': 'forward', }, ],
                                      LoadBalancerArn=load_balancer_response['LoadBalancers'][0]['LoadBalancerArn'],
                                      Port=80,
                                      Protocol='HTTP',
                                      )
    print('Listener initialized successfully')
    return response


def register_to_target_group(target_group_response, instances):
    """
    binds given instances to given target group

    Args:
        target_group_response : [target group response object]
        instances : [instance reponse object]
    """
    client.register_targets(TargetGroupArn=target_group_response['TargetGroups'][0]['TargetGroupArn'], Targets=[
        {'Id': instance['InstanceId']} for instance in instances['Instances']])





print('Initializaing Instances:')
cluster1_instances = create_instance('m4.large', 4)
cluster2_instances = create_instance('t2.xlarge', 4)

print('Running SSH commands')
for instance in cluster1_instances['Instances']:
    run_ssh_commands(instance)
for instance in cluster2_instances['Instances']:
    run_ssh_commands(instance)


client = boto3.client('elbv2')
load_balancer_1 = create_load_balancer(name='LoadBalancerOne', subnets=['subnet-03be0ab145592f886','subnet-0ff26032c2f21ea3d','subnet-0291e8863c4f5b975',
         'subnet-02e2621838ac1f149','subnet-02ab2c272bcfc9cda','subnet-08aa2626900afa1fc'])


cluster1_target_group = create_target_group(
    name='cluster1', load_balancer_response=load_balancer_1)
cluster2_target_group = create_target_group(
    name='cluster2', load_balancer_response=load_balancer_1)

listener = create_listener(
    target_group_response=cluster1_target_group, load_balancer_response=load_balancer_1)

print('Assigning rules to listener')
client.create_rule(ListenerArn=listener['Listeners'][0]['ListenerArn'],
                   Priority=1,
                   Conditions=[
                       {'Field': 'path-pattern', 'Values': ['*/cluster1']}],
                   Actions=[{'Type': 'forward', 'TargetGroupArn': cluster1_target_group['TargetGroups'][0]['TargetGroupArn']}])
client.create_rule(ListenerArn=listener['Listeners'][0]['ListenerArn'],
                   Priority=2,
                   Conditions=[
                       {'Field': 'path-pattern', 'Values': ['*/cluster2']}],
                   Actions=[{'Type': 'forward', 'TargetGroupArn': cluster2_target_group['TargetGroups'][0]['TargetGroupArn']}])


register_to_target_group(cluster1_target_group, cluster1_instances)
register_to_target_group(cluster2_target_group, cluster2_instances)

print('Initilization Finished.\n Starting Test.')

#####################################TESTING PART AND METRICS#########################################

commands = ['git clone "https://github.com/marsup13/lab1LOG8415.git"',
            'cd lab1LOG8415/scripts && sudo chmod +x metrics.sh && sudo ./metrics.sh']
for cmd in commands:
	os.system(cmd)
	


#####################################################PLOT THE GRAPHS AND GIVE TABLES FOR METRICS############################################

import pandas as pd
#%matplotlib inline
import matplotlib.pyplot as plt
import json
from IPython.display import display, HTML
import os


# Get the current working directory
cwd = os.getcwd()

# Print the current working directory
print("Current working directory: {0}".format(cwd))
os.chdir(f'{os.getcwd()}/JSONFiles')
print(os.getcwd())



# load data using Python JSON module
with open('ActiveConnectionCount_Sum.json','r') as f:
    data = json.loads(f.read())
# Flatten data
df_ActiveConnectionCount_Sum = pd.json_normalize(data, record_path =['Datapoints'])
print(df_ActiveConnectionCount_Sum)
print(df_ActiveConnectionCount_Sum.info())
#fig1 = plt.figure()
ax1 = plt.gca()
df_ActiveConnectionCount_Sum['Time'] = pd.to_datetime(df_ActiveConnectionCount_Sum['Timestamp']).dt.time
df_ActiveConnectionCount_Sum.plot(x='Time',y='Sum',color='red', 
                                 title='ActiveConnectionCount_Sum').get_figure().savefig(
                                                                         'ActiveConnectionCount_Sum.png')

plt.show()





with open('NewConnectionCount_Sum.json','r') as f:
    data = json.loads(f.read())
# Flatten data
df_NewConnectionCount_Sum = pd.json_normalize(data, record_path =['Datapoints'])
print(df_NewConnectionCount_Sum)
print(df_NewConnectionCount_Sum.info())
df_NewConnectionCount_Sum['Time'] = pd.to_datetime(df_NewConnectionCount_Sum['Timestamp']).dt.time
ax2 = plt.gca()
df_NewConnectionCount_Sum.plot(x='Time',y='Sum',color='red', 
                                  ax=ax2, title='NewConnectionCount_Sum')
ax2.figure.savefig('NewConnectionCount_Sum.png')
plt.show()





# load data using Python JSON module
with open('RequestCount_Sum.json','r') as f:
    data = json.loads(f.read())
# Flatten data
df_RequestCount_Sum = pd.json_normalize(data, record_path =['Datapoints'])
print(df_RequestCount_Sum)
print(df_RequestCount_Sum.info)
df_RequestCount_Sum['Time'] = pd.to_datetime(df_RequestCount_Sum['Timestamp']).dt.time

ax3 = plt.gca()
df_RequestCount_Sum.plot(x='Time',y='Sum',color='red', 
                                  ax=ax3, title='RequestCount_Sum')
ax3.figure.savefig('RequestCount_Sum.png')
plt.show()




# load data using Python JSON module
with open('RuleEvaluations_Sum.json','r') as f:
    data = json.loads(f.read())
# Flatten data
df_RuleEvaluations_Sum = pd.json_normalize(data, record_path =['Datapoints'])
print(df_RuleEvaluations_Sum)
print(df_RuleEvaluations_Sum.info)

df_RuleEvaluations_Sum['Time'] = pd.to_datetime(df_RuleEvaluations_Sum['Timestamp']).dt.time
ax4 = plt.gca()
df_RuleEvaluations_Sum.plot(x='Time',y='Sum',color='red', 
                                  ax=ax4, title='RuleEvaluations_Sum')

ax4.figure.savefig('RuleEvaluations_Sum.png')
plt.show()





# load data using Python JSON module
with open('cluster1_RequestCountPerTarget_Sum.json','r') as f:
    data1 = json.loads(f.read())
with open('cluster2_RequestCountPerTarget_Sum.json','r') as f:
    data2 = json.loads(f.read())
# Flatten data
df_cluster1_RequestCountPerTarget_Sum = pd.json_normalize(data1, record_path =['Datapoints'])
df_cluster2_RequestCountPerTarget_Sum = pd.json_normalize(data2, record_path =['Datapoints'])

print('cluster1_RequestCountPerTarget_Sum')
display(df_cluster1_RequestCountPerTarget_Sum)
print('****************')
print('****************')
display(df_cluster1_RequestCountPerTarget_Sum.info)
print('****************')
print('****************')

print('cluster2_RequestCountPerTarget_Sum')
display(df_cluster2_RequestCountPerTarget_Sum)
print('****************')
print('****************')
display(df_cluster2_RequestCountPerTarget_Sum.info)
print('****************')
print('****************')

df_cluster1_RequestCountPerTarget_Sum['Time'] = pd.to_datetime(df_cluster1_RequestCountPerTarget_Sum['Timestamp']).dt.time
df_cluster2_RequestCountPerTarget_Sum['Time'] = pd.to_datetime(df_cluster2_RequestCountPerTarget_Sum['Timestamp']).dt.time

ax5 = plt.gca()
df_cluster1_RequestCountPerTarget_Sum.plot(x='Time',y='Sum',color='red', 
                                  ax=ax5)
df_cluster2_RequestCountPerTarget_Sum.plot(x='Time',y='Sum',color='blue', 
                                  ax=ax5, title='cluster1 (red) and cluster 2 (blue) RequestCountPerTarget_Sum')

ax5.figure.savefig('clusters_RequestCountPerTarget_Sum_Comparison.png')
plt.show()





# load data using Python JSON module
with open('cluster1_TargetResponseTime_Sum.json','r') as f:
    data1 = json.loads(f.read())
with open('cluster2_TargetResponseTime_Sum.json','r') as f:
    data2 = json.loads(f.read())
# Flatten data
df_cluster1_TargetResponseTime_Sum = pd.json_normalize(data1, record_path =['Datapoints'])
df_cluster2_TargetResponseTime_Sum = pd.json_normalize(data2, record_path =['Datapoints'])

print('cluster1_TargetResponseTime_Sum')
display(df_cluster1_TargetResponseTime_Sum)
print('****************')
print('****************')
display(df_cluster1_TargetResponseTime_Sum.info)
print('****************')
print('****************')

print('cluster2_TargetResponseTime_Sum')
display(df_cluster2_TargetResponseTime_Sum)
print('****************')
print('****************')
display(df_cluster2_TargetResponseTime_Sum.info)
print('****************')
print('****************')

df_cluster1_TargetResponseTime_Sum['Time'] = pd.to_datetime(df_cluster1_TargetResponseTime_Sum['Timestamp']).dt.time
df_cluster2_TargetResponseTime_Sum['Time'] = pd.to_datetime(df_cluster2_TargetResponseTime_Sum['Timestamp']).dt.time

ax6 = plt.gca()
df_cluster1_TargetResponseTime_Sum.plot(x='Time',y='Sum',color='red', 
                                  ax=ax6)
df_cluster2_TargetResponseTime_Sum.plot(x='Time',y='Sum',color='blue', 
                                  ax=ax6, title='cluster1 (red) and cluster 2 (blue) TargetResponseTime_Sum')
ax6.figure.savefig('clusters_TargetResponseTime_Sum_Comparison.png')
plt.show()


###############################################TERMINATE INSTANCES#################################################

for instance in cluster1_instances['Instances']:
    terminate_instance(instance)
for instance in cluster2_instances['Instances']:
    terminate_instance(instance)

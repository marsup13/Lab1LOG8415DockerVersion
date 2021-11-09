#from typing import Protocol
import boto3
import os
import paramiko
import time
import requests
from datetime import datetime, timedelta
from matplotlib import pyplot as plt


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
        ImageId='ami-09e67e426f25ce0d7',  # Ubuntu Server image
        MinCount=1,
        MaxCount=number_of_instance,
        InstanceType=instance_type,
        KeyName='ec2-keypair'  # key-pair value
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
    privkey = paramiko.RSAKey.from_private_key_file('ec2-keypair.pem')

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


def create_load_balancer(name, subnets):
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
    response = client.create_listener(DefaultActions=[
        {'TargetGroupArn': target_group_response['TargetGroups'][0]['TargetGroupArn'], 'Type': 'forward', }, ],
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


def test(load_balancer_url):
    # DNS address of the load balancer, like
    url = f'http://{load_balancer_url}/'

    def sendRequest(cluster, iter):
        try:
            for i in range(iter):
                print('%3d' % i + ': ', end='')
                r = requests.get(url + cluster)
                try:
                    print(str(r.json()) + '\tstatus ' + str(r.status_code))
                except:
                    print(
                        '\033[0;31mFailed to responce\033[0m\t\t\tstatus ' + str(r.status_code))
        except Exception as e:
            print(f"Exception occured in sending requests: \n {e}")

    def scenario1(cluster):
        print('\033[1;33m' + '-' * 15 + cluster +
              ' starts scenario1' + '-' * 15 + '\033[0m')
        start = time.time()
        sendRequest(cluster, 200)
        duration = time.time() - start

        print('\033[1;33m' + '-' * 8, end='')
        print(cluster + ' completed scenario1 in ' + '%.2f' %
              duration + ' sec', end='')
        print('-' * 7 + '\033[0m', end='\n\n')

    def scenario2(cluster):
        print('\033[1;36m' + '-' * 15 + cluster +
              ' starts scenario2' + '-' * 15 + '\033[0m')
        start = time.time()
        sendRequest(cluster, 500)
        duration = time.time() - start

        print('\033[1;36m' + '-' * 8, end='')
        print(cluster + ' completed scenario2 in ' + '%.2f' %
              duration + ' sec', end='')
        print('-' * 7 + '\033[0m', end='\n\n')

    scenario1('cluster1')
    scenario2('cluster2')


print('Initializaing Instances:')
cluster1_instances = create_instance('t2.micro', 2)
cluster2_instances = create_instance('t2.micro', 2)

print('Running SSH commands')
for instance in cluster1_instances['Instances']:
    run_ssh_commands(instance)
for instance in cluster2_instances['Instances']:
    run_ssh_commands(instance)

client = boto3.client('elbv2')
load_balancer_1 = create_load_balancer(name='LoadBalancerOne',
                                       subnets=['subnet-03c5c7430a5220718', 'subnet-0ea8ee263c594b48c',
                                                'subnet-05b40d02f69eb368a', 'subnet-0b43452ba329ed175',
                                                'subnet-0c5bb5c903b5dbd9d', 'subnet-04159a4fcc1d12324'])

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
                   Actions=[{'Type': 'forward',
                             'TargetGroupArn': cluster1_target_group['TargetGroups'][0]['TargetGroupArn']}])
client.create_rule(ListenerArn=listener['Listeners'][0]['ListenerArn'],
                   Priority=2,
                   Conditions=[
                       {'Field': 'path-pattern', 'Values': ['*/cluster2']}],
                   Actions=[{'Type': 'forward',
                             'TargetGroupArn': cluster2_target_group['TargetGroups'][0]['TargetGroupArn']}])

register_to_target_group(cluster1_target_group, cluster1_instances)
register_to_target_group(cluster2_target_group, cluster2_instances)

print('Initialization Finished.\n Starting Test. (sleep for 60s for initialization to finish.')
time.sleep(60)
test(load_balancer_1['LoadBalancers'][0]['DNSName'])

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
response = cloudwatch.list_metrics(Namespace='AWS/ApplicationELB')
print(cluster1_target_group['TargetGroups'][0]['TargetGroupArn'].split(':')[-1])

load_balancer_request_counts_sum = cloudwatch.get_metric_statistics(Namespace='AWS/ApplicationELB',
                                                                    MetricName='RequestCount',
                                                                    Dimensions=[
                                                                        {'Name': 'LoadBalancer',
                                                                         'Value': '/'.join(
                                                                             load_balancer_1['LoadBalancers'][0][
                                                                                 'LoadBalancerArn'].split(':')[
                                                                                 -1].split('/')[1:])}
                                                                    ],
                                                                    StartTime=datetime.utcnow() - timedelta(
                                                                        seconds=1200),
                                                                    EndTime=datetime.utcnow(),
                                                                    Period=1,
                                                                    Statistics=['Sum'])

active_connection_counts_sum = cloudwatch.get_metric_statistics(Namespace='AWS/ApplicationELB',
                                                                MetricName='ActiveConnectionCount',
                                                                Dimensions=[
                                                                    {'Name': 'LoadBalancer',
                                                                     'Value': '/'.join(
                                                                         load_balancer_1['LoadBalancers'][0][
                                                                             'LoadBalancerArn'].split(':')[
                                                                             -1].split('/')[1:])}
                                                                ],
                                                                StartTime=datetime.utcnow() - timedelta(
                                                                    seconds=1200),
                                                                EndTime=datetime.utcnow(),
                                                                Period=1,
                                                                Statistics=['Sum'])

new_connection_counts_sum = cloudwatch.get_metric_statistics(Namespace='AWS/ApplicationELB',
                                                             MetricName='NewConnectionCount',
                                                             Dimensions=[
                                                                 {'Name': 'LoadBalancer',
                                                                  'Value': '/'.join(
                                                                      load_balancer_1['LoadBalancers'][0][
                                                                          'LoadBalancerArn'].split(':')[
                                                                          -1].split('/')[1:])}
                                                             ],
                                                             StartTime=datetime.utcnow() - timedelta(
                                                                 seconds=1200),
                                                             EndTime=datetime.utcnow(),
                                                             Period=1,
                                                             Statistics=['Sum'])

rule_evaluations_counts_sum = cloudwatch.get_metric_statistics(Namespace='AWS/ApplicationELB',
                                                               MetricName='RuleEvaluations',
                                                               Dimensions=[
                                                                   {'Name': 'LoadBalancer',
                                                                    'Value': '/'.join(
                                                                        load_balancer_1['LoadBalancers'][0][
                                                                            'LoadBalancerArn'].split(':')[
                                                                            -1].split('/')[1:])}
                                                               ],
                                                               StartTime=datetime.utcnow() - timedelta(
                                                                   seconds=1200),
                                                               EndTime=datetime.utcnow(),
                                                               Period=1,
                                                               Statistics=['Sum'])

target_response_time_sum = cloudwatch.get_metric_statistics(Namespace='AWS/ApplicationELB',
                                                            MetricName='TargetResponseTime',
                                                            Dimensions=[
                                                                {'Name': 'LoadBalancer',
                                                                 'Value': '/'.join(
                                                                     load_balancer_1['LoadBalancers'][0][
                                                                         'LoadBalancerArn'].split(':')[
                                                                         -1].split('/')[1:])}
                                                            ],
                                                            StartTime=datetime.utcnow() - timedelta(
                                                                seconds=1200),
                                                            EndTime=datetime.utcnow(),
                                                            Period=1,
                                                            Statistics=['Sum'])

cluster1_target_response_time_avg = cloudwatch.get_metric_statistics(Namespace='AWS/ApplicationELB',
                                                            MetricName='TargetResponseTime',
                                                            Dimensions=[
                                                                {'Name': 'TargetGroup', 'Value':
                                                                    cluster1_target_group['TargetGroups'][0][
                                                                        'TargetGroupArn'].split(':')[-1]
                                                                 },
                                                                {'Name': 'LoadBalancer',
                                                                 'Value': '/'.join(
                                                                     load_balancer_1['LoadBalancers'][0][
                                                                         'LoadBalancerArn'].split(':')[
                                                                         -1].split('/')[1:])}
                                                            ],
                                                            StartTime=datetime.utcnow() - timedelta(
                                                                seconds=1200),
                                                            EndTime=datetime.utcnow(),
                                                            Period=1,
                                                            Statistics=['Average'])

cluster2_target_response_time_avg = cloudwatch.get_metric_statistics(Namespace='AWS/ApplicationELB',
                                                            MetricName='TargetResponseTime',
                                                            Dimensions=[
                                                                {'Name': 'TargetGroup', 'Value':
                                                                    cluster2_target_group['TargetGroups'][0][
                                                                        'TargetGroupArn'].split(':')[-1]
                                                                 },
                                                                {'Name': 'LoadBalancer',
                                                                 'Value': '/'.join(
                                                                     load_balancer_1['LoadBalancers'][0][
                                                                         'LoadBalancerArn'].split(':')[
                                                                         -1].split('/')[1:])}
                                                            ],
                                                            StartTime=datetime.utcnow() - timedelta(
                                                                seconds=1200),
                                                            EndTime=datetime.utcnow(),
                                                            Period=1,
                                                            Statistics=['Average'])

cluster1_target_request_time_per_counter_sum = cloudwatch.get_metric_statistics(Namespace='AWS/ApplicationELB',
                                                            MetricName='RequestCountPerTarget',
                                                            Dimensions=[
                                                                {'Name': 'TargetGroup', 'Value':
                                                                    cluster1_target_group['TargetGroups'][0][
                                                                        'TargetGroupArn'].split(':')[-1]
                                                                 },
                                                                {'Name': 'LoadBalancer',
                                                                 'Value': '/'.join(
                                                                     load_balancer_1['LoadBalancers'][0][
                                                                         'LoadBalancerArn'].split(':')[
                                                                         -1].split('/')[1:])}
                                                            ],
                                                            StartTime=datetime.utcnow() - timedelta(
                                                                seconds=1200),
                                                            EndTime=datetime.utcnow(),
                                                            Period=1,
                                                            Statistics=['Sum'])

cluster2_target_request_time_per_counter_sum = cloudwatch.get_metric_statistics(Namespace='AWS/ApplicationELB',
                                                            MetricName='RequestCountPerTarget',
                                                            Dimensions=[
                                                                {'Name': 'TargetGroup', 'Value':
                                                                    cluster2_target_group['TargetGroups'][0][
                                                                        'TargetGroupArn'].split(':')[-1]
                                                                 },
                                                                {'Name': 'LoadBalancer',
                                                                 'Value': '/'.join(
                                                                     load_balancer_1['LoadBalancers'][0][
                                                                         'LoadBalancerArn'].split(':')[
                                                                         -1].split('/')[1:])}
                                                            ],
                                                            StartTime=datetime.utcnow() - timedelta(
                                                                seconds=1200),
                                                            EndTime=datetime.utcnow(),
                                                            Period=1,
                                                            Statistics=['Sum'])

y_axis = []
x_axis = []
for data in sorted(load_balancer_request_counts_sum['Datapoints'], key=lambda d: d['Timestamp']):
    x_axis.append(data['Timestamp'])
    y_axis.append(data['Sum'])
fig = plt.figure(figsize=(15, 10))
plt.plot(x_axis, y_axis, label='Load Balancer Request Counts - Sum')
plt.legend()
fig.savefig('EB_Request_Count_demo.png', dpi=fig.dpi)

y_axis = []
x_axis = []
for data in sorted(active_connection_counts_sum['Datapoints'], key=lambda d: d['Timestamp']):
    x_axis.append(data['Timestamp'])
    y_axis.append(data['Sum'])
fig = plt.figure(figsize=(15, 10))
plt.plot(x_axis, y_axis, label='Active Connection Counts - Sum')
plt.legend()
fig.savefig('Active_Conn_Count_demo.png', dpi=fig.dpi)

y_axis = []
x_axis = []
for data in sorted(new_connection_counts_sum['Datapoints'], key=lambda d: d['Timestamp']):
    x_axis.append(data['Timestamp'])
    y_axis.append(data['Sum'])
fig = plt.figure(figsize=(15, 10))
plt.plot(x_axis, y_axis, label='New Connection Counts - Sum')
plt.legend()
fig.savefig('New_Conn_Count_demo.png', dpi=fig.dpi)

y_axis = []
x_axis = []
for data in sorted(rule_evaluations_counts_sum['Datapoints'], key=lambda d: d['Timestamp']):
    x_axis.append(data['Timestamp'])
    y_axis.append(data['Sum'])
fig = plt.figure(figsize=(15, 10))
plt.plot(x_axis, y_axis, label='Rule Evaluation Counts - Sum')
plt.legend()
fig.savefig('Rule_Eva_Count_demo.png', dpi=fig.dpi)

y_axis = []
x_axis = []
for data in sorted(target_response_time_sum['Datapoints'], key=lambda d: d['Timestamp']):
    x_axis.append(data['Timestamp'])
    y_axis.append(data['Sum'])
fig = plt.figure(figsize=(15, 10))
plt.plot(x_axis, y_axis, label='Load Balancer Target Response Time - Sum')
plt.legend()
fig.savefig('LB_Resp_T_demo.png', dpi=fig.dpi)

cluster1_y_axis = []
cluster1_x_axis = []
cluster2_y_axis = []
cluster2_x_axis = []
for data in sorted(cluster1_target_response_time_avg['Datapoints'], key=lambda d: d['Timestamp']):
    cluster1_x_axis.append(data['Timestamp'])
    cluster1_y_axis.append(data['Average'])
for data in sorted(cluster2_target_response_time_avg['Datapoints'], key=lambda d: d['Timestamp']):
    cluster2_x_axis.append(data['Timestamp'])
    cluster2_y_axis.append(data['Average'])
fig = plt.figure(figsize=(15, 10))
plt.plot(cluster1_x_axis, cluster1_y_axis, label='Cluster 1 Target Response Time - Average')
plt.plot(cluster2_x_axis, cluster2_y_axis, label='Cluster 2 Target Response Time - Average')
plt.legend()
fig.savefig('Cluster_Avg_T_demo.png', dpi=fig.dpi)

cluster1_y_axis = []
cluster1_x_axis = []
cluster2_y_axis = []
cluster2_x_axis = []
for data in sorted(cluster1_target_request_time_per_counter_sum['Datapoints'], key=lambda d: d['Timestamp']):
    cluster1_x_axis.append(data['Timestamp'])
    cluster1_y_axis.append(data['Sum'])
for data in sorted(cluster2_target_request_time_per_counter_sum['Datapoints'], key=lambda d: d['Timestamp']):
    cluster2_x_axis.append(data['Timestamp'])
    cluster2_y_axis.append(data['Sum'])
fig = plt.figure(figsize=(15, 10))
plt.plot(cluster1_x_axis, cluster1_y_axis, label='Cluster 1 Target Request Time Per Counter - Sum')
plt.plot(cluster2_x_axis, cluster2_y_axis, label='Cluster 2 Target Request Time Per Counter - Sum')
plt.legend()
fig.savefig('Cluster_Avg_Sum_demo.png', dpi=fig.dpi)

for instance in cluster1_instances['Instances']:
    terminate_instance(instance)

for instance in cluster2_instances['Instances']:
    terminate_instance(instance)

#!/usr/bin/python
# -*- coding: utf-8 -*-

from logging import Filter
from functions_create import create_instance, create_keyPair, export_keyPair, create_securityGroup, run_instance, create_image, create_loadBalancer, all_subnets, create_autoscaling, create_tg
from functions_delete import delete_asg_instances,delete_loadbalancer_listener, delete_targetgroup, delete_launch, delete_instance
from permissions import permissoes_NV, permissoes_ohio
from script_postgres import USER_DATA_POSTGRES
import logging
import time




# OHIO
# ------------------------------------------------------------------------------------------------
# Variáveis locais para a construção da instância em Ohio

local = "us-east-2"
name_keyPair = "chave"
file_name = 'Projeto'
image = "ami-0629230e074c580f2"
instance_type = "t2.micro"
group_name = 'sg_OHIO'
desc = 'teste'
instance_name = 'ohio-postgres'

# ------------------------------------------------------------------------------------------------
# Variáveis locais para a construção da instância em North Virginia

local_NV = "us-east-1"
image_NV = "ami-0279c3b3186e54acd"
name_keyPair_NV = "key"
group_name_NV = "sg_NV"
image_name = "ana_AMI"
targetGroupName='grpTargetNV'
instance_nameNV="nv-django"
lb_name = 'loadBalancerNV'
launch_name = 'image_launched'
autoScaling_name = 'autoScaling-nv'
policy_name = 'NV-autoscaling-policy'
as_instance_name = "as-instance"

# ------------------------------------------------------------------------------------------------

logging.basicConfig(filename='log.txt', filemode='w',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

# ------------------------------------------------------------------------------------------------

logging.info("Starting the program...")

print("-------------------------")
print("The program is running...")
print("-------------------------")

logging.info("Deleting the old structures...")

delete_loadbalancer_listener(local_NV, lb_name)

delete_targetgroup(local_NV, targetGroupName)

delete_asg_instances(local_NV, autoScaling_name)

delete_launch(local_NV, launch_name)

logging.info("Structures deleted!")


print(" ")
print("Creating a Postgres instance in Ohio")
logging.info("Creating a Postgres instance in Ohio")
print(" ")

# cria uma instância EC2
client = create_instance(local)

# descobre o vpc da região de criação da instância
id_vpc = client.describe_vpcs()['Vpcs'][0]['VpcId']

# cria uma chave e associa ela a instância criada
key, private_key = create_keyPair(client, name_keyPair)

print("Key pair created, name: " + name_keyPair)
logging.info("Key pair created, name: " + name_keyPair)
print(" ")

# exporta essa chave para um arquivo .pem
export_keyPair(private_key, name_keyPair)
print("A .pem file with the key created, name: " + name_keyPair + ".pem")
logging.info("A .pem file with the key created, name: " + name_keyPair + ".pem")
print(" ")

# deleta a instancia antes de criar um novo ou apagar o security group
delete_instance(client, instance_name)

# criação de um security group
create_securityGroup(client, id_vpc, permissoes_ohio, group_name, desc)
print("Security group for the instance " + instance_name + " created, name: " + group_name)
logging.info("Security group for the instance " + instance_name + " created, name: " + group_name)
print(" ")

# criação da instâncias com os atributos anteriores
instancia, id_instancia = run_instance(client, image, USER_DATA_POSTGRES, name_keyPair, group_name, instance_type) 
client.create_tags(Resources=[id_instancia], Tags=[{'Key':'Name', 'Value':instance_name}])


print("Postgres instance in Ohio created!")
logging.info("Postgres instance in Ohio created!")
print("--------------------------------------------------")
print(" ")



# NORTH VIRGINIA

print(" ")
print("Creating the Django instance in North Virginia")
logging.info("Creating the Django instance in North Virginia")
# cria uma instância EC2
client_NV = create_instance(local_NV)

# descobre o vpc da região de criação da instância
id_vpc_NV = client_NV.describe_vpcs()['Vpcs'][0]['VpcId']

# cria uma chave e associa ela a instância criada
print(" ")
key, private_key = create_keyPair(client_NV, name_keyPair_NV)
print("Key pair created, name: " + name_keyPair_NV)
logging.info("Key pair created, name: " + name_keyPair_NV)
print(" ")

# exporta essa chave para um arquivo .pem
export_keyPair(private_key, name_keyPair_NV)
print("A .pem file with the key created, name: " + name_keyPair_NV + ".pem")
logging.info("A .pem file with the key created, name: " + name_keyPair_NV + ".pem")
print(" ")

# deleta a instancia antes de criar um novo ou apagar o security group
delete_instance(client_NV, instance_nameNV)

# Criação do grupo de segurança e obtenção do seu id
create_securityGroup(client_NV, id_vpc_NV, permissoes_NV, group_name_NV, desc)
print("Security group for the instance " + instance_nameNV + " created, name: " + group_name_NV)
logging.info("Security group for the instance " + instance_nameNV + " created, name: " + group_name_NV)
print(" ")

response = client_NV.describe_security_groups()

for e in response["SecurityGroups"]:
    if e['GroupName'] == group_name_NV:
        id_SecurityGroup = e['GroupId']


ohio_ip = client.describe_instances(InstanceIds=[id_instancia])['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']

# script de criação do django
USER_DATA_DJANGO = '''#!/bin/bash
cd /
sudo apt update
git clone https://github.com/anaclaracf/tasks
cd tasks/portfolio
sudo sed -i s/"'HOST': 'node1',"/"'HOST': '{0}',"/g  /tasks/portfolio/settings.py
sudo sed -i s/"'PASSWORD': 'cloud',"/"'PASSWORD': '',"/g  /tasks/portfolio/settings.py
cd /
cd tasks
./install.sh
sudo ufw allow 8080/tcp
./run.sh
'''.format(ohio_ip)

# criação da instâncias com os atributos anteriores
instancia, id_instancia = run_instance(client_NV, image_NV, USER_DATA_DJANGO, name_keyPair_NV, group_name_NV, instance_type)
client_NV.create_tags(Resources=[id_instancia], Tags=[{'Key':'Name', 'Value':instance_nameNV}])


print("Django instance in North Virginia created!")
logging.info("Django instance in North Virginia created!")
print("--------------------------------------------------")
print(" ")

print("Waiting for the Django instance to be running...")
logging.info("Waiting for the Django instance to be running...")
print(" ")
# espera a instância rodar para poder criar a imagem
waiter = client_NV.get_waiter('instance_running')
waiter.wait(
    InstanceIds=[
        id_instancia,
    ],
)
print("Django instance ready!")
logging.info("Django instance ready!")
print(" ")

print("Creating an AMI image")
logging.info("Creating an AMI image")
# cria a imagem AMI
image_AMI, image_id = create_image(client_NV, id_instancia, image_name)

logging.info("Waiting for the AMI image to be ready...")
logging.info("AMI image ready!")

print("Deleting the instance " + instance_nameNV)
logging.info("Deleting the instance " + instance_nameNV)
print(" ")
# apaga a instancia
delete_instance(client_NV, instance_nameNV)

print("Django instance deleted")
logging.info("Django instance deleted")

# -------------------------------------------------------------------

# lista todas as subnets para a criaçao do load balancer
list_subnets = all_subnets(client_NV)


# cria o load balancer
elb_client, response, lbId = create_loadBalancer(local_NV, lb_name, list_subnets, id_SecurityGroup)

print("Load Balancer created, name: " + lb_name)
logging.info("Load Balancer created, name: " + lb_name)
print(" ")


# cria um target group
create_tg_response, tgId = create_tg(elb_client, targetGroupName, id_vpc_NV)

print("Target Group created, name: " + targetGroupName)
logging.info("Target Group created, name: " + targetGroupName)
print(" ")

create_listener_response = elb_client.create_listener(LoadBalancerArn=lbId,
                                                      Protocol='HTTP', 
                                                      Port=80,
                                                      DefaultActions=[{'Type': 'forward',
                                                                       'TargetGroupArn': tgId}]
                                                      )

print("Listener created")
logging.info("Listener created")
print(" ")

autoscaling_client = create_autoscaling(local_NV, launch_name, image_id, id_SecurityGroup, USER_DATA_DJANGO, autoScaling_name, tgId, as_instance_name)

print("Auto Scaling group created, name: " + autoScaling_name)
logging.info("Auto Scaling group created, name: " + autoScaling_name)
print(" ")

resource_label = 'a' + lbId.split('/a')[1] + '/t' + tgId.split(':t')[1]

autoscaling_client.put_scaling_policy(
    AutoScalingGroupName=autoScaling_name,
    PolicyName= policy_name,
    PolicyType='TargetTrackingScaling',
    TargetTrackingConfiguration={
        'PredefinedMetricSpecification': {
            'PredefinedMetricType': 'ALBRequestCountPerTarget',
            'ResourceLabel': resource_label,
        },
        'TargetValue': 50.0,
    },
)

print("Policy created, name: " + policy_name + " for the Auto Scaling group " + autoScaling_name)
logging.info("Policy created, name: " + policy_name + " for the Auto Scaling group " + autoScaling_name)
print(" ")


print("-------------------------")
print("End of the program")
logging.info("End of the program")
print("-------------------------")
#!/usr/bin/python
# -*- coding: utf-8 -*-

import boto3
import os
from dotenv import load_dotenv

load_dotenv()

accessKey = os.getenv("accessKey")
secretAccessKey = os.getenv("secretAccessKey")

# Criar uma instância
def create_instance(local):
    try:
        client = boto3.client('ec2', 
                            region_name = local, 
                            aws_access_key_id = accessKey, 
                            aws_secret_access_key = secretAccessKey
                            )
        return client

    except Exception as e:
        print(e)

# Para criar uma chave
def create_keyPair(client, name_keyPair):

    key_ohio_response = client.describe_key_pairs(
        Filters=[
            {'Name': 'key-name', 'Values': [name_keyPair]}
        ]
    )

    if key_ohio_response['KeyPairs']:
        client.delete_key_pair(KeyName=name_keyPair)
    
    keyPair_instance = client.create_key_pair(KeyName = name_keyPair)
    private_key = keyPair_instance["KeyMaterial"]
    return keyPair_instance, private_key
    
# Para exportar uma chave para um arquivo .pem
def export_keyPair(private_key, name_keyPair):
    try:
        if os.path.exists(name_keyPair):
            os.remove(name_keyPair)

        with os.fdopen(os.open(name_keyPair+".pem", os.O_WRONLY | os.O_CREAT, 0o777), "w+") as handle:
            handle.write(private_key)

    except Exception as e:
        print(e)


# Para criar um security group
def create_securityGroup(client, id_vpc, permissoes, group_name, desc):
    
    try:

        response = client.describe_security_groups(
            Filters=[
                {'Name': 'group-name', 'Values': [group_name]}
            ]
        )

        if response['SecurityGroups']:
            security_id = response['SecurityGroups'][0]['GroupId']
            client.delete_security_group(GroupId=security_id)

        security_group = client.create_security_group(
            GroupName= group_name,
            Description = desc,
            VpcId= id_vpc
        )
        
        client.authorize_security_group_ingress(
        GroupId=security_group['GroupId'],
        IpPermissions= permissoes
        )
        
        return security_group['GroupId']

    except Exception as e:
        print(e)
    
# Para criar uma instância
def run_instance(client, image, USER_DATA, name_keyPair, group_name, instance_type):
    try:
        instance = client.run_instances(
            ImageId=image,
            MinCount=1,
            MaxCount=1,
            InstanceType= instance_type,
            KeyName = name_keyPair,
            UserData = USER_DATA,
            SecurityGroups = [group_name]
        )
        id_instancia = instance["Instances"][0]["InstanceId"]
        return instance, id_instancia

    except Exception as e:
        print(e)

# Para parar uma instância
def stop_instance(instance, id_instancia):
    try:
        instance.stop_instances(InstanceIds=[id_instancia])
    
    except Exception as e:
        print(e)

# Para começar uma instância
def start_instance(instance, id_instancia):
    try:
        instance.start_instances(InstanceIds=[id_instancia])

    except Exception as e:
        print(e)

# Para criar uma imagem
def create_image(instance, id_instancia, name):
    try:

        response = instance.describe_images(
                        Owners=['self'],
                        Filters=[{
                                'Name': 'name',
                                'Values': [name]},],
                    )

        ec2 = boto3.resource('ec2', region_name='us-east-1', aws_access_key_id = accessKey, 
                            aws_secret_access_key = secretAccessKey)

        if response['Images']:
            id_image = response['Images'][0]['ImageId']
            ami = list(ec2.images.filter(ImageIds=[id_image]).all())[0]
            ami.deregister()

        image_AMI = instance.create_image(
            InstanceId=id_instancia, 
            Name=name
        )

        infos_image = instance.describe_images(Owners=['self'])

        for e in infos_image["Images"]:
            if e['Name'] == name:
                image_id = e["ImageId"]

        image = ec2.Image(image_id)
        if(image.state == 'pending'):
            print("Waiting the image to be ready...")
            print(" ")
            while(image.state != 'available'):
                image = ec2.Image(image_id)
            print("Image created, name: " + name)
            print(" ")

        return image_AMI, image_id

    except Exception as e:
        print(e)

# Para criar um load balancer
def create_loadBalancer(local, name, subnets, securityId):
    try:

        elb_client = boto3.client(service_name="elbv2", 
                            aws_access_key_id = accessKey, 
                            aws_secret_access_key = secretAccessKey, 
                            region_name=local
                            )


        load_balancers = elb_client.describe_load_balancers()

        for i in load_balancers['LoadBalancers']:
            if i['LoadBalancerName'] == name:
                lbId = i['LoadBalancerArn']

                listeners = elb_client.describe_listeners(LoadBalancerArn=lbId)

                if listeners['Listeners']:
                    listener_arn = listeners['Listeners'][0]['ListenerArn']
                    elb_client.delete_listener(ListenerArn=listener_arn)

                elb_client.delete_load_balancer(LoadBalancerArn=lbId)

        
        response = elb_client.create_load_balancer(Name=name,
                                        Subnets = subnets,
                                        SecurityGroups=[securityId],
                                        Scheme='internet-facing')

        for e in response["LoadBalancers"]:
            if e['LoadBalancerName'] == name:
                lbId = e['LoadBalancerArn']

                            
        return elb_client, response, lbId

    except Exception as e:
        print(e)

# Para pegar todas as subnets
def all_subnets(instance):
    try:
        sn_all = instance.describe_subnets()
        list_subnets = []
        for sn in sn_all['Subnets']:
            list_subnets.append(sn['SubnetId'])
            
        return list_subnets

    except Exception as e:
        print(e)

# Para criar os Target Groups
def create_tg(elb_client, targetGroupName, id_vpc):

    try:    
        # exists = elb_client.describe_target_groups()

        # if exists['TargetGroups'][0]['TargetGroupName'] == targetGroupName:
        #     tg_arn = exists['TargetGroups'][0]['TargetGroupArn']
        #     elb_client.delete_target_group(TargetGroupArn = tg_arn)

        create_tg_response = elb_client.create_target_group(Name=targetGroupName,
                                                        Protocol='HTTP',
                                                        Port=8080,
                                                        VpcId=id_vpc)

        for e in create_tg_response["TargetGroups"]:
            if e['TargetGroupName'] == targetGroupName:
                tgId = e['TargetGroupArn']

        return create_tg_response, tgId

    except Exception as e:
        print(e)

# Criar auto scalling grouo + launch group
def create_autoscaling(local, launch_name, image_id, id_SecurityGroup, user_data, autoScaling_name, tgId, as_instance_name):
    
    try:
        autoscaling_client = boto3.client(service_name="autoscaling", 
                            aws_access_key_id = accessKey, 
                            aws_secret_access_key = secretAccessKey, 
                            region_name=local
                            )

        
        autoscaling_client.create_launch_configuration(
                LaunchConfigurationName=launch_name,
                ImageId=image_id,
                SecurityGroups=[id_SecurityGroup],
                InstanceType='t2.micro', 
                UserData = user_data
        )
        
        auto_scaling = autoscaling_client.create_auto_scaling_group(
                AutoScalingGroupName = autoScaling_name,
                LaunchConfigurationName = launch_name,
                MaxInstanceLifetime=2592000,
                MaxSize=3,
                MinSize=1,
                VPCZoneIdentifier='subnet-d43987fa',
                TargetGroupARNs=[tgId],
                Tags = [{
                            "Key": "Name",
                            "Value": as_instance_name,
                            "PropagateAtLaunch": True
                        }
                ]
        )
        
        return autoscaling_client

    except Exception as e:
        print(e)
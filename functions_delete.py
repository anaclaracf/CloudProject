import boto3
import os
from dotenv import load_dotenv

load_dotenv()

accessKey = os.getenv("accessKey")
secretAccessKey = os.getenv("secretAccessKey")

def delete_launch(local, launch_name):
    try:

        autoscaling_client = boto3.client(service_name="autoscaling", 
                                aws_access_key_id = accessKey, 
                                aws_secret_access_key = secretAccessKey, 
                                region_name=local
                                )

        lc = autoscaling_client.describe_launch_configurations(
            LaunchConfigurationNames=[
                launch_name,
            ],
        )

        if lc['LaunchConfigurations'][0]['LaunchConfigurationName'] == launch_name:

            autoscaling_client.delete_launch_configuration(
                LaunchConfigurationName=launch_name
            )

            print("Deleting the old launch configuration")

    except Exception as e:
        print("There is no launch group to be deleted")

# Deleta auto scaling group e suas instancias
def delete_asg_instances(local, autoScaling_name):
    try:
        autoscaling_client = boto3.client(service_name="autoscaling", 
                                aws_access_key_id = accessKey, 
                                aws_secret_access_key = secretAccessKey, 
                                region_name=local
                                )

        resp = autoscaling_client.describe_auto_scaling_instances()
        asg = autoscaling_client.describe_auto_scaling_groups(
                    AutoScalingGroupNames=[
                        autoScaling_name,
                    ],
                )

        # print(asg)

        if asg['AutoScalingGroups']:
            if asg['AutoScalingGroups'][0]['AutoScalingGroupName'] == autoScaling_name:
                autoscaling_client.update_auto_scaling_group(
                        AutoScalingGroupName = autoScaling_name,
                        MinSize=0,
                        DesiredCapacity=0,
                )
        

        for e in resp['AutoScalingInstances']:
            id_asi = e['InstanceId']
            autoscaling_client.terminate_instance_in_auto_scaling_group(
                InstanceId = id_asi,
                ShouldDecrementDesiredCapacity= False
            )

        for e in asg['AutoScalingGroups']:
            if asg['AutoScalingGroups'][0]['AutoScalingGroupName'] == autoScaling_name:

                autoscaling_client.delete_auto_scaling_group(
                    AutoScalingGroupName=autoScaling_name,
                    ForceDelete=True
                )

                print('Deleting the old Autoscaling Group')

    except Exception as e:
        print("There is no auto scaling group to be deleted")

# deleta o target group
def delete_targetgroup(local, targetGroupName):

    try:
        elb_client = boto3.client(service_name="elbv2", 
                                aws_access_key_id = accessKey, 
                                aws_secret_access_key = secretAccessKey, 
                                region_name=local
                                )

        tg = elb_client.describe_target_groups(
                Names=[
                    targetGroupName,
                ],
            )
            
        if tg['TargetGroups'][0]['TargetGroupName'] == targetGroupName:
            tg_arn = tg['TargetGroups'][0]['TargetGroupArn']
            elb_client.delete_target_group(TargetGroupArn = tg_arn)
            print("Deleting the old Target Group")

    except Exception as e:
            print("There is no Target Group to be deleted")

# deleta o load balancer e listeners
def delete_loadbalancer_listener(local, name):
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
                print("Deleting the old Load Balancer and Listener")
            
    except Exception as e:
        print("There is no Load Balancer and Listener to be deleted")

# Deleta uma instancia
def delete_instance(client, instance_name):
    waiter = client.get_waiter('instance_terminated')

    response = client.describe_instances(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    instance_name,
                ]
            },
            {
                'Name': 'instance-state-name',
                'Values': [
                    'running',
                ]
            },
        ],
    )

    if response['Reservations']:
        instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
        client.terminate_instances(InstanceIds=[instance_id])

        waiter.wait(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [
                        instance_name,
                    ]
                },
            ]
        )
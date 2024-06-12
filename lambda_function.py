import boto3
import time

def lambda_handler(event, context):
    # Initialize Boto3 clients
    ec2_client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')
    ses_client = boto3.client('ses')

    # Set parameters
    golden_ami_id = 'ami-0fd95cb73815b2ed0' 
    subnet_id = 'subnet-033693bd4f800986e'
    key_name = 'amphenolpoc'
    instance_type = 't2.micro'
    security_group_ids = ['sg-0b01b7050a07c5e4f']
    iam_instance_profile_arn = 'arn:aws:iam::867295767287:instance-profile/lambda-1'
    sender_email = 'rajesh.jangid@ranosys.com'
    recipient_email = 'rithik.narula@ranosys.com'
    username = "ec2-user"

    # Create EC2 instances using Golden AMI
    instance_ids = create_ec2_instances(ec2_resource, golden_ami_id, subnet_id, key_name, instance_type, security_group_ids, iam_instance_profile_arn) 
    if instance_ids:
        # Get instance private IPs
        while True:
            instance_ips = get_instance_private_ips(ec2_client,instance_ids)
            if instance_ips:
                # Get username and key name of the instance
                instance_info = get_instance_info(ec2_client, instance_ids[0])
                username = instance_info.get('username', 'Unknown')
                key_name = instance_info.get('key_name', 'Unknown')
                
                # Send email with instance IPs, username, and key name
                send_email(ses_client, sender_email, recipient_email, instance_ips, username, key_name)
                
                return {
                    'statusCode': 200,
                    'body': 'EC2 instances created successfully. Email sent with instance private IPs, username, and key name.'
                }
            time.sleep(10)  
    else:
        return {
            'statusCode': 400,
            'body': 'Failed to create EC2 instances.'
        }

def create_ec2_instances(ec2_resource, golden_ami_id, subnet_id, key_name, instance_type, security_group_ids, iam_instance_profile_arn):
    instance_ids = []
    create_instance = ec2_resource.create_instances(ImageId=golden_ami_id,
                                    MinCount=1,
                                    MaxCount=1,
                                    InstanceType=instance_type,
                                    KeyName=key_name,
                                    SecurityGroupIds=security_group_ids,
                                    SubnetId=subnet_id,
                                    IamInstanceProfile={'Arn': iam_instance_profile_arn}
                                )
    instance_id = create_instance[0].id
    instance_ids.append(instance_id)
    # Implement logic to create EC2 instances using the provided parameters
    return instance_ids

def get_instance_private_ips(ec2_client, instance_ids):
    # Retrieve private IPs of the instances
    instance_ips = []
    for instance_id in instance_ids:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        reservations = response.get('Reservations', [])
        for reservation in reservations:
            instances = reservation.get('Instances', [])
            for instance in instances:
                state = instance.get('State', {}).get('Name', 'Unknown')
                if state == "running":
                    private_ip = instance.get('PrivateIpAddress')
                    if private_ip:
                        instance_ips.append(private_ip)
    return instance_ips

def get_instance_info(ec2_client, instance_id):
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    reservations = response.get('Reservations', [])
    for reservation in reservations:
        instances = reservation.get('Instances', [])
        for instance in instances:
            username = instance.get('UserName', 'Unknown')
            key_name = instance.get('KeyName', 'Unknown')
            return {'username': username, 'key_name': key_name}

def send_email(ses_client, sender_email, recipient_email, instance_ips, username, key_name):
    # Compose email message
    subject = 'EC2 Instance IP Notification'
    body_text = f'EC2 instances have been launched.\n\nPrivate IP addresses: {", ".join(instance_ips)}\nUsername: {username}\nKey Name: {key_name}'

    # Send email
    response = ses_client.send_email(
        Source=sender_email,
        Destination={
            'ToAddresses': [recipient_email]
        },
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': body_text}}
        }
    )

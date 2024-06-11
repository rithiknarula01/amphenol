{\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang2057{\fonttbl{\f0\fnil\fcharset0 Calibri;}}
{\*\generator Riched20 10.0.19041}\viewkind4\uc1 
\pard\sa200\sl276\slmult1\f0\fs22\lang9 import boto3\par
import time\par
\par
def lambda_handler(event, context):\par
    # Initialize Boto3 clients\par
    ec2_client = boto3.client('ec2')\par
    ec2_resource = boto3.resource('ec2')\par
    ses_client = boto3.client('ses')\par
\par
    # Set parameters\par
    golden_ami_id = '\tab ami-080562ec47e8c508c' \par
    subnet_id = 'subnet-033693bd4f800986e'\par
    key_name = 'amphenolpoc'\par
    instance_type = 't2.micro'\par
    security_group_ids = ['sg-0b01b7050a07c5e4f']\par
    iam_instance_profile_arn = 'arn:aws:iam::867295767287:instance-profile/lambda-1'\par
    sender_email = 'rajesh.jangid@ranosys.com'\par
    recipient_email = 'rithik.narula@ranosys.com'\par
    username = "ec2-user"\par
\par
    # Create EC2 instances using Golden AMI\par
    instance_ids = create_ec2_instances(ec2_resource, golden_ami_id, subnet_id, key_name, instance_type, security_group_ids, iam_instance_profile_arn) \par
    if instance_ids:\par
        # Get instance private IPs\par
        while True:\par
            instance_ips = get_instance_private_ips(ec2_client,instance_ids)\par
            if instance_ips:\par
                # Get username and key name of the instance\par
                instance_info = get_instance_info(ec2_client, instance_ids[0])\par
                username = instance_info.get('username', 'Unknown')\par
                key_name = instance_info.get('key_name', 'Unknown')\par
                \par
                # Send email with instance IPs, username, and key name\par
                send_email(ses_client, sender_email, recipient_email, instance_ips, username, key_name)\par
                \par
                return \{\par
                    'statusCode': 200,\par
                    'body': 'EC2 instances created successfully. Email sent with instance private IPs, username, and key name.'\par
                \}\par
            time.sleep(10)  \par
    else:\par
        return \{\par
            'statusCode': 400,\par
            'body': 'Failed to create EC2 instances.'\par
        \}\par
\par
def create_ec2_instances(ec2_resource, golden_ami_id, subnet_id, key_name, instance_type, security_group_ids, iam_instance_profile_arn):\par
    instance_ids = []\par
    create_instance = ec2_resource.create_instances(ImageId=golden_ami_id,\par
                                    MinCount=1,\par
                                    MaxCount=1,\par
                                    InstanceType=instance_type,\par
                                    KeyName=key_name,\par
                                    SecurityGroupIds=security_group_ids,\par
                                    SubnetId=subnet_id,\par
                                    IamInstanceProfile=\{'Arn': iam_instance_profile_arn\}\par
                                )\par
    instance_id = create_instance[0].id\par
    instance_ids.append(instance_id)\par
    # Implement logic to create EC2 instances using the provided parameters\par
    return instance_ids\par
\par
def get_instance_private_ips(ec2_client, instance_ids):\par
    # Retrieve private IPs of the instances\par
    instance_ips = []\par
    for instance_id in instance_ids:\par
        response = ec2_client.describe_instances(InstanceIds=[instance_id])\par
        reservations = response.get('Reservations', [])\par
        for reservation in reservations:\par
            instances = reservation.get('Instances', [])\par
            for instance in instances:\par
                state = instance.get('State', \{\}).get('Name', 'Unknown')\par
                if state == "running":\par
                    private_ip = instance.get('PrivateIpAddress')\par
                    if private_ip:\par
                        instance_ips.append(private_ip)\par
    return instance_ips\par
\par
def get_instance_info(ec2_client, instance_id):\par
    response = ec2_client.describe_instances(InstanceIds=[instance_id])\par
    reservations = response.get('Reservations', [])\par
    for reservation in reservations:\par
        instances = reservation.get('Instances', [])\par
        for instance in instances:\par
            username = instance.get('UserName', 'Unknown')\par
            key_name = instance.get('KeyName', 'Unknown')\par
            return \{'username': username, 'key_name': key_name\}\par
\par
def send_email(ses_client, sender_email, recipient_email, instance_ips, username, key_name):\par
    # Compose email message\par
    subject = 'EC2 Instance IP Notification'\par
    body_text = f'EC2 instances have been launched.\\n\\nPrivate IP addresses: \{", ".join(instance_ips)\}\\nUsername: \{username\}\\nKey Name: \{key_name\}'\par
\par
    # Send email\par
    response = ses_client.send_email(\par
        Source=sender_email,\par
        Destination=\{\par
            'ToAddresses': [recipient_email]\par
        \},\par
        Message=\{\par
            'Subject': \{'Data': subject\},\par
            'Body': \{'Text': \{'Data': body_text\}\}\par
        \}\par
    )\par
}
 
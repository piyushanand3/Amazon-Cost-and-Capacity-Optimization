import csv
import boto3
from datetime import datetime, timedelta

# Create an EC2 client
ec2_client = boto3.client('ec2')

# Create a CloudWatch client
cloudwatch_client = boto3.client('cloudwatch')

# Retrieve a list of all EC2 instances
response = ec2_client.describe_instances()

# Prepare the list of instances
instances = []

# Iterate through the instances and store the details
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
        instance_type = instance['InstanceType']
        instance_state = instance['State']['Name']
        instance_launch_time = instance['LaunchTime']
        instance_name = next((tag['Value'] for tag in instance['Tags'] if tag['Key'] == 'Name'), 'N/A')
        private_ip = instance['PrivateIpAddress']
        public_ip = instance['PublicIpAddress'] if 'PublicIpAddress' in instance else 'N/A'

        instances.append([instance_id, instance_name, instance_type, instance_state, instance_launch_time, private_ip, public_ip])

# Specify the output CSV file path
output_file = 'ec2_instances.csv'

# Write the instances to the CSV file
with open(output_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Instance ID', 'Instance Name', 'Instance Type', 'Instance State', 'Launch Time', 'Private IP', 'Public IP'])
    writer.writerows(instances)

# Retrieve the CPU utilization metrics for the past 30 days for each instance
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=30)

# Prepare the list of underutilized instances
underutilized_instances = []

for instance in instances:
    instance_id = instance[0]

    response = cloudwatch_client.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': instance_id
            },
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=86400,  # One day period (24 hours x 60 minutes x 60 seconds)
        Statistics=['Average'],
    )

    # Calculate the average CPU utilization for the past 30 days
    cpu_utilization = sum(point['Average'] for point in response['Datapoints']) / len(response['Datapoints']) if response['Datapoints'] else 0

    if cpu_utilization < 10:  # Adjust the threshold as needed
        underutilized_instances.append(instance + [cpu_utilization])

# Specify the output CSV file path for underutilized instances
underutilized_output_file = 'underutilized_ec2_instances.csv'

# Write the underutilized instances to the CSV file
with open(underutilized_output_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Instance ID', 'Instance Name', 'Instance Type', 'Instance State', 'Launch Time', 'Private IP', 'Public IP', 'CPU Utilization'])
    writer.writerows(underutilized_instances)

print(f"EC2 instances exported to {output_file}")
print(f"Underutilized EC2 instances exported to {underutilized_output_file}")

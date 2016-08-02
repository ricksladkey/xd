#!/bin/bash -x

#source src/aws/config

XD_PROFILE="arn:aws:iam::165509303398:instance-profile/xd-scraper"

echo aws s3 cp src/aws/config s3://xd-private/etc/config

ami_id=ami-75fd3b15 #Ubuntu Server 16.04 LTS (HVM)
ssh_security_gid=sg-e00fbe87
INSTANCE_JSON=/tmp/instance.json

#  created via IAM console: role/xd-scraper
aws ec2 run-instances \
      --key-name $KEY \
      --region ${REGION} \
      --instance-type r3.large \
      --instance-initiated-shutdown-behavior terminate \
      --iam-instance-profile Arn="$XD_PROFILE" \
      --user-data file://scripts/00-aws-bootstrap.sh \
      --image-id $ami_id > $INSTANCE_JSON

instance_id=$(cat $INSTANCE_JSON | grep instance_id)
echo aws ec2 modify-instance-attribute --groups $ssh_security_gid --instance-id $instance_id

public_ip=$(aws ec2 describe-instances | grep PublicIp)
echo ssh -i ~/*.pem ubuntu@$public_ip

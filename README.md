# Custom Cloudformation Resources for Aviatrix

## 1. Deploy the execution environment

Start by deploying the execution environment from [template.yml](https://github.com/nickda/aviatrix-cfn-types/blob/main/template.yml) to Cloudformation.
>Important: Ensure you select the correct region in the AWS Console or AWS CLI.

## 2. Install the prerequisites to generate Cloudformation Resources from Aviatrix Terraform provider resources

- Python 3
- Git
- Docker
- Terraform 0.15+
- CloudFormation CLI with Python Provider

Example of installation on Amazon Linux instance:

```sh
## Update AWS CLI to the latest version
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

## Configure AWS credentials and region to which the Cloudformation resources will be registered
aws configure

## Install the prerequisites
sudo yum update
sudo yum install python3
sudo yum install git
sudo yum install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo yum install unzip
sudo yum -y install terraform
sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
sudo yum -y install terraform
sudo yum install python3-pip
pip3 install virtualenv

## Create the virtual environment and install and Cloudformation CLI and Python plugin into it
virtualenv venv
source venv/bin/activate
pip3 install cloudformation-cli
cfn --version
pip3 install cloudformation-cli cloudformation-cli-python-plugin
```

## 3. Pull and Run the Lambda Python Image in Docker

docker pull public.ecr.aws/lambda/python:3.9
docker run -d -p 9000:8080 public.ecr.aws/lambda/python:3.9 app

## 4. Generate the Aviatrix resources and provider documenation
To generate resources based on the latest version of Terraform provider:

```sh
python3 generate.py
```

## 5. Submit the resources to Cloudformation

> Note: By default AWS imposes a limit of 50 custom resources per account per region. To submit resources one at a time:

```sh
python3 submit <resource-name>
```

e.g.,

```sh
python3 submit TF::Aviatrix::Account
```

To submit resources in bulk:

```sh
python3 submit-all.py
```

>Note: To only submit resources that you require, you can delete the folder with unneeded resources from the `resources` directory.

## 6. Configuring Aviatrix Controller IP address and credentials

To configure this resource, you must create an AWS Secrets Manager secret with the name `aviatrix_secret`.

The following arguments must be included as the key/value or JSON properties in the secret:

| Argument | Description |
| --- | --- |
| `controller_ip` | The IP address of the Aviatrix controller |
| `password` | The password of the `admin` user |

## 7. Deploy resources by Creating a Cloudformation template

You can find an example of Controller configuration and network infrastructure deployment template in the cfn_template_examples directory.

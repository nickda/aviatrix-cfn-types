<!-- TOC start (generated with https://github.com/derlin/bitdowntoc) -->

- [Custom Cloudformation Resource types for Aviatrix](#custom-cloudformation-resource-types-for-aviatrix)
   * [1. Deploy the execution environment](#1-deploy-the-execution-environment)
   * [2. Install the prerequisites](#2-install-the-prerequisites)
   * [3. Pull and Run the Lambda Python Image in Docker](#3-pull-and-run-the-lambda-python-image-in-docker)
   * [4. Generate the Aviatrix resources and provider documentation](#4-generate-the-aviatrix-resources-and-provider-documentation)
   * [5. Submit the resources to Cloudformation](#5-submit-the-resources-to-cloudformation)
   * [6. Configuring Aviatrix Controller IP address and credentials](#6-configuring-aviatrix-controller-ip-address-and-credentials)
   * [7. Deploy resources by Creating a Cloudformation template](#7-deploy-resources-by-creating-a-cloudformation-template)

<!-- TOC end -->

<!-- TOC --><a name="custom-cloudformation-resource-types-for-aviatrix"></a>
# Custom Cloudformation Resource types for Aviatrix

<!-- TOC --><a name="1-deploy-the-execution-environment"></a>
## 1. Deploy the execution environment

Start by deploying the execution environment from [template.yml](https://github.com/nickda/aviatrix-cfn-types/blob/main/template.yml) to Cloudformation.
>Important: Ensure you select the correct region in the AWS Console or AWS CLI.

<!-- TOC --><a name="2-install-the-prerequisites"></a>
## 2. Install the prerequisites

The following prerequisites are required to generate Cloudformation resource types from Aviatrix Terraform provider:

- Python 3
- Git
- Docker
- Terraform 1.0+
- CloudFormation CLI with Python Plugin

Example of installation on Amazon Linux instance:

```sh
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

## Update AWS CLI to the latest version
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

## Configure AWS credentials and region to which the Cloudformation resources will be registered
aws configure
```

<!-- TOC --><a name="3-pull-and-run-the-lambda-python-image-in-docker"></a>
## 3. Pull and Run the Lambda Python Image in Docker

docker pull public.ecr.aws/lambda/python:3.9
docker run -d -p 9000:8080 public.ecr.aws/lambda/python:3.9 app

<!-- TOC --><a name="4-generate-the-aviatrix-resources-and-provider-documentation"></a>
## 4. Generate the Aviatrix resources and provider documentation

To generate resources based on the latest version of Terraform provider:

```sh
python3 generate.py
```

<!-- TOC --><a name="5-submit-the-resources-to-cloudformation"></a>
## 5. Submit the resources to Cloudformation

> Note: By default, AWS imposes a limit of 50 custom resources per account per region.

To submit resources one at a time:

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

>Note: To submit only a subset of resources, you can delete the folder with unneeded resources from the `resources` directory before running the submit-all.py script.

<!-- TOC --><a name="6-configuring-aviatrix-controller-ip-address-and-credentials"></a>
## 6. Configuring Aviatrix Controller IP address and credentials

To configure this resource, you must create an AWS Secrets Manager secret named `aviatrix_secret`.

The following arguments must be included as the key/value or JSON properties in the secret:

| Argument | Description |
| --- | --- |
| `controller_ip` | The IP address of the Aviatrix controller |
| `password` | The password of the `admin` user |

<!-- TOC --><a name="7-deploy-resources-by-creating-a-cloudformation-template"></a>
## 7. Deploy resources by Creating a Cloudformation template

You can find an example of Controller configuration and network infrastructure deployment template in the [cfn_template_examples](https://github.com/nickda/aviatrix-cfn-types/tree/main/cfn_template_examples) directory.

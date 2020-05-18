## Application Tracing on Kubernetes with AWS X-Ray

## Attach the AWSXRayDaemonWriteAccess to EKS worker node Role
```bash
aws iam attach-role-policy --role-name $ROLE_NAME \
--policy-arn arn:aws-cn:iam::aws:policy/AWSXRayDaemonWriteAccess --region ${AWS_REGION}
```

## Deploy X-Ray DaemonSet
```bash
git clone https://github.com/aws-samples/aws-xray-kubernetes.git
cd aws-xray-kubernetes/xray-daemon
## Modify the image location to China repository
kubectl apply -f xray-k8s-daemonset.yaml
kubectl describe daemonset xray-daemon
kubectl get pods -l app=xray-daemon
kubectl logs -l app=xray-daemon
```

By default, the X-Ray SDK expects the daemon to be available on 127.0.0.1:2000 and hosted within its own Pod as sider car

[Sample document](https://aws.amazon.com/blogs/compute/application-tracing-on-kubernetes-with-aws-x-ray/) guild you to Build the X-Ray daemon Docker image and deploy it.

## Deploy sample application
1. Connecting to the X-Ray daemon

The deployed X-Ray DaemonSet exposes all Pods via the Kubernetes service discovery, so applications can use this endpoint to discover the X-Ray daemon. If you deployed to the default namespace, the endpoint is: `xray-service.default`

Applications now need to set the daemon address either with the `AWS_XRAY_DAEMON_ADDRESS` environment variable (**preferred**) or directly within the SDK setup code: `AWSXRay.setDaemonAddress('xray-service.default:2000');`

To set up the environment variable, include the following information in your Kubernetes application deployment description YAML. 
```yaml
env:
- name: AWS_XRAY_DAEMON_ADDRESS 
  value: xray-service.default
```

2. Deploy sample pods

```bash
# Build docker image for service-a and service-b
aws ecr get-login --region cn-northwest-1

cd aws-xray-kubernetes/demo-app/service-a
docker build -t aws-xray-kubernetes-service-a .
aws ecr create-repository --repository-name xray-k8s-service-a --region cn-northwest-1
docker tag aws-xray-kubernetes-service-a <your-account-id>.dkr.ecr.cn-northwest-1.amazonaws.com.cn/xray-k8s-service-a
docker push <your-account-id>.dkr.ecr.cn-northwest-1.amazonaws.com.cn/xray-k8s-service-a

cd aws-xray-kubernetes/demo-app/service-b
docker build -t aws-xray-kubernetes-service-b .
aws ecr create-repository --repository-name xray-k8s-service-b --region cn-northwest-1
docker tag aws-xray-kubernetes-service-a <your-account-id>.dkr.ecr.cn-northwest-1.amazonaws.com.cn/xray-k8s-service-b
docker push <your-account-id>.dkr.ecr.cn-northwest-1.amazonaws.com.cn/xray-k8s-service-b

# modify the aws-xray-kubernetes/demo-app/k8s-deploy.yaml to point to the ECR image
cd aws-xray-kubernetes/demo-app/
kubectl apply -f k8s-deploy.yaml
```

More example
```bash
# modify the aws-xray-kubernetes/demo-app/k8s-deploy.yaml to point to the ECR image
wget https://eksworkshop.com/intermediate/245_x-ray/sample-front.files/x-ray-sample-front-k8s.yml
kubectl apply -f x-ray-sample-front-k8s.yml
kubectl get pods -l app=x-ray-sample-front-k8s

wget https://eksworkshop.com/intermediate/245_x-ray/sample-back.files/x-ray-sample-back-k8s.yml
kubectl apply -f x-ray-sample-back-k8s.yml
kubectl get pods -l app=x-ray-sample-back-k8s

kubectl describe deployments x-ray-sample-front-k8s x-ray-sample-back-k8s
kubectl describe services x-ray-sample-front-k8s x-ray-sample-back-k8s
kubectl get service x-ray-sample-front-k8s -o wide

kubectl logs -l app=x-ray-sample-front-k8s
kubectl logs -l app=x-ray-sample-back-k8s
```



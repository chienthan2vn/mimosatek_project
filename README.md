# Hệ thống Tưới Tự Động Thông Minh

Hệ thống tưới tự động dựa trên AI với vòng lặp phản hồi kép, kết hợp phân tích định lượng và định tính.

## Đặc điểm

- **Vòng lặp Phản hồi Kép**: Học từ cả dữ liệu số và nhận xét ngôn ngữ tự nhiên
- **Trí nhớ Toàn diện**: Lưu trữ lịch sử hoàn chỉnh dưới dạng JSON
- **2 Giai đoạn**: Hiệu chỉnh và Vận hành riêng biệt
- **AI Agents**: Plan Agent và Reflection Agent
- **Web UI**: Giao diện web với Gradio
- **Cloud Native**: Deploy trên AWS EKS với Helm

## Kiến trúc Deployment

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Terraform     │    │      Helm       │    │     CI/CD       │
│                 │    │                 │    │                 │
│ • AWS VPC       │    │ • Kubernetes    │    │ • GitHub Actions│
│ • EKS Cluster   │    │ • Deployments   │    │ • Build & Push  │
│ • RDS Database  │    │ • Services      │    │ • Auto Deploy   │
│ • Security      │    │ • Ingress       │    │ • Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Cài đặt & Cấu hình

### 1. Cài đặt Local (Development)

```bash
# Clone repository
git clone <repository-url>
cd mimosatek_project

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình environment
cp .env.example .env
# Chỉnh sửa .env với API keys của bạn

# Chạy ứng dụng
python gradio_app.py
```

### 2. Deploy Infrastructure với Terraform

```bash
cd terraform

# Copy và cấu hình variables
cp terraform.tfvars.example terraform.tfvars
# Chỉnh sửa terraform.tfvars với thông tin của bạn

# Khởi tạo Terraform
terraform init

# Xem plan
terraform plan

# Apply infrastructure
terraform apply
```

**Cấu hình cần thiết trong `terraform.tfvars`:**
```hcl
# Project Configuration
project_name = "your-project-name"
environment  = "dev"  # dev, staging, production

# AWS Configuration  
aws_region                = "ap-southeast-1"
terraform_state_bucket   = "your-terraform-state-bucket"

# Database Configuration
db_password = "your-secure-password"
```

### 3. Deploy Application với Helm

```bash
cd helm

# Copy và cấu hình values
cp values.yaml values-dev.yaml
# Chỉnh sửa values-dev.yaml với cấu hình của bạn

# Update kubeconfig
aws eks update-kubeconfig --region ap-southeast-1 --name your-cluster-name

# Deploy với Helm
helm install mimosatek ./mimosatek \
  --namespace mimosatek-dev \
  --create-namespace \
  --values values-dev.yaml
```

**Cấu hình cần thiết trong `values-dev.yaml`:**
```yaml
# Image configuration
image:
  repository: your-account.dkr.ecr.region.amazonaws.com/mimosatek
  tag: "latest"

# Ingress configuration
ingress:
  hosts:
    - host: your-domain.com

# Database configuration
database:
  host: "your-rds-endpoint"
  password: "your-db-password"
```

### 4. Setup CI/CD Pipeline

1. **GitHub Secrets** cần cấu hình:
   ```
   AWS_ACCESS_KEY_ID
   AWS_SECRET_ACCESS_KEY
   ```

2. **GitHub Variables** cần cấu hình:
   ```
   AWS_REGION=ap-southeast-1
   EKS_CLUSTER_NAME=your-cluster-name
   ECR_REPOSITORY=your-ecr-repo
   ```

3. **Trigger deployment:**
   ```bash
   git push origin main  # Auto deploy to production
   git push origin develop  # Auto deploy to staging
   ```

## Template Files

### 📁 Cấu trúc thư mục:
```
mimosatek_project/
├── terraform/                 # AWS Infrastructure
│   ├── main.tf
│   ├── variables.tf
│   ├── terraform.tfvars.example
│   └── ...
├── helm/                     # Kubernetes Deployment
│   └── mimosatek/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── cicd/                     # CI/CD Pipelines
│   └── .github/workflows/
└── ...
```

### 🔧 Cấu hình Templates:

1. **Terraform Variables**: Sao chép `terraform.tfvars.example` → `terraform.tfvars`
2. **Helm Values**: Sao chép `values.yaml` → `values-{env}.yaml`
3. **Environment**: Sao chép `.env.example` → `.env`

## Monitoring & Logging

Hệ thống tích hợp:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboard  
- **ELK Stack**: Centralized logging
- **AWS CloudWatch**: Infrastructure monitoring

## Bảo mật

- **IAM Roles**: Least privilege access
- **Security Groups**: Network isolation
- **Secrets Management**: AWS Secrets Manager
- **TLS/SSL**: End-to-end encryption
- **Pod Security**: Non-root containers

## Troubleshooting

### Common Issues:

1. **Terraform State Lock**:
   ```bash
   terraform force-unlock <lock-id>
   ```

2. **Helm Deployment Failed**:
   ```bash
   helm status mimosatek -n mimosatek-dev
   kubectl logs -n mimosatek-dev -l app.kubernetes.io/name=mimosatek
   ```

3. **Database Connection**:
   ```bash
   kubectl exec -it <pod-name> -n mimosatek-dev -- env | grep DATABASE
   ```

## Scaling

- **Horizontal Pod Autoscaler**: Tự động scale pods
- **Cluster Autoscaler**: Tự động scale nodes
- **Database**: RDS auto-scaling storage

## Mục tiêu

Điều chỉnh thời gian chờ để đạt EC = 4.0 một cách tối ưu với khả năng scale cao trên cloud.

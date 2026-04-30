# DevOps Final Project — CI/CD Pipeline Plan

## Scenario

AUPP Student Management System. Every new feature must go through fast delivery, secure code scanning, automated deployment, and real-time monitoring.

---

## Pipeline Flow

```
Developer → GitHub → Code Review → Merge (resolve conflict) → CI Pipeline
→ SonarQube Scan → Trivy Security Scan → Build Docker Image
→ Terraform Create EC2 → Deploy Docker Container
→ Access from Laptop → Monitor via Prometheus + Grafana
```

---

## 1. Source Control & Collaboration (GitHub)

**Branch strategy:**

- `main` — protected branch, requires 1 reviewer approval before merge
- `feature/*` — developer branches for new features

**Steps:**

1. Developer creates a feature branch: `git checkout -b feature/student-gpa-status`
2. Developer pushes code and opens a Pull Request
3. At least 1 reviewer is assigned and must approve before merge
4. If two developers edit the same file → merge conflict → resolve manually → re-review → merge

**Branch Protection Rules:**

- Require pull request reviews before merging (min 1 reviewer)
- Require status checks to pass (CI pipeline)
- No direct pushes to `main`

---

## 2. CI Pipeline (Jenkins)

**Trigger:** Push to `main` branch

### Pipeline Stages

| # | Stage               | Description                                              |
| - | ------------------- | -------------------------------------------------------- |
| 1 | Checkout            | Clone repo from GitHub                                   |
| 2 | SonarQube Scan      | Analyze Python code quality                              |
| 3 | Quality Gate        | Abort pipeline if SonarQube gate fails                   |
| 4 | Build Docker Image  | Build `chanhengmenh/devops-final-project:latest`       |
| 5 | Trivy Security Scan | Scan image — abort if CRITICAL CVEs found               |
| 6 | Push Image          | Push to Docker Hub                                       |
| 7 | Provision EC2       | Terraform creates EC2 instance                           |
| 8 | Deploy App          | SSH to EC2, pull and run container on port 8000          |
| 9 | Deploy Monitoring   | Copy monitoring stack to EC2, start Prometheus + Grafana |

### Fail Conditions

- SonarQube Quality Gate **fails** → pipeline stops at Stage 3
- Trivy finds **CRITICAL** vulnerability → pipeline stops at Stage 5

---

## 2.1 Code Quality — SonarQube

- Tool: SonarQube (self-hosted, running on Jenkins server)
- Config file: `sonar-project.properties`
- Scans: `app/` directory (Python source)
- Pipeline fails if quality gate is not passed

---

## 2.2 Security Scan — Trivy

- Tool: Trivy
- Scans: built Docker image for vulnerabilities
- Also catches: dependency vulnerabilities in `requirements.txt`
- Pipeline **stops** on any CRITICAL severity finding

---

## 2.3 Build & Containerization

- Base image: `python:3.10-slim`
- App: FastAPI (Student Management API — student CRUD)
- Exposes: port 8000
- Image name: `chanhengmenh/devops-final-project:latest`
- Registry: Docker Hub

---

## 2.4 Infrastructure as Code — Terraform

- Provider: AWS (`ap-southeast-1`)
- Resource: EC2 `t2.micro` (Ubuntu)
- Security group opens ports: **22** (SSH), **8000** (App), **9090** (Prometheus), **3000** (Grafana), **9100** (Node Exporter)
- User data: installs Docker + Docker Compose plugin on boot

---

## 3. Continuous Deployment

After CI success:

1. SSH into EC2 using stored key pair
2. Pull latest Docker image from Docker Hub
3. Stop and remove old container
4. Run new container with `--restart always`

Application accessible at: `http://<EC2-PUBLIC-IP>:8000`

---

## 4. Monitoring & Observability

**Tools:** Prometheus + Grafana (deployed via Docker Compose on the EC2 instance)

### Components

| Service       | Port | Purpose                             |
| ------------- | ---- | ----------------------------------- |
| Prometheus    | 9090 | Metrics collection and storage      |
| Node Exporter | 9100 | EC2 system metrics (CPU, RAM, disk) |
| Grafana       | 3000 | Dashboard visualization             |

### Metrics collected

- **System:** CPU usage, memory, disk I/O, network (via Node Exporter)
- **Application:** HTTP request count, latency, in-flight requests (via `/metrics` endpoint)

### Access

- Prometheus: `http://<EC2-IP>:9090`
- Grafana: `http://<EC2-IP>:3000` → login `admin / admin`
  - Import dashboard **1860** (Node Exporter Full) for system metrics
  - Import dashboard **17175** (FastAPI Observability) for app metrics

---

## Repository Structure

```
devops-final-project/
├── Jenkinsfile                          # CI/CD pipeline definition
├── sonar-project.proper
ties             # SonarQube scanner config
├── app/
│   ├── main.py                          # FastAPI application
│   ├── requirements.txt                 # Python dependencies
│   └── Dockerfile                       # Container build instructions
├── terraform/
│   ├── main.tf                          # EC2 + security group
│   └── outputs.tf                       # Outputs EC2 public IP
└── monitoring/
    ├── docker-compose.yml               # Prometheus + Node Exporter + Grafana
    ├── prometheus.yml                   # Scrape configuration
    └── grafana/
        └── provisioning/
            ├── datasources/
            │   └── prometheus.yaml      # Auto-wires Prometheus datasource
            └── dashboards/
                └── dashboard.yaml       # Dashboard auto-loader
```

---

## Jenkins Prerequisites

| Requirement         | Setup                                                                         |
| ------------------- | ----------------------------------------------------------------------------- |
| SonarQube server    | Manage Jenkins → Configure System → SonarQube servers → Name:`SonarQube` |
| sonar-scanner       | Install on Jenkins agent                                                      |
| Trivy               | `sudo apt install trivy -y` on Jenkins agent                                |
| `dockerhub-creds` | Jenkins credential: Docker Hub username/password                              |
| `ec2-key`         | Jenkins credential: SSH private key (devops-key.pem)                          |
| `aws-credentials` | Jenkins credential: AWS Access Key ID + Secret                                |

---

## Screenshot Checklist

| # | Screenshot                           | Points |
| - | ------------------------------------ | ------ |
| a | GitHub Branches + Pull Request       |        |
| b | Reviewer Approve                     |        |
| c | Merge Conflict + Resolution          |        |
| d | Full Jenkinsfile script              |        |
| e | SonarQube report                     |        |
| f | Trivy scan result                    |        |
| g | Pipeline termination on quality fail |        |
| h | Terraform apply output               |        |
| i | Continuous Deployment stage          |        |
| j | Pipeline success (graphical view)    |        |
| k | App running from laptop browser      |        |
| l | Grafana dashboard                    |        |

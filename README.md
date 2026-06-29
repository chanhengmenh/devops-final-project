Scenario Overview

At American University of Phnom Penh (AUPP), the internal learning platform (similar to Canvas LMS) is actively developed.

Every time a new feature is added (e.g., grading improvements, UI updates, API integrations), the system must ensure:

Fast feature delivery
Secure code & infrastructure
Automated deployment
Real-time monitoring

You are part of the DevOps team responsible for designing a complete CI/CD pipeline to support this.

1. Developer pushes code → GitHub  
2. Pull Request created → Reviewer Approves
3. Resolve Merge Conflict and Merge to the main branch
4. CI pipeline runs
5. SonarQube checks code quality  
6. Trivy scans for vulnerabilities  
7. Docker image built  
8. Terraform provisions/ Create server (EC2)  
9. Docker Image deployed  
10. Access from Laptop
11. Prometheus collects metrics  
12. Grafana displays dashboard  

PROJECT FLOW:

Developer → GitHub → Code Review → Merge in the main branch after resolve Merge Conflict → CI Pipeline Runs → SonarQube Scan → Trivy Security Scan → Build Docker Image → Terraform Create EC2 → Deploy Docker Image → Access it from your laptop → Monitor via Prometheus or CloudWatch + Grafana

REQUIRED screenshots:
a) GitHub Branches and GitHub Pull Request
b) Reviewer Approve
c) Merge conflict and Resolved
d) Jenkins / GitHub action's full Script  
e) SonarQube report
f) Trivy scan result
g) For Quality Fail Pipeline termination 
h) Terraform 
i) Continues Deployment 
j) Pipeline success (Graphical)
k) Access your Running application from your laptop
l) Grafana dashboard

----------------------------------------------------------------------------------------------------------

1. Source Control & Collaboration (GitHub)

Required Practices: 
a) Assign at least 1 reviewer
b) Enforce branch protection rules
c) Resolve merge conflicts

At least 1 reviewer required before merge
Demonstrate merge conflict resolution

For Example: - Two developers modify the API module → conflict → manually resolve → re-review → merge

2. Continuous Integration (CI) 

Pipeline Tool: Jenkins OR GitHub Actions

Pipeline triggers: Push to main branch

a) Load Application from GitHub for Backend (APIs)
b) Code Quality Scan Using SonarQube

2.1. Security Integration 

Tool: Trivy

Scanning Includes:
Docker image vulnerabilities
Dependency vulnerabilities

Policy:
Pipeline should FAIL / Stop if:

SonarQube Quality Gate fails
Critical vulnerabilities found by Trivy

2.2. Build & Containerization

Build Docker image:

2.3. Infrastructure as Code (IaC)

Tool: Terraform

Create EC2 Instance and configure it as required.

3. Continuous Deployment (CD)

After CI success:

Deploy docker container to the EC2 through Pipeline

--------------------------------------------------------------------------

4. Monitoring & Observability

Tools: Prometheus or CloudWatch + Grafana

# DevOps Final Project — Step-by-Step Execution Guide

Follow this guide **in order**. Each section tells you exactly what to do, what to verify, and what can go wrong.

---

## Table of Contents

1. [Prerequisites & Local Tools](#1-prerequisites--local-tools)
2. [GitHub Repository Setup](#2-github-repository-setup)
3. [Branch Protection Rules](#3-branch-protection-rules)
4. [Feature Branch + Pull Request + Merge Conflict](#4-feature-branch--pull-request--merge-conflict)
5. [Jenkins Server Setup](#5-jenkins-server-setup)
6. [SonarQube Setup](#6-sonarqube-setup)
7. [Jenkins Credentials](#7-jenkins-credentials)
8. [Jenkins Pipeline Job](#8-jenkins-pipeline-job)
9. [Simulate Quality Gate Failure (Screenshot g)](#9-simulate-quality-gate-failure-screenshot-g)
10. [Trivy Verification](#10-trivy-verification)
11. [Full Pipeline Run — Success](#11-full-pipeline-run--success)
12. [Verify Deployment](#12-verify-deployment)
13. [Grafana Dashboards](#13-grafana-dashboards)
14. [Screenshot Checklist](#14-screenshot-checklist)
15. [Common Errors & Fixes](#15-common-errors--fixes)

---

## 1. Prerequisites & Local Tools

### What you need installed on your laptop

| Tool | Version check | Install if missing |
|------|---------------|-------------------|
| Git | `git --version` | https://git-scm.com |
| Docker Desktop | `docker version` | https://docker.com |
| AWS CLI | `aws --version` | https://aws.amazon.com/cli |
| Terraform | `terraform version` | https://developer.hashicorp.com/terraform/install |

### AWS account setup

1. Log in to AWS Console → IAM → Users → your user → Security credentials
2. Create an **Access Key** (type: "Application running outside AWS")
3. Save the **Access Key ID** and **Secret Access Key** — you will add these to Jenkins later
4. Your IAM user needs these permissions: `AmazonEC2FullAccess`

### Generate the EC2 key pair (do this once)

```bash
# In AWS Console → EC2 → Key Pairs → Create key pair
# Name: devops-key
# Type: RSA
# Format: .pem
# Download: devops-key.pem — save it somewhere safe (e.g. C:\Users\<you>\keypair\devops-key.pem)
```

**Edge case:** If you already have `devops-key` in AWS from a previous assignment, download the `.pem` again is NOT possible — AWS only lets you download once. If you lost the file, delete the old key pair in AWS and create a new one named `devops-key`.

---

## 2. GitHub Repository Setup

### Verify the repository exists

Go to `https://github.com/chanhengmenh/devops-final-project`. It should exist and contain:

```
Jenkinsfile
app/main.py
app/requirements.txt
app/Dockerfile
terraform/main.tf
terraform/outputs.tf
monitoring/
sonar-project.properties
```

### If the repo is missing files — push them now

```bash
# On your laptop, inside devops-final-project/
git status
git add Jenkinsfile app/ terraform/ monitoring/ sonar-project.properties
git commit -m "add all project files"
git push origin main
```

**Edge case:** Push is rejected because main is already protected.
- Go to GitHub → Settings → Branches → temporarily disable branch protection
- Push the files
- Re-enable branch protection (Section 3)

---

## 3. Branch Protection Rules

Go to: `GitHub → your repo → Settings → Branches → Add branch ruleset`

Use **Branch Ruleset** (modern UI) or **Branch Protection Rules** (classic UI — either works).

### Classic UI path

1. Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Check: **Require a pull request before merging**
   - Required approvals: `1`
4. Check: **Require status checks to pass before merging**
   - After your first Jenkins run you can add the Jenkins check here
5. Check: **Do not allow bypassing the above settings**
6. Click **Save changes**

**Verify:** Try pushing directly to main from your terminal:

```bash
git commit --allow-empty -m "test direct push"
git push origin main
```

Expected: `remote: error: GH006: Protected branch update failed` — this confirms protection is on.

---

## 4. Feature Branch + Pull Request + Merge Conflict

This section produces screenshots **a, b, and c**.

### Step 4.1 — First developer adds a feature

```bash
git checkout main
git pull origin main
git checkout -b feature/grading-api
```

Open `app/main.py` and add this endpoint at the bottom:

```python
# Grading API
@app.get("/grades")
def get_grades():
    return {"grades": [{"student": "Alice", "score": 95}, {"student": "Bob", "score": 82}]}
```

```bash
git add app/main.py
git commit -m "add grading API endpoint"
git push origin feature/grading-api
```

Go to GitHub → your repo → you will see a banner "Compare & pull request".

1. Click **Compare & pull request**
2. Title: `Add grading API endpoint`
3. Assign a reviewer (add a classmate as a collaborator under Settings → Collaborators, or use your second GitHub account)
4. Click **Create pull request**

**Screenshot a:** Take a screenshot of the GitHub PR page showing the open PR, the branch `feature/grading-api`, and the reviewer assigned.

### Step 4.2 — Reviewer approves

The reviewer (classmate or second account) goes to the PR → **Files changed** → reviews → clicks **Review changes** → selects **Approve** → **Submit review**.

**Screenshot b:** Take a screenshot of the approval: the green "Approved" badge with the reviewer's name.

### Step 4.3 — Create a merge conflict

The goal: two branches both change the same line in `app/main.py`.

**On a second branch** (simulate another developer):

```bash
git checkout main
git pull origin main
git checkout -b feature/update-root-message
```

Edit the root endpoint in `app/main.py`:

```python
# Change this line:
return {"message": "FoodExpress API is running"}
# To:
return {"message": "FoodExpress Learning Platform API v2"}
```

```bash
git add app/main.py
git commit -m "update root message for learning platform"
git push origin feature/update-root-message
```

Open a second PR for this branch and merge it **first** (approve it yourself or have the reviewer approve it, then merge it to main).

Now go back to the `feature/grading-api` PR. GitHub will show: **"This branch has conflicts that must be resolved"**.

**Resolve the conflict locally:**

```bash
git checkout feature/grading-api
git pull origin main        # this triggers the conflict
```

Git will show a conflict in `app/main.py`. Open the file — you will see:

```
<<<<<<< HEAD
return {"message": "FoodExpress Learning Platform API v2"}
=======
return {"message": "FoodExpress API is running"}
>>>>>>> feature/grading-api
```

Edit the file to keep BOTH changes correctly:

```python
return {"message": "FoodExpress Learning Platform API v2"}
```

(Keep the updated message AND keep the grading endpoint below it.)

```bash
git add app/main.py
git commit -m "resolve merge conflict - keep updated root message and grading API"
git push origin feature/grading-api
```

The PR on GitHub will now show the conflict is resolved. Reviewer re-approves. Merge the PR.

**Screenshot c:** Take a screenshot showing the conflict markers in the file (before resolving), OR the GitHub conflict editor UI, OR the terminal showing the merge conflict — then a second screenshot after the commit showing it resolved.

---

## 5. Jenkins Server Setup

> If Jenkins is already running on your previous assignment server, skip to Section 6. If starting fresh, follow below.

### Option A — Jenkins on the same EC2 as the DevOps assignments

SSH into your Jenkins EC2 instance:

```bash
ssh -i keypair/devops-key.pem ubuntu@<JENKINS-EC2-IP>
```

Verify Jenkins is running:

```bash
sudo systemctl status jenkins
```

If not running: `sudo systemctl start jenkins`

Jenkins UI: `http://<JENKINS-EC2-IP>:8080`

### Required Jenkins plugins

Go to **Manage Jenkins → Plugins → Available plugins** and install:

- `SonarQube Scanner`
- `SSH Agent`
- `Docker Pipeline`
- `Amazon Web Services SDK` (for AWS credentials binding)
- `Credentials Binding Plugin`
- `Pipeline`

Restart Jenkins after installing.

### Install Trivy on the Jenkins server

```bash
sudo apt-get install -y wget apt-transport-https gnupg
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb generic main" | \
  sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install -y trivy
trivy --version    # verify
```

### Install Terraform on the Jenkins server

```bash
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | \
  sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
  https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update && sudo apt-get install terraform
terraform version   # verify
```

### Install sonar-scanner on the Jenkins server

```bash
cd /opt
sudo wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-6.2.1.4610-linux-x64.zip
sudo apt install unzip -y
sudo unzip sonar-scanner-cli-6.2.1.4610-linux-x64.zip
sudo mv sonar-scanner-6.2.1.4610-linux-x64 sonar-scanner
sudo ln -s /opt/sonar-scanner/bin/sonar-scanner /usr/local/bin/sonar-scanner
sonar-scanner --version  # verify
```

**Edge case:** Jenkins runs as the `jenkins` user but `/usr/local/bin/sonar-scanner` must be executable by it.

```bash
sudo chmod +x /usr/local/bin/sonar-scanner
```

---

## 6. SonarQube Setup

SonarQube runs on the Jenkins server (or same network), port 9000.

### Start SonarQube with Docker (if not already running)

```bash
docker run -d \
  --name sonarqube \
  -p 9000:9000 \
  sonarqube:lts-community
```

Wait ~60 seconds for it to start, then open: `http://<JENKINS-EC2-IP>:9000`

Default login: `admin / admin` → it will ask you to change the password immediately (change it to something you remember, e.g., `Admin@1234`).

### Create a SonarQube project

1. SonarQube UI → **Projects → Create project manually**
2. Project key: `devops-final-project`
3. Display name: `devops-final-project`
4. Set up: **Locally**
5. Generate a token → copy it (e.g., `sqa_abc123...`)

### Wire SonarQube into Jenkins

**Manage Jenkins → System → SonarQube servers:**

- Name: `SonarQube` (must match exactly — the Jenkinsfile uses this name)
- Server URL: `http://localhost:9000` (or `http://<JENKINS-IP>:9000` if on a different host)
- Server authentication token: Add → Jenkins → Secret text → paste the token you generated → ID: `sonar-token`

**Manage Jenkins → Tools → SonarQube Scanner:**

- Add SonarQube Scanner
- Name: `SonarQube Scanner`
- Install automatically: check it, pick latest version

### Verify sonar-project.properties

This file lives in the root of your repo. It should contain:

```properties
sonar.projectKey=devops-final-project
sonar.projectName=devops-final-project
sonar.sources=app
sonar.language=py
sonar.host.url=http://localhost:9000
sonar.login=<your-sonar-token>
```

**Edge case:** If `sonar.host.url` is wrong the scan runs but cannot post results back. Double-check the URL is reachable from the Jenkins process.

---

## 7. Jenkins Credentials

Go to **Manage Jenkins → Credentials → System → Global credentials → Add Credential**.

### 7.1 Docker Hub credentials

- Kind: **Username with password**
- Username: `chanhengmenh`
- Password: your Docker Hub password (or access token — preferred)
- ID: `dockerhub-creds`
- Description: Docker Hub

**How to create a Docker Hub access token (preferred over password):**
- Docker Hub → Account Settings → Security → New Access Token → name it `jenkins` → copy the token
- Use the token as the password above

### 7.2 EC2 SSH key

- Kind: **SSH Username with private key**
- ID: `ec2-key`
- Username: `ubuntu`
- Private key: Enter directly → paste the contents of `devops-key.pem`

**Edge case:** On Windows, when you open `devops-key.pem` in Notepad, it may use Windows line endings (CRLF). Jenkins on Linux needs Unix line endings (LF). Use VS Code to open the file → bottom-right corner → click CRLF → change to LF → save → copy the content, or run:

```bash
# On the Jenkins server
cat devops-key.pem | tr -d '\r' > devops-key-unix.pem
```

### 7.3 AWS credentials

- Kind: **AWS Credentials** (requires the AWS SDK plugin)
- ID: `aws-credentials`
- Access Key ID: your AWS access key
- Secret Access Key: your AWS secret key

---

## 8. Jenkins Pipeline Job

### Create the pipeline

1. Jenkins dashboard → **New Item**
2. Name: `devops-final-project`
3. Type: **Pipeline**
4. Click OK

### Configure the pipeline

Scroll to the **Pipeline** section:

- Definition: **Pipeline script from SCM**
- SCM: **Git**
- Repository URL: `https://github.com/chanhengmenh/devops-final-project.git`
  - (Or use SSH: `git@github.com:chanhengmenh/devops-final-project.git` — requires SSH key credential added for the GitHub connection)
- Branch: `*/main`
- Script Path: `Jenkinsfile`

Under **Build Triggers**, check: **GitHub hook trigger for GITScm polling** (for auto-trigger on push).

Click **Save**.

### Set up the GitHub webhook (for auto-trigger)

1. GitHub repo → Settings → Webhooks → Add webhook
2. Payload URL: `http://<JENKINS-EC2-IP>:8080/github-webhook/`
3. Content type: `application/json`
4. Events: **Just the push event**
5. Click Add webhook

**Edge case:** GitHub cannot reach Jenkins if Jenkins is on a private/local IP. Use a public EC2 IP. If Jenkins is on localhost, the webhook won't work — trigger the build manually instead (click **Build Now** in Jenkins).

**Screenshot d:** After saving the pipeline, go to the job page → click **Pipeline Syntax** or simply take a screenshot of the full `Jenkinsfile` content open in a text editor or the Jenkins SCM configuration page.

---

## 9. Simulate Quality Gate Failure (Screenshot g)

Before the full success run, demonstrate that the pipeline can fail at SonarQube.

### Method: Temporarily set a failing quality gate

1. SonarQube UI → Administration → Quality Gates → Create a new gate named `Strict`
2. Add condition: **Coverage** is less than `80%` (Python FastAPI without tests will have 0% coverage → this will always fail)
3. Go to: Projects → devops-final-project → Project Settings → Quality Gate → select `Strict`

Now trigger a pipeline run (click **Build Now** in Jenkins).

The pipeline will:
- Pass Stage 1 (Checkout) ✓
- Pass Stage 2 (SonarQube Scan) ✓
- **Fail Stage 3 (Quality Gate)** ✗ — pipeline aborts here

**Screenshot g:** Take a screenshot of the Jenkins pipeline view showing stages 1 and 2 green and stage 3 red (failed), with the error message in the console log.

### Reset the quality gate to default

After the screenshot:
1. SonarQube → Projects → devops-final-project → Project Settings → Quality Gate → select `Sonar way` (the default)
2. This allows the pipeline to pass in the next run

---

## 10. Trivy Verification

Trivy is called in Stage 5 of the Jenkinsfile. To verify it works without running the full pipeline:

```bash
# On the Jenkins server
docker build -t chanhengmenh/devops-final-project:latest ./app
trivy image \
  --exit-code 1 \
  --severity CRITICAL \
  --no-progress \
  --format table \
  chanhengmenh/devops-final-project:latest
```

Expected: A table of vulnerabilities. If there are no CRITICAL ones, exit code is 0 (pipeline continues). If there are CRITICALs, exit code is 1 (pipeline stops).

**Screenshot f:** Take a screenshot of the Trivy output table in the Jenkins console log during a pipeline run, OR from the terminal command above.

**Edge case — Trivy fails to download the DB:**

```
FATAL  fatal error: OCI repository error
```

Fix: Trivy needs internet access from the Jenkins server. Check security groups allow outbound traffic on port 443. Also try:

```bash
trivy image --download-db-only
```

---

## 11. Full Pipeline Run — Success

With the quality gate reset to default (Section 9), trigger a build.

### Pre-flight checklist

Before clicking Build Now, verify:

- [ ] SonarQube is running: `http://<JENKINS-IP>:9000` loads
- [ ] Docker is running on Jenkins server: `docker ps`
- [ ] Terraform is installed: `terraform version`
- [ ] `devops-key.pem` key pair exists in AWS: EC2 → Key Pairs → `devops-key`
- [ ] All 3 credentials are set in Jenkins (dockerhub-creds, ec2-key, aws-credentials)

### Trigger the build

Jenkins → devops-final-project → **Build Now**

Watch the **Stage View** in real time.

### Stage-by-stage expected behavior

| Stage | Expected duration | Success indicator |
|-------|------------------|-------------------|
| Checkout | ~5s | Clones repo |
| SonarQube Scan | ~30–60s | "ANALYSIS SUCCESSFUL" in log |
| Quality Gate | ~10–30s | "Quality gate status: OK" |
| Build Docker Image | ~60–120s | "Successfully built" and "Successfully tagged" |
| Trivy Security Scan | ~60–120s | Table printed, no CRITICAL exit |
| Push Image | ~30s | "latest: digest: sha256:..." |
| Provision EC2 | ~60–120s | "Apply complete! Resources: 2 added" |
| Deploy App | ~60–180s | Includes SSH retry loop; "foodapp" container started |
| Deploy Monitoring | ~30–60s | `docker compose up -d` shows containers |

**Edge case — Stage 7 (Provision EC2) fails: "Error: creating Security Group: InvalidGroup.Duplicate"**

This happens when Terraform tries to create `web_sg` but it already exists from a previous run (Terraform lost its state).

Fix option A — import existing resources into Terraform state:

```bash
# On Jenkins server, in the terraform/ directory
terraform import aws_security_group.web_sg <sg-id>
terraform import aws_instance.app <instance-id>
```

Fix option B — destroy and recreate (if no state file exists):

```bash
# Manually delete the security group in AWS Console first
# EC2 → Security Groups → select web_sg → Actions → Delete
# Then re-run the pipeline
```

Fix option C — add `create_before_destroy` or use `name_prefix` in `main.tf` to avoid name collisions (better long-term).

**Edge case — Stage 8 (Deploy App): SSH times out after 12 retries**

The EC2 instance takes longer than 3 minutes to boot. Wait and re-run the pipeline. The user_data script (Docker install) can take 3–5 minutes on first boot.

**Edge case — Stage 8: "docker: command not found" on EC2**

User data hasn't finished running. Wait 2–3 more minutes. SSH in manually and check:

```bash
ssh -i devops-key.pem ubuntu@<EC2-IP>
docker --version   # if this fails, user_data is still running
tail -f /var/log/cloud-init-output.log   # watch bootstrap logs
```

**Screenshot h:** Take a screenshot of the Jenkins console log showing the Terraform apply output with "Apply complete! Resources: 2 added" and the EC2 public IP output.

**Screenshot i:** Take a screenshot of the Jenkins console log for the **Deploy App** stage showing the SSH commands running and the container starting (lines like `docker pull`, `docker run`, and the container ID output).

**Screenshot j:** Take a screenshot of the Jenkins **Stage View** (the colored pipeline graph on the job's main page) showing all 9 stages green.

---

## 12. Verify Deployment

Get the EC2 public IP from the Jenkins console output (the last "Pipeline succeeded!" message shows all URLs), or run:

```bash
# On Jenkins server
cd terraform
terraform output public_ip
```

### Test the application from your laptop browser

Open: `http://<EC2-PUBLIC-IP>:8000`

Expected: `{"message": "FoodExpress Learning Platform API v2"}`

Also test the API docs: `http://<EC2-PUBLIC-IP>:8000/docs` — Swagger UI should load.

Test the health check: `http://<EC2-PUBLIC-IP>:8000/health`

Expected: `{"status": "ok"}`

**Screenshot k:** Take a screenshot of your **laptop browser** showing `http://<EC2-PUBLIC-IP>:8000` with the JSON response, and/or the Swagger UI at `/docs`.

**Edge case — browser shows "This site can't be reached":**

1. Check EC2 instance is running: AWS Console → EC2 → Instances
2. Check security group has port 8000 open: EC2 → Security Groups → `web_sg` → Inbound rules
3. Check the container is running on EC2:
   ```bash
   ssh -i devops-key.pem ubuntu@<EC2-IP>
   docker ps   # should show foodapp container
   docker logs foodapp   # check for startup errors
   ```

---

## 13. Grafana Dashboards

Prometheus and Grafana are running on the EC2 instance (deployed in Stage 9).

### Verify Prometheus is up

Open: `http://<EC2-PUBLIC-IP>:9090`

Go to **Status → Targets** — you should see three targets:

| Target | Status |
|--------|--------|
| `prometheus:9090` | UP |
| `node-exporter:9100` | UP |
| `172.17.0.1:8000` | UP |

**Edge case — foodexpress-api target is DOWN:**

The `prometheus.yml` scrapes `172.17.0.1:8000` (the Docker bridge gateway IP). This is the default Docker bridge but may differ on your EC2. SSH in and check:

```bash
docker network inspect bridge | grep Gateway
```

If the gateway is different (e.g., `172.18.0.1`), update `monitoring/prometheus.yml` locally and re-run the pipeline (or SCP the updated file manually).

### Access Grafana

Open: `http://<EC2-PUBLIC-IP>:3000`

Login: `admin` / `admin`

### Import Node Exporter dashboard (system metrics)

1. Left sidebar → **Dashboards → Import**
2. Dashboard ID: `1860`
3. Click **Load**
4. Data source: select `Prometheus`
5. Click **Import**

You should see CPU, memory, disk, and network graphs for the EC2 instance.

### Import FastAPI Observability dashboard (app metrics)

1. Left sidebar → **Dashboards → Import**
2. Dashboard ID: `17175`
3. Click **Load**
4. Data source: select `Prometheus`
5. Click **Import**

To generate some traffic so the graphs show data:

```bash
# From your laptop
for i in {1..20}; do curl http://<EC2-PUBLIC-IP>:8000/orders; done
for i in {1..5}; do
  curl -X POST http://<EC2-PUBLIC-IP>:8000/orders \
    -H "Content-Type: application/json" \
    -d '{"item":"Pizza","quantity":2,"price":12.5}'
done
```

Wait ~30 seconds for Prometheus to scrape, then refresh the Grafana dashboard.

**Screenshot l:** Take a screenshot of a Grafana dashboard (dashboard 1860 or 17175) showing live data/graphs with the EC2 IP visible in the browser URL bar.

---

## 14. Screenshot Checklist

| # | Screenshot | How to get it | Done |
|---|-----------|---------------|------|
| a | GitHub Branches + Pull Request | GitHub → your repo → Pull requests → open PR page | [ ] |
| b | Reviewer Approve | GitHub → PR → show the green "Approved" review by reviewer | [ ] |
| c | Merge Conflict + Resolution | Terminal showing conflict markers OR GitHub conflict editor, then the resolved commit | [ ] |
| d | Full Jenkinsfile script | Open `Jenkinsfile` in editor + full scroll, or GitHub repo file view | [ ] |
| e | SonarQube report | SonarQube → Projects → devops-final-project → Overview page | [ ] |
| f | Trivy scan result | Jenkins console log → Stage 5 (Trivy Security Scan) output table | [ ] |
| g | Pipeline termination on quality fail | Jenkins Stage View with Stage 3 (Quality Gate) red/failed | [ ] |
| h | Terraform apply output | Jenkins console log → Stage 7 (Provision EC2) → "Apply complete!" | [ ] |
| i | Continuous Deployment stage | Jenkins console log → Stage 8 (Deploy App) → docker run output | [ ] |
| j | Pipeline success (graphical view) | Jenkins → job page → Stage View with all 9 stages green | [ ] |
| k | App running from laptop browser | Browser at `http://<EC2-IP>:8000` showing JSON or `/docs` Swagger | [ ] |
| l | Grafana dashboard | Grafana at `http://<EC2-IP>:3000` showing a live dashboard with data | [ ] |

---

## 15. Common Errors & Fixes

### "Permission denied (publickey)" when Jenkins SSHs to EC2

- The `ec2-key` credential in Jenkins has Windows-format line endings
- Fix: re-paste the key content after converting to Unix line endings (see Section 7.2)

### Terraform: "No valid credential sources found"

- The `aws-credentials` Jenkins credential is not bound correctly
- The Jenkinsfile uses `AmazonWebServicesCredentialsBinding` — requires the **AWS SDK Plugin** installed in Jenkins
- Check: Manage Jenkins → Plugins → Installed → search "Amazon Web Services"

### SonarQube quality gate hangs / never returns

The quality gate waits for a webhook callback from SonarQube. Set it up:

1. SonarQube → Administration → Configuration → Webhooks → Create
2. Name: `Jenkins`
3. URL: `http://<JENKINS-IP>:8080/sonarqube-webhook/`
4. Click Create

Without this webhook, the pipeline will hang at `waitForQualityGate` for 5 minutes then time out.

### Docker push fails: "denied: requested access to the resource is denied"

- Docker Hub credentials are wrong, or the image name doesn't match your Docker Hub username
- Image name in Jenkinsfile: `chanhengmenh/devops-final-project:latest`
- Your Docker Hub username must be `chanhengmenh` — if different, update `IMAGE` in the Jenkinsfile

### Grafana: "No data" on dashboards

- Prometheus is not scraping successfully — check Targets page at `:9090`
- Generate traffic to the app (curl commands in Section 13)
- Wait 1–2 scrape intervals (15s each) before expecting data

### EC2 instance already exists from a previous run

Terraform will try to create a new instance every run unless state is preserved. The `terraform.tfstate` file on the Jenkins server (inside the `terraform/` workspace) tracks what was created. If it exists, Terraform will update instead of recreate. If it's missing (new pipeline workspace), Terraform will try to create new resources — causing duplicates.

Best practice: store Terraform state in S3 (add a backend block to `main.tf`) or manually clean up old EC2 resources before re-running.

### `docker compose` vs `docker-compose`

The Jenkinsfile uses `docker compose` (the plugin, V2 syntax). If your EC2 only has `docker-compose` (V1, standalone binary), the deploy monitoring stage will fail.

Fix — the Jenkinsfile already handles this:

```bash
if ! docker compose version > /dev/null 2>&1; then
    sudo apt-get install -y docker-compose-plugin
fi
```

This auto-installs the plugin if missing. If this still fails, SSH to the EC2 and run the install manually.

---

*End of guide. Follow sections 1 → 14 in order for a clean first run.*

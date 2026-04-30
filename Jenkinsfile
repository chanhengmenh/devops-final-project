pipeline {
    agent any

    environment {
        IMAGE = "chanhengmenh/devops-final-project:latest"
        SONAR_PROJECT_KEY = "devops-final-project"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('SonarQube Scan') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    script {
                        def scannerHome = tool 'SonarQube Scanner'
                        sh "${scannerHome}/bin/sonar-scanner -Dproject.settings=sonar-project.properties"
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${IMAGE} ./app"
            }
        }

        stage('Trivy Security Scan') {
            steps {
                sh """
                    trivy image \
                        --exit-code 1 \
                        --severity CRITICAL \
                        --no-progress \
                        --format table \
                        ${IMAGE}
                """
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo "${DOCKER_PASS}" | docker login -u "${DOCKER_USER}" --password-stdin
                        docker push ${IMAGE}
                    """
                }
            }
        }

        stage('Provision EC2') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-credentials',
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]]) {
                    dir('terraform') {
                        sh """
                            terraform init
                            terraform apply -auto-approve
                            terraform output -raw public_ip > ../ec2_ip.txt
                        """
                    }
                }
            }
        }

        stage('Deploy App') {
            steps {
                script {
                    def ec2Ip = readFile('ec2_ip.txt').trim()
                    sshagent(['ec2-key']) {
                        // Retry loop: wait up to ~3 minutes for EC2 to finish booting
                        retry(12) {
                            sleep(time: 15, unit: 'SECONDS')
                            sh """
                                ssh -o StrictHostKeyChecking=no ubuntu@${ec2Ip} '
                                    docker pull ${env.IMAGE}
                                    docker stop foodapp 2>/dev/null || true
                                    docker rm foodapp 2>/dev/null || true
                                    docker run -d \
                                        --name foodapp \
                                        --restart always \
                                        -p 8000:8000 \
                                        ${env.IMAGE}
                                '
                            """
                        }
                    }
                }
            }
        }

        stage('Deploy Monitoring') {
            steps {
                script {
                    def ec2Ip = readFile('ec2_ip.txt').trim()
                    sshagent(['ec2-key']) {
                        sh """
                            scp -o StrictHostKeyChecking=no -r monitoring ubuntu@${ec2Ip}:~/monitoring
                            ssh -o StrictHostKeyChecking=no ubuntu@${ec2Ip} '
                                cd ~/monitoring
                                if ! docker compose version > /dev/null 2>&1; then
                                    sudo apt-get install -y docker-compose-plugin
                                fi
                                docker compose up -d
                            '
                        """
                    }
                    echo "App:        http://${ec2Ip}:8000"
                    echo "Prometheus: http://${ec2Ip}:9090"
                    echo "Grafana:    http://${ec2Ip}:3000"
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed.'
        }
    }
}

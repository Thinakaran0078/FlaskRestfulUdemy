pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/python -m pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Tests and Coverage') {
            steps {
                sh '''
                    mkdir -p reports
                    .venv/bin/python -m pytest tests -v \
                        --junitxml=reports/junit.xml \
                        --cov \
                        --cov-report=term-missing \
                        --cov-report=xml:reports/coverage.xml
                '''
            }
        }
        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'sonar-scanner'

                    withSonarQubeEnv('local-sonarqube') {
                        sh "\"${scannerHome}/bin/sonar-scanner\""
                    }
                }
            }
        }
        stage('Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        def gate = waitForQualityGate()

                        if (gate.status != 'OK') {
                            error "Quality gate failed: ${gate.status}"
                        }
                    }
                }
            }
        }
        stage('Dependency Scan') {
            steps {
                sh '''
                    python3 -m venv .audit-venv
                    .audit-venv/bin/python -m pip install pip-audit

                    mkdir -p reports
                    rm -f reports/dependency-audit.txt

                    .audit-venv/bin/python -m pip_audit \
                        -r requirements.txt \
                        --strict \
                        --progress-spinner off \
                        --format columns \
                        --output reports/dependency-audit.txt
                '''
            }

            post {
                always {
                    sh '''
                        if [ -f reports/dependency-audit.txt ]; then
                            cat reports/dependency-audit.txt
                        fi
                    '''

                    archiveArtifacts artifacts: 'reports/dependency-audit.txt',
                                     allowEmptyArchive: true
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                sh '''
                    docker version

                    docker build \
                        --tag "flask-restful-udemy:${BUILD_NUMBER}" \
                        .

                    docker image inspect \
                        "flask-restful-udemy:${BUILD_NUMBER}" \
                        --format '{{.Id}}'
                '''
            }
        }
        stage('Push Docker Image') {
            steps {
                sh '''
                    docker tag "flask-restful-udemy:${BUILD_NUMBER}" \
                        "localhost:15000/flask-restful-udemy:${BUILD_NUMBER}"

                    docker push \
                        "localhost:15000/flask-restful-udemy:${BUILD_NUMBER}"
                '''
            }
        }
    } // Close stages BEFORE post

    post {
        always {
            junit 'reports/junit.xml'
            archiveArtifacts artifacts: 'reports/*.xml',
                             allowEmptyArchive: true
        }
    }
}
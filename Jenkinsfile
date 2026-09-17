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
    } // Close stages BEFORE post

    post {
        always {
            junit 'reports/junit.xml'
            archiveArtifacts artifacts: 'reports/*.xml',
                             allowEmptyArchive: true
        }
    }
}
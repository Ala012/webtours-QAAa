pipeline {
    agent any
    environment {
        WEBTOURS_URL = 'http://127.0.0.1:1080'
        HEADLESS     = '1'
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Install') {
            steps { bat 'python -m pip install -r requirements.txt' }
        }
        stage('Vérifier WebTours') {
            // WebTours doit tourner sur l'agent (startserver.bat)
            steps { bat 'curl -f %WEBTOURS_URL%/WebTours/index.htm' }
        }
        stage('Tests automatiques') {
            steps {
                bat 'python -m pytest tests --junitxml=report.xml --html=report.html --self-contained-html'
            }
        }
    }
    post {
        always {
            junit allowEmptyResults: true, testResults: 'report.xml'
            archiveArtifacts artifacts: 'report.html', allowEmptyArchive: true
        }
    }
}

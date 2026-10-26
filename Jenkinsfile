
pipeline {
    agent any

    stages {
        stage('Descargar codigo') {
            steps {
                checkout scm
            }
        }

        stage('Empaquetar Equi') {
            steps {
                bat 'git archive --format=zip --output=Equi_Equigrup.zip HEAD'
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: 'Equi_Equigrup.zip',
                             fingerprint: true
        }
    }
}

// Pipeline Jenkins : WebTours QA. Un seul test automatisé par défaut (test_ft_login_valide_http), modifiable par le paramètre TESTS
// Dépôt : https://github.com/Ala012/webtours-QAAa.git (public, branche main : aucun identifiant nécessaire)
//
// Prérequis sur l'agent Jenkins (Windows) :
//   - Python 3.12 installé (Google Chrome seulement pour les tests d'interface)
//   - WebTours installé (dossier par défaut C:\WebTours, voir le paramètre WEBTOURS_HOME)
pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 45, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
    }

    triggers {
        pollSCM('H/5 * * * *')   // vérifie le dépôt toutes les 5 minutes et lance un build s'il y a un nouveau commit
        cron('H 2 * * *')        // et lance aussi une exécution chaque nuit
    }

    parameters {
        // un seul test automatisé par défaut : connexion jojo / bean par HTTP (stable, sans navigateur)
        // pour lancer toute la suite, mettre « tests » ; pour les tests d'interface, Chrome doit être installé sur l'agent
        string(name: 'TESTS', defaultValue: 'tests/test_rsva_auth.py::test_ft_login_valide_http', description: 'Test(s) pytest à lancer')
        string(name: 'WEBTOURS_HOME', defaultValue: 'C:\\WebTours', description: "Dossier de WebTours sur l'agent")
    }

    environment {
        REPO_URL     = 'https://github.com/Ala012/webtours-QAAa.git'
        WEBTOURS_URL = 'http://127.0.0.1:1080'
        HEADLESS     = '1'   // Chrome sans fenêtre : un agent Jenkins n'a pas d'écran
        PYTHONUTF8   = '1'
    }

    stages {
        stage('Récupérer le code') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[url: env.REPO_URL]]
                ])
            }
        }

        stage('Installer les dépendances') {
            steps {
                bat 'python -m pip install -r requirements.txt'
            }
        }

        stage('Préparer WebTours') {
            // vérifie que WebTours répond ; sinon le démarre et attend jusqu'à 60 secondes
            steps {
                powershell '''
                $url = "$env:WEBTOURS_URL/WebTours/index.htm"
                function Test-Up { try { (Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 10).StatusCode -eq 200 } catch { $false } }
                if (-not (Test-Up)) {
                    Write-Host "WebTours ne répond pas : démarrage"
                    Start-Process -FilePath "$env:WEBTOURS_HOME\\StartServer.bat" -WorkingDirectory $env:WEBTOURS_HOME -WindowStyle Hidden
                    for ($i = 0; $i -lt 30 -and -not (Test-Up); $i++) { Start-Sleep -Seconds 2 }
                }
                if (-not (Test-Up)) { throw "WebTours ne répond pas sur $url" }
                Write-Host "WebTours OK"
                '''
            }
        }

        stage('Tests automatiques') {
            steps {
                script {
                    def code = bat(returnStatus: true, script: """
                        if not exist results mkdir results
                        python -m pytest ${params.TESTS} -p capture_plugin --junitxml=results/report.xml --html=results/report.html --self-contained-html
                    """)
                    // pytest renvoie 1 quand des tests échouent : tant que des anomalies de WebTours existent,
                    // le build est « instable » (jaune) et non « en erreur » (rouge)
                    if (code == 1) {
                        unstable('Des tests ont échoué : voir le rapport results/report.html')
                    } else if (code != 0) {
                        error("pytest s'est arrêté avec le code ${code}")
                    }
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'results/report.xml'
            archiveArtifacts artifacts: 'results/report.html, results/report.xml, results/captures/**', allowEmptyArchive: true
        }
    }
}

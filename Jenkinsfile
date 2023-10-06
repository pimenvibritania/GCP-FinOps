pipeline {
    agent {
        node {
            label 'docker-slave-ssh || docker-slave-ssh-02'
        }
    }
    environment {
        serviceName = "${JOB_NAME}".split('/').first()
        gitRepositoryUrl = "bitbucket.org/moladinTech"
        gitCommitHash = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
        shortCommitHash = gitCommitHash.take(7)
        codeRepo = "git@bitbucket.org:moladinTech/${serviceName}.git"
        dockerUsername = "ubuntu"
        servicePort = "8000"
        deploymentName = "${serviceName}"
        emailJenkinsServiceAccount = "infra-prod-sa-id@moladin-infra-prod.iam.gserviceaccount.com"
        keyJenkinsServiceAccount = credentials('jenkinsServiceAccountInfra')
        garLocation = "asia-southeast2-docker.pkg.dev"
        garProject = "moladin-infra-prod"
        techFamily = "infra"
        garRepository = "infra-prod"
        gkeName = "${techFamily}-prod-cluster"
        gkeZone = "asia-southeast2-a"
        projectName = "moladin-${techFamily}-prod"   
        context = 'gke_moladin-infra-prod_asia-southeast2-a_infra-prod-cluster'
        consulToken = credentials('consul-dev-token')
        consulProdToken = credentials('consul-prod-token')
        gitCommitMsg = sh (script: 'git log -1 --pretty=%B ${GIT_COMMIT}', returnStdout: true).trim()
        gitAuthor = sh (script: 'git show -s --pretty=%an', returnStdout: true).trim()
        gitCommitId = sh (script: 'git rev-parse HEAD|cut -c1-7',returnStdout: true).trim()
    }
    stages {
        stage('Environment Check') {
            steps {
                script {
                    if (env.BRANCH_NAME.contains("feature") || env.BRANCH_NAME.contains("hotfix") || env.BRANCH_NAME.contains("bugfix") || env.BRANCH_NAME.contains("fix")) {
                        echo "Due feature branch not coverage for right now, the build will skip"
                        currentBuild.getRawBuild().getExecutor().interrupt(Result.SUCCESS)
                        sleep(1)
                    } else if (env.BRANCH_NAME == "main") {
                        env.resourceEnv = "production"
                        env.versioningCode = "prod"
                        env.consul = "https://consul-gcp.development.jinny.id/v1/kv/${serviceName}/backend"
                        currentBuild.result = hudson.model.Result.SUCCESS.toString()
                    } else if (env.BRANCH_NAME =~ /PROD.*$/){
                        env.resourceEnv = "release"
                        env.versioningCode = "release"
                        env.consul = "https://consul-gcp.production.jinny.id/v1/kv/${serviceName}/backend"
                        currentBuild.result = hudson.model.Result.SUCCESS.toString()
                    } else {
                        echo "environment server not match"
                        currentBuild.getRawBuild().getExecutor().interrupt(Result.SUCCESS)
                        sleep(1)
                    }
                }
            }
        }
        stage ("Build Image") {
            when {
                expression {
                    currentBuild.result == 'SUCCESS' && env.resourceEnv != "pull_request"
                }
            }
            steps {
                script {
                    try {
                        sh "gcloud auth activate-service-account ${emailJenkinsServiceAccount} --key-file=${keyJenkinsServiceAccount}"
                        sh "gcloud auth configure-docker ${garLocation}"
                        sh "cp /home/jenkins/.ssh/id_rsa id_rsa_moladin.pem && cp /home/jenkins/.ssh/id_rsa id_rsa"
                        sh "chmod 400 id_rsa_moladin.pem"
                        if (env.BRANCH_NAME == "main") {
                            sh "getConsul.py ${consul}/cold ${consulToken} > .env"
                            sh "getConsul.py ${consul}/hot ${consulToken} >> .env"
                            sh 'consulMantisCommand.py --get ${consul}/cold ${consulToken} SERVICE_ACCOUNT | sed "s/\'/\\"/g" > service-account.json'
                            sh 'consulMantisCommand.py --get ${consul}/cold ${consulToken} KUBECOST_SA | sed "s/\'/\\"/g" > kubecost_sa.json'
                        } else if (env.BRANCH_NAME =~ /PROD.*$/){
                            sh "getConsul.py ${consul}/cold ${consulProdToken} > .env"
                            sh "getConsul.py ${consul}/hot ${consulProdToken} >> .env"
                            sh 'consulMantisCommand.py --get ${consul}/cold ${consulProdToken} SERVICE_ACCOUNT | sed "s/\'/\\"/g" > service-account.json'
                            sh 'consulMantisCommand.py --get ${consul}/cold ${consulProdToken} KUBECOST_SA | sed "s/\'/\\"/g" > kubecost_sa.json'
                        }
                        // sh "getConsul.py ${consul}/cold ${consulToken} > .env"
                        // sh "getConsul.py ${consul}/hot ${consulToken} >> .env"
                        // sh 'consulMantisCommand.py --get ${consul}/cold ${consulToken} SERVICE_ACCOUNT | sed "s/\'/\\"/g" > service-account.json'
                        // sh 'consulMantisCommand.py --get ${consul}/cold ${consulToken} KUBECOST_SA | sed "s/\'/\\"/g" > kubecost_sa.json'
                        sh "docker build -t ${garLocation}/${garProject}/${garRepository}/${serviceName}:${shortCommitHash}-${BUILD_NUMBER} ."
                        sh "cd kubernetes/development/cronjob/script; docker build -t ${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-${shortCommitHash}-${BUILD_NUMBER} -f Dockerfile.cronjob ."
                        sh "cd kubernetes/development/cronjob/script; docker build -t ${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-send-report-devl -f Dockerfile.cronjob ."
                        sh "cd kubernetes/production/cronjob/script; docker build -t ${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-send-report-prod -f Dockerfile.cronjob ."
                        sh "cd kubernetes/production/cronjob/script; docker build -t ${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-sync-gcp-cost-prod -f Dockerfile.cronjob ."
                        sh "docker push ${garLocation}/${garProject}/${garRepository}/${serviceName}:${shortCommitHash}-${BUILD_NUMBER}"
                        sh "docker push ${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-${shortCommitHash}-${BUILD_NUMBER}"
                        sh "docker push ${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-send-report-devl"
                        sh "docker push ${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-send-report-prod"
                        sh "docker push ${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-sync-gcp-cost-prod"
                        currentBuild.result = 'SUCCESS'
                    } catch(e) {
                        currentBuild.result = 'FAILURE'
                        throw e
                    } finally {
                        if (currentBuild.result == "FAILURE") {
                            echo "Build Image ${serviceName} fail"
                        }
                    }
                }
            }
        }
        stage ("Deployment") {
            when {
                expression {
                    currentBuild.result == "SUCCESS" && env.resourceEnv == "production"
                }
            }
            steps {
                script {
                    try {
                        sh "gcloud auth activate-service-account ${emailJenkinsServiceAccount} --key-file=${keyJenkinsServiceAccount}"
                        sh "gcloud auth configure-docker ${garLocation}"
                        sh "gcloud container clusters get-credentials ${gkeName} --zone ${gkeZone} --project ${projectName}"
                        sh "getConsul.py ${consul}/cold ${consulToken} > ${serviceName}-env-cold"
                        sh "getConsul.py ${consul}/hot ${consulToken} > ${serviceName}-env-hot"
                        sh "kubectl --context ${context} -n ${deploymentName} delete secret ${deploymentName}-cold-app-secret || true"
                        sh "kubectl --context ${context} -n ${deploymentName} delete secret ${deploymentName}-hot-app-secret || true"
                        sh "kubectl --context ${context} -n ${deploymentName} create secret generic ${deploymentName}-cold-app-secret --from-env-file=${serviceName}-env-cold"
                        sh "kubectl --context ${context} -n ${deploymentName} create secret generic ${deploymentName}-hot-app-secret --from-env-file=${serviceName}-env-hot"
                        sh "kubectl --context ${context} -n ${deploymentName} set image deployment/${deploymentName}-app-deployment ${deploymentName}-app=${garLocation}/${garProject}/${garRepository}/${serviceName}:${shortCommitHash}-${BUILD_NUMBER}"
                        sh "kubectl --context ${context} -n ${deploymentName} rollout restart deployment.apps"
                        
                        sh "kubectl --context ${context} -n ${deploymentName} set image cronjob.batch/kubecost-insert-data kubecost-insert-data=${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-${shortCommitHash}-${BUILD_NUMBER}"
                        sh "kubectl --context ${context} -n ${deploymentName} set image cronjob.batch/kubecost-check-status kubecost-check-status=${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-${shortCommitHash}-${BUILD_NUMBER}"
                        currentBuild.result = 'SUCCESS'
                    } catch(e) {
                        currentBuild.result = 'FAILURE'
                        throw e
                    } finally {
                        if (currentBuild.result == "FAILURE") {
                            echo "Deployment ${serviceName} fail"
                        }
                    }
                }
            }
        }
        stage ("Deployment To Release") {
            when {
                expression {
                    currentBuild.result == "SUCCESS" && env.resourceEnv == "release"
                }
            }
            steps {
                script {
                    try {
                        sh "gcloud auth activate-service-account ${emailJenkinsServiceAccount} --key-file=${keyJenkinsServiceAccount}"
                        sh "gcloud auth configure-docker ${garLocation}"
                        sh "gcloud container clusters get-credentials ${gkeName} --zone ${gkeZone} --project ${projectName}"
                        sh "getConsul.py ${consul}/cold ${consulProdToken} > ${serviceName}-env-cold"
                        sh "getConsul.py ${consul}/hot ${consulProdToken} > ${serviceName}-env-hot"
                        sh "kubectl --context ${context} -n ${deploymentName}-release delete secret ${deploymentName}-cold-app-secret || true"
                        sh "kubectl --context ${context} -n ${deploymentName}-release delete secret ${deploymentName}-hot-app-secret || true"
                        sh "kubectl --context ${context} -n ${deploymentName}-release create secret generic ${deploymentName}-cold-app-secret --from-env-file=${serviceName}-env-cold"
                        sh "kubectl --context ${context} -n ${deploymentName}-release create secret generic ${deploymentName}-hot-app-secret --from-env-file=${serviceName}-env-hot"
                        sh "kubectl --context ${context} -n ${deploymentName}-release set image deployment/${deploymentName}-app-deployment ${deploymentName}-app=${garLocation}/${garProject}/${garRepository}/${serviceName}:${shortCommitHash}-${BUILD_NUMBER}"
                        sh "kubectl --context ${context} -n ${deploymentName}-release rollout restart deployment.apps"

                        sh "kubectl --context ${context} -n ${deploymentName}-release set image cronjob.batch/kubecost-insert-data kubecost-insert-data=${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-${shortCommitHash}-${BUILD_NUMBER}"
                        sh "kubectl --context ${context} -n ${deploymentName}-release set image cronjob.batch/kubecost-check-status kubecost-check-status=${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-${shortCommitHash}-${BUILD_NUMBER}"
                        sh "kubectl --context ${context} -n ${deploymentName}-release set image cronjob.batch/cms-create-report-devl cms-create-report-devl=${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-send-report-devl"
                        sh "kubectl --context ${context} -n ${deploymentName}-release set image cronjob.batch/cms-create-report-prod cms-create-report-prod=${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-send-report-prod"
                        sh "kubectl --context ${context} -n ${deploymentName}-release set image cronjob.batch/cms-sync-gcp-cost cms-sync-gcp-cost=${garLocation}/${garProject}/${garRepository}/${serviceName}:cronjob-sync-gcp-cost-prod"
                        currentBuild.result = 'SUCCESS'
                    } catch(e) {
                        currentBuild.result = 'FAILURE'
                        throw e
                    } finally {
                        if (currentBuild.result == "FAILURE") {
                            echo "Deployment ${serviceName} fail"
                        }
                    }
                }
            }
        }
    }
    post { 
        always { 
           cleanWs()
       }
    }
}

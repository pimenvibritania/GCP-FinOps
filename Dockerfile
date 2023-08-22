# FROM python:3.9
FROM asia-southeast2-docker.pkg.dev/moladin-infra-prod/infra-prod/cost-management-system:base

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Jakarta

COPY requirements.txt .
# install python dependencies
RUN apt-get update
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get install cron -y

COPY . .

# running migrations
RUN python manage.py migrate

# collectstatic
RUN python manage.py collectstatic

# enable cronjob
RUN python manage.py crontab add

# generate kubeconfig for kubecost
RUN gcloud auth activate-service-account --project=moladin-infra-prod --key-file=kubecost_sa.json
RUN gcloud container clusters get-credentials mof-devl-cluster --zone asia-southeast2-a --project moladin-mof-devl
RUN gcloud container clusters get-credentials mof-stag-cluster --zone asia-southeast2-a --project moladin-mof-stag
RUN gcloud container clusters get-credentials mof-prod-regional-cluster --zone asia-southeast2 --project moladin-mof-prod
RUN gcloud container clusters get-credentials shared-devl-cluster --zone asia-southeast2-a --project moladin-shared-devl
RUN gcloud container clusters get-credentials shared-stag-regional-cluster --zone asia-southeast2 --project moladin-shared-stag
RUN gcloud container clusters get-credentials shared-prod-regional-cluster --zone asia-southeast2 --project moladin-shared-prod
RUN gcloud container clusters get-credentials wholesale-prod-cluster --zone asia-southeast2-a --project moladin-wholesale-prod
RUN gcloud container clusters get-credentials frame-prod-cluster --zone asia-southeast2-a --project moladin-frame-prod

# gunicorn
# CMD ["gunicorn", "--config", "gunicorn-cfg.py", "core.wsgi"]

#uvicorn
CMD ["uvicorn", "--workers", "5", "core.asgi:application","--host", "0.0.0.0", "--port", "5005"]

#gunicorn&uvicorrn
# CMD ["gunicorn", "--worker-class", "uvicorn.workers.UvicornWorker", "--config", "gunicorn-cfg.py", "core.asgi"]

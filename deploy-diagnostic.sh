#!/bin/bash
# Déploie le service « Diagnostic jardin Cover Green » sur Cloud Run. À lancer dans Cloud Shell, depuis le dossier du dépôt.
#   bash deploy-diagnostic.sh ID_DU_PROJET_GOOGLE_CLOUD
set -euo pipefail
PROJET=${1:?Indiquez le projet Google Cloud}; REGION=europe-west1; SERVICE=diagnostic-jardin
BUCKET=${PROJET}-diagnostic-jardin; IMAGE=$REGION-docker.pkg.dev/$PROJET/cover-green/$SERVICE:latest
export CLOUDSDK_CORE_PROJECT="$PROJET"   # sans toucher au projet par défaut de Cloud Shell (Alfred)
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com storage.googleapis.com
gcloud artifacts repositories describe cover-green --location=$REGION >/dev/null 2>&1 || gcloud artifacts repositories create cover-green --repository-format=docker --location=$REGION
gcloud storage buckets describe gs://$BUCKET >/dev/null 2>&1 || gcloud storage buckets create gs://$BUCKET --location=$REGION --uniform-bucket-level-access --public-access-prevention
# RGPD : les projets (photos, adresses) sont supprimés automatiquement au bout de 12 mois
printf '{"rule":[{"action":{"type":"Delete"},"condition":{"age":365}}]}' > /tmp/cycle.json && gcloud storage buckets update gs://$BUCKET --lifecycle-file=/tmp/cycle.json >/dev/null
# clé privée de la page des avis, tirée au hasard (jamais dans le code)
gcloud secrets describe admin-key >/dev/null 2>&1 || openssl rand -hex 16 | tr -d '\n' | gcloud secrets create admin-key --data-file=- --replication-policy=automatic
for S in openai-key anthropic-key; do
  if ! gcloud secrets describe $S >/dev/null 2>&1; then
    read -rsp "Collez la clé pour $S puis Entrée : " K; echo
    printf '%s' "$K" | gcloud secrets create $S --data-file=- --replication-policy=automatic
  fi
done
NUM=$(gcloud projects describe "$PROJET" --format='value(projectNumber)'); SA=$NUM-compute@developer.gserviceaccount.com
for S in openai-key anthropic-key admin-key; do gcloud secrets add-iam-policy-binding $S --member=serviceAccount:$SA --role=roles/secretmanager.secretAccessor >/dev/null; done
gcloud storage buckets add-iam-policy-binding gs://$BUCKET --member=serviceAccount:$SA --role=roles/storage.objectAdmin >/dev/null
gcloud builds submit --config cloudbuild.diagnostic.yaml --substitutions=_IMAGE=$IMAGE .
gcloud run deploy $SERVICE --image $IMAGE --region $REGION --allow-unauthenticated --execution-environment gen2 \
  --cpu 2 --memory 2Gi --timeout 600 --no-cpu-throttling --min-instances 0 --max-instances 3 \
  --set-secrets OPENAI_API_KEY=openai-key:latest,ANTHROPIC_API_KEY=anthropic-key:latest,CLE_ADMIN=admin-key:latest \
  --add-volume name=data,type=cloud-storage,bucket=$BUCKET --add-volume-mount volume=data,mount-path=/data
gcloud run services describe $SERVICE --region $REGION --format='value(status.url)'
echo "Page des avis : $(gcloud run services describe $SERVICE --region $REGION --format='value(status.url)')/admin/avis?cle=$(gcloud secrets versions access latest --secret admin-key)"

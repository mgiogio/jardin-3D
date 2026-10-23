#!/bin/bash
# Déplace le service Diagnostic jardin dans son propre projet Google Cloud (sans retaper les clés).
#   bash migrer-diagnostic.sh NOUVEAU_PROJET ANCIEN_PROJET
set -euo pipefail
NEUF=${1:?nouveau projet}; VIEUX=${2:?ancien projet}
gcloud projects describe "$NEUF" >/dev/null 2>&1 || gcloud projects create "$NEUF" --name="Cover Green Diagnostic jardin"
FACT=$(gcloud billing projects describe "$VIEUX" --format='value(billingAccountName)')
gcloud billing projects link "$NEUF" --billing-account="${FACT#billingAccounts/}"
gcloud services enable secretmanager.googleapis.com --project "$NEUF"
for S in openai-key anthropic-key; do   # copie directe d'un coffre à l'autre, la clé n'est jamais affichée
  gcloud secrets describe $S --project "$NEUF" >/dev/null 2>&1 || gcloud secrets versions access latest --secret $S --project "$VIEUX" | gcloud secrets create $S --data-file=- --replication-policy=automatic --project "$NEUF"
done
bash "$(dirname "$0")/deploy-diagnostic.sh" "$NEUF"
gcloud storage cp -r "gs://$VIEUX-diagnostic-jardin/*" "gs://$NEUF-diagnostic-jardin/" 2>/dev/null || true   # projets de test déjà créés
echo "Ancien service toujours en place dans $VIEUX : à supprimer une fois la bascule vérifiée."

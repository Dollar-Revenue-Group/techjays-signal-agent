#!/bin/sh
# Publishes docs/index.html to the n8n-hosted staging site:
#   https://n8n-bkfvq-u78038.vm.elestio.app/webhook/techjays-agent/app
# Usage:  N8N_PUBLISH_CODE=ADMIN-xxxx sh scripts/publish-to-n8n.sh
# The admin code is kept out of the repo on purpose. Ask Jay for it.
set -e
if [ -z "$N8N_PUBLISH_CODE" ]; then echo "Set N8N_PUBLISH_CODE first." >&2; exit 1; fi
DIR=$(cd "$(dirname "$0")/.." && pwd)
python3 -c "import json,sys;json.dump({'content':open(sys.argv[1]).read()},open(sys.argv[2],'w'))" "$DIR/docs/index.html" "$DIR/payload.json"
curl -sS -X POST -H "Content-Type: application/json" --data @"$DIR/payload.json" \
  "https://n8n-bkfvq-u78038.vm.elestio.app/webhook/techjays-agent/publish-site?code=$N8N_PUBLISH_CODE"
echo
rm -f "$DIR/payload.json"

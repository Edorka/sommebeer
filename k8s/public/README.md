# The sommebeer public deployment.
# Expected pre-existing: Secret sommebeer-llm (key: apiKey) in this namespace.
#   kubectl create secret generic sommebeer-llm --from-literal=apiKey=<deepinfra-key> -n sommebeer
# Rotation:
#   kubectl create secret generic sommebeer-llm --from-literal=apiKey=<new> -n sommebeer \
#     --dry-run=client -o yaml | kubectl apply -f - \
#   && kubectl rollout restart deployment/api -n sommebeer
#
# Apply order (kubectl apply -f k8s/public/ handles ordering declaratively;
# the seeding Job retries with backoff until Weaviate answers):
#   kubectl apply -f k8s/public/
#   kubectl -n sommebeer logs job/sommebeer-seed -f        # 3612 beers imported
#   kubectl -n sommebeer get pods                          # all Running
#
# Reaching the UI before DNS exists:
#   echo "<node-ip> sommebeer.ai.abscin.de" >> /etc/hosts
#
# Later, TLS: install cert-manager + Certificate; the Ingress below is kept
# HTTP-only until then (add tls section + ClusterIssuer issuer reference).
### Note: DNS for sommebeer.ai.abscin.de -> node IP is managed outside Git.

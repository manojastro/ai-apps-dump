# Deploying to Azure (for the owner to run)

Nothing in this document has been executed. It needs your Azure subscription and creates billable resources.

## What gets created (infra/bicep/main.bicep)

| Resource | SKU | Purpose |
|---|---|---|
| Log Analytics workspace | PerGB2018, 30-day retention | Container Apps logs |
| User-assigned managed identity | — | pulls images, reads Key Vault, Event Hubs receiver, Azure OpenAI (if you add the role) |
| Key Vault (RBAC) | standard | `database-url` secret |
| Container Registry | Basic | api / worker images |
| PostgreSQL Flexible Server 16 | Burstable B1ms, 32 GB, no HA | checkpoints, runs, lineage |
| Event Hubs namespace | Standard, 1 TU, Kafka enabled, local auth off | replaces local Kafka |
| Container Apps environment + `api` + `worker` | consumption | api scales 0–2, worker fixed at 1 |

## Estimated monthly cost (an estimate, not a quote)

From public list prices as I know them (East US, pay-as-you-go). Verify with the Azure Pricing Calculator before deploying.

| Item | Estimate (USD / month) |
|---|---|
| PostgreSQL Flexible B1ms + 32 GB storage | 15 – 25 |
| Event Hubs Standard, 1 throughput unit | 20 – 25 |
| Container Apps (worker always on, 0.5 vCPU / 1 GiB; api mostly idle) | 15 – 40 |
| Container Registry Basic | ~5 |
| Log Analytics (a few GB ingested) | 2 – 15 |
| Key Vault (few operations) | < 1 |
| **Total** | **≈ 60 – 110** |

Azure OpenAI usage is extra and per token. With the fake LLM it is $0.

## Prerequisites

* Azure CLI ≥ 2.60 with Bicep (`az bicep install`), logged in: `az login`
* Choose the subscription explicitly: `az account set --subscription <id>`
* An Azure OpenAI resource is optional (`llmProvider=fake` works without it)

## Steps

```bash
# 1. Variables
RG=rg-schemaguard-dev
LOC=eastus
TAG=v0.1.0

# 2. Resource group
az group create -n $RG -l $LOC

# 3. Validate the template (no changes made)
az bicep build --file infra/bicep/main.bicep --stdout > /dev/null
az deployment group what-if -g $RG --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.parameters.json --parameters postgresAdminPassword="$(openssl rand -base64 24)"

# 4. Deploy infrastructure (keep the password only in Key Vault; it is written there by the template)
az deployment group create -g $RG --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.parameters.json \
  --parameters imageTag=$TAG postgresAdminPassword="$(openssl rand -base64 24)"

# 5. Build images in ACR (no local Docker needed)
ACR=$(az deployment group show -g $RG -n main --query properties.outputs.registryLoginServer.value -o tsv)
az acr build --registry $ACR --image schemaguard-api:$TAG --target api .
az acr build --registry $ACR --image schemaguard-worker:$TAG --target worker .

# 6. Point the apps at the images (first deploy references images that did not exist yet)
az containerapp update -g $RG -n schemaguard-api --image $ACR/schemaguard-api:$TAG
az containerapp update -g $RG -n schemaguard-worker --image $ACR/schemaguard-worker:$TAG

# 7. Smoke test (the API is internal by default; use the console or exec)
az containerapp exec -g $RG -n schemaguard-api --command "python -c \"import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/health').read())\""
```

### Optional: Azure OpenAI with managed identity

```bash
AOAI_ID=$(az cognitiveservices account show -g <aoai-rg> -n <aoai-name> --query id -o tsv)
MI=$(az identity show -g $RG -n schemaguard-id --query principalId -o tsv)
az role assignment create --assignee-object-id $MI --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services OpenAI User" --scope $AOAI_ID
az deployment group create ... --parameters llmProvider=azure azureOpenAiEndpoint=https://<aoai-name>.openai.azure.com/ azureOpenAiDeployment=<deployment>
```

### Schema registry in Azure

Event Hubs provides the Kafka endpoint, but its schema registry does not speak the Confluent REST
API that `ConfluentSchemaRegistry` uses. Options: run a Confluent-compatible registry (Apicurio
`ccompat` API or Karapace) as another container app and pass `registryUrl`, or submit changes via
`POST /changes`. An Azure Schema Registry adapter is `planned`.

### GitHub Actions deploy (optional)

1. Create an Entra app registration with a federated credential for this repo's `production` environment and give it Contributor on the resource group (plus User Access Administrator for the role assignments, or pre-create them).
2. Repo secrets: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `POSTGRES_ADMIN_PASSWORD`.
3. Repo settings → Environments → `production` → required reviewers.
4. Actions → deploy → Run workflow (resource group, image tag).

## Production hardening not done here

* VNet-integrated Container Apps environment and Postgres private access instead of "allow Azure services".
* Entra ID auth on the API ingress (reviewer identity is currently self-declared).
* Postgres Entra authentication instead of a password.
* OTLP exporter to Application Insights.

## Teardown

```bash
az group delete -n $RG --yes --no-wait
# Key Vault is soft-deleted for 7 days; purge it to free the name immediately:
az keyvault list-deleted --query "[?contains(name,'schemaguard')].name" -o tsv | xargs -I{} az keyvault purge --name {}
```

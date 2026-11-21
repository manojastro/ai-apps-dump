// SchemaGuard on Azure (prepare only; deploy with docs/DEPLOY.md after review).
// Resources: Log Analytics, user-assigned managed identity, Key Vault (RBAC), Container Registry,
// PostgreSQL Flexible Server 16, Event Hubs namespace (Kafka endpoint), Container Apps env + api + worker.
// No secrets in code: the Postgres password is a @secure() deploy-time parameter, stored only in Key Vault.

targetScope = 'resourceGroup'

@description('Short prefix for resource names (3-11 lowercase letters/numbers).')
@minLength(3)
@maxLength(11)
param namePrefix string = 'schemaguard'

param location string = resourceGroup().location

@description('Image tag pushed to the registry by the deploy workflow.')
param imageTag string = 'latest'

@description('Postgres administrator login.')
param postgresAdminLogin string = 'sgadmin'

@secure()
@description('Postgres administrator password. Pass at deploy time; never commit it.')
param postgresAdminPassword string

@description('Expose the API on a public HTTPS endpoint. Default: internal to the Container Apps environment.')
param apiExternalIngress bool = false

@description('Azure OpenAI endpoint (optional). Access uses the managed identity, not a key.')
param azureOpenAiEndpoint string = ''

@description('Azure OpenAI deployment name (optional).')
param azureOpenAiDeployment string = ''

@description('LLM provider for SchemaGuard: fake | azure.')
@allowed(['fake', 'azure'])
param llmProvider string = 'fake'

@description('Confluent-compatible schema registry URL reachable from the worker (see DEPLOY.md).')
param registryUrl string = ''

var suffix = uniqueString(resourceGroup().id)
var tags = { app: 'schemaguard', data: 'synthetic' }

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${namePrefix}-logs-${suffix}'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-id'
  location: location
  tags: tags
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: '${namePrefix}acr${suffix}'
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: false }
}

// AcrPull for the app identity
resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, identity.id, 'acrpull')
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${namePrefix}-kv-${take(suffix, 8)}'
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
  }
}

// Key Vault Secrets User for the app identity
resource kvSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, identity.id, 'kv-secrets-user')
  scope: vault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: '${namePrefix}-pg-${suffix}'
  location: location
  tags: tags
  sku: { name: 'Standard_B1ms', tier: 'Burstable' }
  properties: {
    version: '16'
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    storage: { storageSizeGB: 32 }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: 'Disabled' }
    network: { publicNetworkAccess: 'Enabled' }
  }
}

resource pgDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgres
  name: 'schemaguard'
}

// Dev-grade networking: only Azure-hosted services may connect, TLS enforced by the server.
// Production: use VNet integration + private access instead (see DEPLOY.md).
resource pgAllowAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = {
  parent: postgres
  name: 'AllowAzureServices'
  properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
}

resource dbUrlSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'database-url'
  properties: {
    value: 'postgresql://${postgresAdminLogin}:${uriComponent(postgresAdminPassword)}@${postgres.properties.fullyQualifiedDomainName}:5432/schemaguard?sslmode=require'
  }
}

resource eventHubs 'Microsoft.EventHub/namespaces@2024-01-01' = {
  name: '${namePrefix}-eh-${suffix}'
  location: location
  tags: tags
  sku: { name: 'Standard', tier: 'Standard', capacity: 1 } // Standard is the lowest tier with the Kafka endpoint
  properties: {
    kafkaEnabled: true
    minimumTlsVersion: '1.2'
    disableLocalAuth: true // Entra ID (managed identity) only, no SAS keys
  }
}

resource topics 'Microsoft.EventHub/namespaces/eventhubs@2024-01-01' = [for t in ['orders.v1', 'payments.v1', 'customers.v1', 'inventory.v1']: {
  parent: eventHubs
  name: t
  properties: { partitionCount: 2, messageRetentionInDays: 1 }
}]

// Azure Event Hubs Data Receiver for the worker identity
resource ehReceiver 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(eventHubs.id, identity.id, 'eh-receiver')
  scope: eventHubs
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a638d3c7-ab3a-418d-83e6-5f17a39d4fde')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${namePrefix}-env'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

var commonEnv = [
  { name: 'SCHEMAGUARD_DATABASE_URL', secretRef: 'database-url' }
  { name: 'SCHEMAGUARD_LLM_PROVIDER', value: llmProvider }
  { name: 'SCHEMAGUARD_AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
  { name: 'SCHEMAGUARD_AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
  { name: 'SCHEMAGUARD_REGISTRY_URL', value: registryUrl }
  { name: 'AZURE_CLIENT_ID', value: identity.properties.clientId } // DefaultAzureCredential picks the UAMI
  { name: 'SCHEMAGUARD_LOG_LEVEL', value: 'INFO' }
]
var secrets = [
  { name: 'database-url', keyVaultUrl: dbUrlSecret.properties.secretUri, identity: identity.id }
]

resource api 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-api'
  location: location
  tags: tags
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${identity.id}': {} } }
  dependsOn: [acrPull, kvSecretsUser]
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: { external: apiExternalIngress, targetPort: 8000, transport: 'auto', allowInsecure: false }
      registries: [{ server: registry.properties.loginServer, identity: identity.id }]
      secrets: secrets
    }
    template: {
      containers: [{
        name: 'api'
        image: '${registry.properties.loginServer}/schemaguard-api:${imageTag}'
        resources: { cpu: json('0.5'), memory: '1Gi' }
        env: commonEnv
        probes: [{ type: 'Liveness', httpGet: { path: '/health', port: 8000 }, periodSeconds: 30 }]
      }]
      scale: { minReplicas: 0, maxReplicas: 2 }
    }
  }
}

resource worker 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-worker'
  location: location
  tags: tags
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${identity.id}': {} } }
  dependsOn: [acrPull, kvSecretsUser]
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      registries: [{ server: registry.properties.loginServer, identity: identity.id }]
      secrets: secrets
    }
    template: {
      containers: [{
        name: 'worker'
        image: '${registry.properties.loginServer}/schemaguard-worker:${imageTag}'
        resources: { cpu: json('0.5'), memory: '1Gi' }
        env: commonEnv
      }]
      scale: { minReplicas: 1, maxReplicas: 1 } // single poller: avoids duplicate polling races
    }
  }
}

output registryLoginServer string = registry.properties.loginServer
output apiFqdn string = api.properties.configuration.ingress.fqdn
output keyVaultName string = vault.name
output eventHubsKafkaEndpoint string = '${eventHubs.name}.servicebus.windows.net:9093'
output identityClientId string = identity.properties.clientId

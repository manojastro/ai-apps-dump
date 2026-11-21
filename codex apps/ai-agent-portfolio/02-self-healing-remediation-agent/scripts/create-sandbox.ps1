$ErrorActionPreference = 'Stop'
if (-not (Get-Command kind -ErrorAction SilentlyContinue)) { throw 'kind is required: https://kind.sigs.k8s.io/' }
kind create cluster --name selfheal-02 --config (Join-Path $PSScriptRoot '..\infra\kind-config.yaml')
kubectl apply -f (Join-Path $PSScriptRoot '..\infra\k8s\namespace-rbac.yaml')
kubectl apply -f (Join-Path $PSScriptRoot '..\infra\k8s\demo-workloads.yaml')
kubectl wait --for=condition=Available deployment --all -n selfheal-demo --timeout=120s
Write-Host 'Sandbox ready: kind-selfheal-02 / namespace selfheal-demo'

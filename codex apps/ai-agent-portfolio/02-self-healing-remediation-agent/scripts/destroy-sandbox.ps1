$ErrorActionPreference = 'Stop'
if (-not (Get-Command kind -ErrorAction SilentlyContinue)) { throw 'kind is required' }
kind delete cluster --name selfheal-02


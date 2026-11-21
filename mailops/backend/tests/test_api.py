from fastapi.testclient import TestClient
from app.api import create_app
from app.store import Store

def test_api_requires_reviewer_and_approval_version(tmp_path):
    store=Store(str(tmp_path/'api.sqlite')); store.initialize()
    client=TestClient(create_app(store, 'test-secret'))
    assert client.get('/cases').status_code == 401
    headers={'Authorization':'Bearer test-secret'}
    created=client.post('/cases',headers=headers,json={'sender':'vendor@example.test','body':'Invoice INV-2207','message_key':'api-1'})
    assert created.status_code == 201
    case=client.post('/cases/'+created.json()['id']+'/investigate',headers=headers).json()
    assert client.post('/cases/'+case['id']+'/approve',headers=headers,json={'version':case['version']-1}).status_code == 409
    assert client.post('/cases/'+case['id']+'/approve',headers=headers,json={'version':case['version']}).json()['status'] == 'COMPLETED'
    assert client.post('/cases/'+case['id']+'/approve',headers=headers,json={'version':case['version']}).status_code == 409

def test_case_details_and_dashboard_are_real_data(tmp_path):
    store=Store(str(tmp_path/'dashboard.sqlite')); store.initialize()
    client=TestClient(create_app(store, 'secret'))
    h={'Authorization':'Bearer secret'}
    c=client.post('/cases',headers=h,json={'sender':'vendor@example.test','body':'Invoice INV-2207','message_key':'invoice'}).json()
    c=client.post(f"/cases/{c['id']}/investigate",headers=h).json()
    assert client.get('/dashboard',headers=h).json()['pending_approvals']==1
    assert client.get(f"/cases/{c['id']}/outbound",headers=h).status_code==404
    client.post(f"/cases/{c['id']}/approve",headers=h,json={'version':c['version']})
    assert client.get('/dashboard',headers=h).json()['resolved']==1
    assert client.get(f"/cases/{c['id']}/outbound",headers=h).json()['recipient']=='vendor@example.test'
    assert len(client.get(f"/cases/{c['id']}/history",headers=h).json())==3

def test_reporting_returns_tenant_scoped_incoming_and_stored_outbound(tmp_path):
    store=Store(str(tmp_path/'report.sqlite')); store.initialize()
    client=TestClient(create_app(store,'secret')); h={'Authorization':'Bearer secret'}
    assert client.get('/reports/mail').status_code==401
    case=store.intake('demo','vendor@example.test','Invoice INV-2207','report')
    case=store.investigate('demo',case['id']); store.approve('demo',case['id'],'reviewer',case['version'])
    store.intake('other','someone@example.test','Other tenant','other')
    report=client.get('/reports/mail',headers=h).json()
    assert len(report['incoming'])==1 and len(report['outbound'])==1
    assert report['incoming'][0]['case_id']==case['id']
    assert report['outbound'][0]['recipient']=='vendor@example.test'
    assert report['outbound'][0]['recorded_at']
    assert report['outbound'][0]['delivery_status']=='stored_not_sent'

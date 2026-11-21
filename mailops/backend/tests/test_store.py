import pytest
from app.store import Store, Conflict, Denied

@pytest.fixture
def store(tmp_path):
    s = Store(str(tmp_path / 'test.sqlite'))
    s.initialize()
    return s

def test_invoice_approval_is_durable_and_idempotent(store):
    case = store.intake('demo', 'vendor@example.test', 'Invoice INV-2207 is overdue', 'one')
    case = store.investigate('demo', case['id'])
    assert case['decision'] == 'CREATE_PAYMENT_EXCEPTION'
    assert store.count('outbound') == 0
    result = store.approve('demo', case['id'], 'reviewer', case['version'])
    assert result['status'] == 'COMPLETED'
    assert store.count('exceptions') == 1
    assert store.count('outbound') == 1
    with pytest.raises(Conflict):
        store.approve('demo', case['id'], 'reviewer', case['version'])
    assert store.count('exceptions') == 1

def test_order_change_and_unauthorized_sender(store):
    bad = store.intake('demo', 'attacker@example.test', 'Move PO-45821 to 2027-01-15', 'bad')
    bad = store.investigate('demo', bad['id'])
    assert bad['status'] == 'DENIED'
    assert not bad['evidence']
    with pytest.raises(Conflict):
        store.approve('demo', bad['id'], 'reviewer', bad['version'])
    good = store.intake('demo', 'buyer@example.test', 'Move PO-45821 to 2027-01-15', 'good')
    good = store.investigate('demo', good['id'])
    assert good['decision'] == 'CHANGE_DELIVERY'
    store.approve('demo', good['id'], 'reviewer', good['version'])
    assert store.order_date('demo', 'PO-45821') == '2027-01-15'

def test_duplicate_intake_and_tenant_boundary(store):
    one = store.intake('demo', 'vendor@example.test', 'Invoice INV-2207', 'same')
    two = store.intake('demo', 'vendor@example.test', 'Invoice INV-2207', 'same')
    assert one['id'] == two['id']
    with pytest.raises(Denied):
        store.get('other', one['id'])

def test_stale_invoice_cannot_be_approved(store):
    case=store.intake('demo','vendor@example.test','Invoice INV-2207','stale')
    case=store.investigate('demo',case['id'])
    with store.connect() as db:
        db.execute("UPDATE invoices SET amount='1300.00' WHERE tenant='demo' AND number='INV-2207'")
    with pytest.raises(Conflict):
        store.approve('demo',case['id'],'reviewer',case['version'])
    assert store.count('outbound') == 0
    assert store.count('exceptions') == 0

def test_order_changed_after_review_is_rejected(store):
    case=store.intake('demo','buyer@example.test','Move PO-45821 to 2027-01-15','stale-order')
    case=store.investigate('demo',case['id'])
    with store.connect() as db:
        db.execute("UPDATE orders SET version=version+1 WHERE tenant='demo' AND number='PO-45821'")
    with pytest.raises(Conflict):
        store.approve('demo',case['id'],'reviewer',case['version'])
    assert store.count('outbound') == 0

def test_reject_records_event_without_execution(store):
    case=store.intake('demo','vendor@example.test','Invoice INV-2207','reject')
    case=store.investigate('demo',case['id'])
    result=store.reject('demo',case['id'],'reviewer',case['version'],'Need more evidence')
    assert result['status']=='REJECTED'
    assert store.count('outbound')==0
    assert store.history('demo',case['id'])[-1]['kind']=='REJECTED'

def test_request_more_investigation_reopens_case(store):
    case=store.intake('demo','vendor@example.test','Invoice INV-2207','reopen')
    case=store.investigate('demo',case['id'])
    case=store.request_investigation('demo',case['id'],'reviewer',case['version'],'Recheck')
    assert case['status']=='RECEIVED'
    assert store.investigate('demo',case['id'])['status']=='AWAITING_APPROVAL'

def test_order_status_with_date_does_not_change_delivery(store):
    case=store.intake('demo','buyer@example.test','What is the status of PO-45821? It was placed on 2027-01-15.','status')
    result=store.investigate('demo',case['id'])
    assert result['decision']=='RESPOND'

def test_multiple_order_numbers_require_manual_review(store):
    case=store.intake('demo','buyer@example.test','Move PO-45821 and PO-45822 to 2027-01-15','multiple')
    result=store.investigate('demo',case['id'])
    assert result['decision']=='MANUAL_REVIEW'
    assert not result['evidence']

def test_past_date_at_execution_is_rejected(store, monkeypatch):
    case=store.intake('demo','buyer@example.test','Move PO-45821 to 2027-01-15','past-execution')
    case=store.investigate('demo',case['id'])
    import app.store as module
    class LaterDate(module.date):
        @classmethod
        def today(cls): return cls(2027, 1, 16)
    monkeypatch.setattr(module, 'date', LaterDate)
    with pytest.raises(Conflict):
        store.approve('demo',case['id'],'reviewer',case['version'])
    assert store.count('outbound')==0

def test_negated_request_never_changes_order(store):
    case=store.intake('demo','buyer@example.test','Do not move PO-45821 to 2027-01-15','negation')
    assert store.investigate('demo',case['id'])['decision'] != 'CHANGE_DELIVERY'

def test_status_response_stale_order_blocks_outbound(store):
    case=store.intake('demo','buyer@example.test','Status of PO-45821?','status-stale')
    case=store.investigate('demo',case['id'])
    with store.connect() as db:
        db.execute("UPDATE orders SET delivery_date='2027-01-22',version=version+1 WHERE tenant='demo' AND number='PO-45821'")
    with pytest.raises(Conflict):
        store.approve('demo',case['id'],'reviewer',case['version'])
    assert store.count('outbound')==0

def test_pending_approval_survives_store_restart(tmp_path):
    path=str(tmp_path/'restart.sqlite')
    first=Store(path); first.initialize()
    case=first.intake('demo','vendor@example.test','Invoice INV-2207','restart')
    case=first.investigate('demo',case['id'])
    second=Store(path); second.initialize()
    assert second.get('demo',case['id'])['status']=='AWAITING_APPROVAL'
    assert second.approve('demo',case['id'],'reviewer',case['version'])['status']=='COMPLETED'
    assert second.count('outbound')==1

def test_approved_order_response_confirms_only_successful_update(store):
    case=store.intake('demo','buyer@example.test','Move PO-45821 to 2027-01-15','confirm-order')
    case=store.investigate('demo',case['id'])
    assert 'subject to approval' in case['draft']
    store.approve('demo',case['id'],'reviewer',case['version'])
    assert '2027-01-15' in store.outbound('demo',case['id'])['body']
    assert 'has been updated' in store.outbound('demo',case['id'])['body']

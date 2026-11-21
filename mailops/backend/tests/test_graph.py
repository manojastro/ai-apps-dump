from app.graph import run_investigation
from app.store import Store

def test_graph_persists_case_investigation(tmp_path):
    store=Store(str(tmp_path/'store.sqlite')); store.initialize()
    case=store.intake('demo','vendor@example.test','Invoice INV-2207','graph')
    result=run_investigation(store,'demo',case['id'],str(tmp_path/'graph.sqlite'))
    assert result['status']=='AWAITING_APPROVAL'
    assert Store(str(tmp_path/'store.sqlite')).get('demo',case['id'])['decision']=='CREATE_PAYMENT_EXCEPTION'

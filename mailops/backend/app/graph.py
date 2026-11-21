"""Checkpointed investigation wrapper. The case store remains authoritative."""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from .store import Store

class InvestigationState(TypedDict, total=False):
    tenant: str
    case_id: str
    status: str
    decision: str | None

def run_investigation(store: Store, tenant: str, case_id: str, checkpoint_path: str):
    def investigate(state: InvestigationState):
        case=store.get(state['tenant'],state['case_id'])
        if case['status']=='RECEIVED':
            case=store.investigate(state['tenant'],state['case_id'])
        return {'status':case['status'],'decision':case['decision']}
    graph=StateGraph(InvestigationState)
    graph.add_node('investigate',investigate)
    graph.add_edge(START,'investigate'); graph.add_edge('investigate',END)
    with SqliteSaver.from_conn_string(checkpoint_path) as saver:
        app=graph.compile(checkpointer=saver)
        return app.invoke({'tenant':tenant,'case_id':case_id},config={'configurable':{'thread_id':tenant+':'+case_id}})

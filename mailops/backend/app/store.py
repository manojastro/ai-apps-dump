"""Persistent local workflow storage and controlled transactional execution."""
import json
import re
import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

class Conflict(Exception): pass
class Denied(Exception): pass

class Store:
    def __init__(self, path): self.path = path
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db
    def initialize(self):
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, tenant TEXT NOT NULL, sender TEXT NOT NULL, body TEXT NOT NULL, message_key TEXT NOT NULL, status TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 0, decision TEXT, evidence TEXT NOT NULL DEFAULT '[]', draft TEXT, created TEXT NOT NULL, UNIQUE(tenant,message_key));
            CREATE TABLE IF NOT EXISTS invoices (tenant TEXT, number TEXT, contact TEXT NOT NULL, amount TEXT NOT NULL, po_amount TEXT NOT NULL, receipt INTEGER NOT NULL, payment_date TEXT, PRIMARY KEY(tenant,number));
            CREATE TABLE IF NOT EXISTS orders (tenant TEXT, number TEXT, contact TEXT NOT NULL, delivery_date TEXT NOT NULL, inventory INTEGER NOT NULL, dispatched INTEGER NOT NULL, version INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(tenant,number));
            CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id), kind TEXT NOT NULL, detail TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS exceptions (case_id TEXT PRIMARY KEY REFERENCES cases(id), invoice TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS outbound (case_id TEXT PRIMARY KEY REFERENCES cases(id), recipient TEXT NOT NULL, body TEXT NOT NULL);
            ''')
            db.execute('INSERT OR IGNORE INTO invoices VALUES (?,?,?,?,?,?,?)', ('demo','INV-2207','vendor@example.test','1200.00','1000.00',1,None))
            db.execute('INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?,?)', ('demo','PO-45821','buyer@example.test','2027-01-20',10,0,0))
    def event(self, db, case_id, kind, detail):
        db.execute('INSERT INTO events(case_id,kind,detail,created) VALUES (?,?,?,?)', (case_id,kind,json.dumps(detail),datetime.now(timezone.utc).isoformat()))
    def row(self, db, tenant, case_id):
        row=db.execute('SELECT * FROM cases WHERE tenant=? AND id=?',(tenant,case_id)).fetchone()
        if row is None: raise Denied('Case not found')
        result=dict(row); result['evidence']=json.loads(result['evidence']); return result
    def get(self, tenant, case_id):
        with self.connect() as db: return self.row(db,tenant,case_id)
    def list(self, tenant):
        with self.connect() as db:
            ids=db.execute('SELECT id FROM cases WHERE tenant=? ORDER BY created DESC',(tenant,)).fetchall()
            return [self.row(db,tenant,x['id']) for x in ids]
    def intake(self, tenant, sender, body, key):
        if not sender or not body or not key or len(body)>20000 or len(key)>200: raise ValueError('Invalid message')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute('SELECT id,sender,body FROM cases WHERE tenant=? AND message_key=?',(tenant,key)).fetchone()
            if existing:
                if existing['sender'] != sender.lower() or existing['body'] != body: raise Conflict('Idempotency key reused for different message')
                return self.row(db,tenant,existing['id'])
            cid=str(uuid4())
            db.execute('INSERT INTO cases(id,tenant,sender,body,message_key,status,created) VALUES(?,?,?,?,?,?,?)',(cid,tenant,sender.lower(),body,key,'RECEIVED',datetime.now(timezone.utc).isoformat()))
            self.event(db,cid,'RECEIVED',{})
            return self.row(db,tenant,cid)
    def investigate(self, tenant, case_id):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE'); case=self.row(db,tenant,case_id)
            if case['status'] != 'RECEIVED': raise Conflict('Case already processed')
            inv=re.search(r'\bINV-\d+\b',case['body'],re.I); order=re.search(r'\bPO-\d+\b',case['body'],re.I)
            evidence=[]; decision=None; draft=None; status='NEEDS_REVIEW'
            identifiers=re.findall(r'\b(?:INV|PO)-\d+\b',case['body'],re.I)
            if bool(inv) == bool(order) or len(identifiers) != 1:
                decision='MANUAL_REVIEW'; draft='We need additional information to identify your request.'
            else:
                table='invoices' if inv else 'orders'; number=(inv or order).group().upper()
                record=db.execute(f'SELECT * FROM {table} WHERE tenant=? AND number=?',(tenant,number)).fetchone()
                if record is None or record['contact'] != case['sender']:
                    status='DENIED'; decision='DENY'; draft=None
                elif inv:
                    record=dict(record); evidence=[{'source':'invoice','record':number,'amount':record['amount'],'purchase_order_amount':record['po_amount'],'goods_received':bool(record['receipt']),'payment_date':record['payment_date']}]
                    mismatch=Decimal(record['amount']) != Decimal(record['po_amount']) or not record['receipt']
                    decision='CREATE_PAYMENT_EXCEPTION' if mismatch else 'RESPOND'
                    draft=('We found a discrepancy that requires review. ' if mismatch else 'The invoice is matched. ') + ('The confirmed payment date is '+record['payment_date']+'.' if record['payment_date'] else 'The payment date is unconfirmed.')
                    status='AWAITING_APPROVAL'
                else:
                    record=dict(record); evidence=[{'source':'order','record':number,'delivery_date':record['delivery_date'],'inventory':record['inventory'],'dispatched':bool(record['dispatched']),'version':record['version']}]
                    requested=re.search(r'\b\d{4}-\d{2}-\d{2}\b',case['body'])
                    try: requested_date=date.fromisoformat(requested.group()) if requested else None
                    except ValueError: requested_date=None
                    change_requested=bool(re.search(r'\b(move|change|reschedule|shift)\b',case['body'],re.I)) and not re.search(r"\b(?:not|never|don't|dont|cancel)\b",case['body'],re.I)
                    feasible=bool(change_requested and requested_date and requested_date > date.today() and record['inventory'] > 0 and not record['dispatched'])
                    decision='CHANGE_DELIVERY' if feasible else 'RESPOND'
                    if feasible:
                        evidence.append({'source':'requested_date','value':requested_date.isoformat()})
                        draft=f'We can request delivery on {requested_date.isoformat()}, subject to approval.'
                    else: draft='We cannot confirm the requested delivery change; a reviewer will investigate.'
                    status='AWAITING_APPROVAL'
            db.execute('UPDATE cases SET status=?, decision=?, evidence=?, draft=?, version=version+1 WHERE id=?',(status,decision,json.dumps(evidence),draft,case_id))
            self.event(db,case_id,'INVESTIGATED',{'decision':decision,'status':status})
            return self.row(db,tenant,case_id)
    def approve(self, tenant, case_id, reviewer, version):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE'); case=self.row(db,tenant,case_id)
            if case['status'] != 'AWAITING_APPROVAL' or case['version'] != version: raise Conflict('Approval is stale or unavailable')
            if case['evidence'] and case['evidence'][0]['source']=='invoice':
                ev=case['evidence'][0]
                current=db.execute('SELECT * FROM invoices WHERE tenant=? AND number=?',(tenant,ev['record'])).fetchone()
                if (current is None or current['contact'] != case['sender'] or
                    current['amount'] != ev['amount'] or current['po_amount'] != ev['purchase_order_amount'] or
                    bool(current['receipt']) != ev['goods_received'] or current['payment_date'] != ev['payment_date']):
                    raise Conflict('Invoice changed since investigation')
            if case['evidence'] and case['evidence'][0]['source']=='order':
                ev=case['evidence'][0]
                current=db.execute('SELECT * FROM orders WHERE tenant=? AND number=?',(tenant,ev['record'])).fetchone()
                if (current is None or current['contact'] != case['sender'] or current['version'] != ev['version'] or
                    current['delivery_date'] != ev['delivery_date'] or current['inventory'] != ev['inventory'] or
                    bool(current['dispatched']) != ev['dispatched']):
                    raise Conflict('Order changed since investigation')
            outbound_body=case['draft']
            if case['decision']=='CREATE_PAYMENT_EXCEPTION':
                db.execute('INSERT INTO exceptions VALUES (?,?)',(case_id,case['evidence'][0]['record']))
            elif case['decision']=='CHANGE_DELIVERY':
                ev=case['evidence'][0]; target=case['evidence'][1]['value']
                if date.fromisoformat(target) <= date.today(): raise Conflict('Requested date has passed')
                changed=db.execute('UPDATE orders SET delivery_date=?,version=version+1 WHERE tenant=? AND number=? AND version=? AND dispatched=0 AND inventory>0',(target,tenant,ev['record'],ev['version'])).rowcount
                if changed != 1: raise Conflict('Order changed since investigation')
                outbound_body=f'The delivery date for {ev["record"]} has been updated to {target} in our order system.'
            db.execute('INSERT INTO outbound VALUES (?,?,?)',(case_id,case['sender'],outbound_body))
            db.execute("UPDATE cases SET status='COMPLETED',version=version+1 WHERE id=?",(case_id,))
            self.event(db,case_id,'APPROVED_AND_EXECUTED',{'reviewer':reviewer,'decision':case['decision']})
            return self.row(db,tenant,case_id)
    def count(self, table):
        if table not in ('outbound','exceptions'): raise ValueError('Invalid table')
        with self.connect() as db: return db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    def order_date(self,tenant,number):
        with self.connect() as db: return db.execute('SELECT delivery_date FROM orders WHERE tenant=? AND number=?',(tenant,number)).fetchone()[0]
    def history(self, tenant, case_id):
        with self.connect() as db:
            self.row(db,tenant,case_id)
            return [dict(row) for row in db.execute('SELECT kind,detail,created FROM events WHERE case_id=? ORDER BY id',(case_id,))]
    def review_transition(self, tenant, case_id, reviewer, version, reason, status, event):
        if not reason or len(reason)>2000: raise ValueError('Reason is required')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE'); case=self.row(db,tenant,case_id)
            if case['status'] != 'AWAITING_APPROVAL' or case['version'] != version: raise Conflict('Approval is stale or unavailable')
            db.execute('UPDATE cases SET status=?,version=version+1 WHERE id=?',(status,case_id))
            self.event(db,case_id,event,{'reviewer':reviewer,'reason':reason})
            return self.row(db,tenant,case_id)
    def reject(self, tenant, case_id, reviewer, version, reason):
        return self.review_transition(tenant,case_id,reviewer,version,reason,'REJECTED','REJECTED')
    def request_investigation(self, tenant, case_id, reviewer, version, reason):
        return self.review_transition(tenant,case_id,reviewer,version,reason,'RECEIVED','INVESTIGATION_REQUESTED')
    def dashboard(self, tenant):
        with self.connect() as db:
            rows=db.execute('SELECT status, COUNT(*) AS n FROM cases WHERE tenant=? GROUP BY status',(tenant,)).fetchall()
            counts={row['status']:row['n'] for row in rows}
            return {'incoming':sum(counts.values()), 'pending_approvals':counts.get('AWAITING_APPROVAL',0), 'resolved':counts.get('COMPLETED',0), 'needs_review':counts.get('NEEDS_REVIEW',0), 'denied':counts.get('DENIED',0)}
    def outbound(self, tenant, case_id):
        with self.connect() as db:
            self.row(db,tenant,case_id)
            row=db.execute('SELECT recipient,body FROM outbound WHERE case_id=?',(case_id,)).fetchone()
            if row is None: raise Denied('Outbound message not found')
            return dict(row)
    def mail_report(self, tenant):
        """Return records from the local case and outbound stores, scoped to tenant."""
        with self.connect() as db:
            incoming=[dict(row) for row in db.execute('SELECT id AS case_id,sender,body,status,decision,created AS recorded_at FROM cases WHERE tenant=? ORDER BY created DESC',(tenant,))]
            outbound=[dict(row) for row in db.execute("""SELECT c.id AS case_id,o.recipient,o.body,c.status,
                (SELECT MAX(e.created) FROM events e WHERE e.case_id=c.id AND e.kind='APPROVED_AND_EXECUTED') AS recorded_at
                FROM outbound o JOIN cases c ON c.id=o.case_id WHERE c.tenant=? ORDER BY recorded_at DESC""",(tenant,))]
            for item in outbound: item['delivery_status']='stored_not_sent'
            return {'incoming':incoming,'outbound':outbound}

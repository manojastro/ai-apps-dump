"""Authenticated local API. Configure an explicit secret before use."""
import hmac
import os
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from .store import Store, Conflict, Denied

class Message(BaseModel):
    sender: str = Field(min_length=3, max_length=320)
    body: str = Field(min_length=1, max_length=20000)
    message_key: str = Field(min_length=1, max_length=200)

class Approval(BaseModel):
    version: int = Field(ge=0)

class Review(Approval):
    reason: str = Field(min_length=1, max_length=2000)

def create_app(store: Store, secret: str) -> FastAPI:
    if not secret: raise ValueError('MAILOPS_REVIEWER_TOKEN must be configured')
    app=FastAPI(title='MailOps AI local API')
    def reviewer(authorization: str = Header(default='')):
        expected='Bearer '+secret
        if not hmac.compare_digest(authorization,expected):
            raise HTTPException(401,'Authentication required',headers={'WWW-Authenticate':'Bearer'})
        return 'local-reviewer'
    @app.exception_handler(Conflict)
    async def conflict_handler(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=409,content={'detail':str(exc)})
    @app.exception_handler(Denied)
    async def denied_handler(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404,content={'detail':'Case not found'})
    @app.get('/health')
    def health(): return {'status':'ok','provider':'deterministic offline'}
    @app.get('/reports/mail')
    def mail_report(user=Depends(reviewer)): return store.mail_report('demo')
    @app.get('/dashboard')
    def dashboard(user=Depends(reviewer)): return store.dashboard('demo')
    @app.get('/cases')
    def cases(user=Depends(reviewer)): return store.list('demo')
    @app.post('/cases',status_code=201)
    def intake(message: Message,user=Depends(reviewer)):
        return store.intake('demo',message.sender,message.body,message.message_key)
    @app.get('/cases/{case_id}')
    def get_case(case_id: str,user=Depends(reviewer)): return store.get('demo',case_id)
    @app.post('/cases/{case_id}/investigate')
    def investigate(case_id: str,user=Depends(reviewer)): return store.investigate('demo',case_id)
    @app.post('/cases/{case_id}/approve')
    def approve(case_id: str,approval: Approval,user=Depends(reviewer)):
        return store.approve('demo',case_id,user,approval.version)
    @app.get('/cases/{case_id}/outbound')
    def outbound(case_id: str,user=Depends(reviewer)): return store.outbound('demo',case_id)
    @app.get('/cases/{case_id}/history')
    def history(case_id: str,user=Depends(reviewer)): return store.history('demo',case_id)
    @app.post('/cases/{case_id}/reject')
    def reject(case_id: str,review: Review,user=Depends(reviewer)):
        return store.reject('demo',case_id,user,review.version,review.reason)
    @app.post('/cases/{case_id}/reinvestigate')
    def reinvestigate(case_id: str,review: Review,user=Depends(reviewer)):
        return store.request_investigation('demo',case_id,user,review.version,review.reason)
    return app

def app_factory():
    store=Store(os.environ.get('MAILOPS_DB','mailops.sqlite3'))
    store.initialize()
    return create_app(store,os.environ.get('MAILOPS_REVIEWER_TOKEN',''))

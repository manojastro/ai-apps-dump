"""Read-only local ERP MCP server; identity is fixed by the launching process.

This is a demo adapter, not a network authentication mechanism. Never expose it
without binding process identity to an authenticated integration principal.
"""
import os
from mcp.server.fastmcp import FastMCP
from .store import Store

mcp=FastMCP('MailOps local ERP')

def read_record(table: str, number: str) -> dict:
    path=os.environ.get('MAILOPS_DB'); tenant=os.environ.get('MAILOPS_TENANT'); principal=os.environ.get('MAILOPS_PRINCIPAL')
    if not path or not tenant or not principal: raise ValueError('Integration principal is not configured')
    with Store(path).connect() as db:
        row=db.execute(f'SELECT * FROM {table} WHERE tenant=? AND number=? AND contact=?',(tenant,number,principal.lower())).fetchone()
        if row is None: return {'status':'unavailable'}
        record=dict(row); record.pop('contact',None); record.pop('tenant',None)
        return {'status':'ok','source':table,'record':record}

@mcp.tool()
def get_invoice(number: str) -> dict:
    """Retrieve an invoice authorized for this integration principal."""
    return read_record('invoices',number)

@mcp.tool()
def get_order(number: str) -> dict:
    """Retrieve an order authorized for this integration principal."""
    return read_record('orders',number)

if __name__=='__main__': mcp.run(transport='stdio')

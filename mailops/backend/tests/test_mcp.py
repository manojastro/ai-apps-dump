import os
import sys
import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.store import Store

def test_real_mcp_server_restricts_record_access(tmp_path):
    path=str(tmp_path/'enterprise.sqlite'); Store(path).initialize()
    async def exercise():
        env=dict(os.environ,MAILOPS_DB=path,MAILOPS_TENANT='demo',MAILOPS_PRINCIPAL='vendor@example.test')
        server=StdioServerParameters(command=sys.executable,args=['-m','app.erp_mcp'],env=env)
        async with stdio_client(server) as (reader,writer):
            async with ClientSession(reader,writer) as session:
                await session.initialize()
                names={tool.name for tool in (await session.list_tools()).tools}
                assert 'get_invoice' in names
                allowed=await session.call_tool('get_invoice',{'number':'INV-2207'})
                assert not allowed.isError and '1200.00' in str(allowed.content)
                denied=await session.call_tool('get_order',{'number':'PO-45821'})
                assert '45821' not in str(denied.content)
    anyio.run(exercise)

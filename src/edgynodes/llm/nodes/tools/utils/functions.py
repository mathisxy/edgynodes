from datetime import timedelta
from typing import Any
import fastmcp
import llmir

class MCPToolFunction:

    tool: llmir.Tool
    client: fastmcp.Client[Any]
    timeout: timedelta | float | int | None
    progress_handler: fastmcp.client.client.ProgressHandler | None
    raise_on_error: bool
    meta: dict[str, Any] | None

    def __init__(self, 
                 tool: llmir.Tool, 
                 client: fastmcp.Client[Any], 
                 timeout: timedelta | float | int | None = None,
                 progress_handler: fastmcp.client.client.ProgressHandler | None = None,
                 raise_on_error: bool = True,
                 meta: dict[str, Any] | None = None,
        ) -> None:
        self.tool = tool
        self.client = client
        self.timeout = timeout
        self.progress_handler = progress_handler
        self.raise_on_error = raise_on_error
        self.meta = meta



    async def __call__(self, **kwargs: Any) -> fastmcp.client.client.CallToolResult:
        
        async with self.client:

            return await self.client.call_tool(
                self.tool.name, 
                kwargs, 
                timeout=self.timeout, 
                progress_handler=self.progress_handler, 
                raise_on_error=self.raise_on_error, 
                meta=self.meta
            )
"""McpProcessManager — on-demand subprocess lifecycle for MCP servers."""

import asyncio
import logging
import os

logger = logging.getLogger(__name__)


class McpProcessManager:
    """Manages MCP server subprocesses. Start on-demand, shut down cleanly."""

    def __init__(self) -> None:
        # server_id -> asyncio.subprocess.Process
        self._processes: dict[int, asyncio.subprocess.Process] = {}

    async def start(
        self,
        server_id: int,
        command: str,
        args: list[str],
        env_vars: dict[str, str],
    ) -> None:
        """Start an MCP server subprocess if not already running."""
        if self.is_running(server_id):
            return
        env = {**os.environ, **env_vars}
        proc = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        self._processes[server_id] = proc
        logger.info("Started MCP server %s (pid=%s)", server_id, proc.pid)

    async def stop(self, server_id: int) -> None:
        """Stop a running MCP server: close stdin -> SIGTERM -> SIGKILL after 5s."""
        proc = self._processes.pop(server_id, None)
        if proc is None or proc.returncode is not None:
            return
        try:
            if proc.stdin:
                proc.stdin.close()
            proc.terminate()  # SIGTERM
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except TimeoutError:
                proc.kill()  # SIGKILL
                await proc.wait()
        except ProcessLookupError:
            pass
        logger.info("Stopped MCP server %s", server_id)

    def is_running(self, server_id: int) -> bool:
        """Check if a server subprocess is currently running."""
        proc = self._processes.get(server_id)
        return proc is not None and proc.returncode is None

    async def stop_all(self) -> None:
        """Stop all running MCP servers (called on app shutdown)."""
        for server_id in list(self._processes):
            await self.stop(server_id)

    async def cleanup_orphans(self) -> None:
        """No-op on startup -- processes dict is empty at cold start.

        Implement PGID-based cleanup here if needed in future.
        """

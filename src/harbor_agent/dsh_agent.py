
from __future__ import annotations

import json
import shlex
import time
from pathlib import Path
from typing import Any, ClassVar

from pydantic import Field

from harbor.agents.base import BaseAgent
from harbor.agents.options import AgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


DSH_RUNTIME_VERSION = "0.2.2-rc.1"
ADAPTER_VERSION = "0.1.1"


class DSHAgentOptions(AgentOptions):
    """Options exposed by the Harbor DSH adapter."""

    timeout_sec: int = Field(
        default=540,
        ge=1,
        le=3600,
        description="Maximum DSH execution time in seconds.",
    )


class DSHAgent(BaseAgent):
    """Run DeepSeek Harness through its Headless CLI."""

    options_model: ClassVar[type[AgentOptions] | None] = DSHAgentOptions

    @staticmethod
    def name() -> str:
        return "dsh-headless"

    def version(self) -> str:
        return ADAPTER_VERSION

    def _runtime_env(self) -> dict[str, str]:
        """Forward only explicitly configured variables and required credentials."""

        env = {
            "HOME": "/root",
            "DSH_HOME": "/root/.dsh",
        }

        env.update(self.extra_env)

        # Headless uses launch-time API credentials.
        for key in ("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL"):
            if key not in env:
                value = self._get_env(key)
                if value is not None:
                    env[key] = value

        return env

    def _write_log(self, filename: str, content: str) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / filename).write_text(
            content,
            encoding="utf-8",
        )

    @staticmethod
    def _parse_events(stdout: str) -> dict[str, Any]:
        """Extract structured events while preserving non-JSON diagnostics."""

        counts: dict[str, int] = {}
        usage_events = []
        errors = []

        stdout_diagnostics = []
        malformed_details = []

        session_id = None
        final_reason = None
        final_text_chars = None

        diagnostic_prefix = (
            "[llm-deepseek-api-key]"
        )

        for line_no, line in enumerate(stdout.splitlines(), 1):
            if not line.strip():
                continue

            try:
                event = json.loads(line)

            except json.JSONDecodeError as exc:
                # Known provider initialization log.
                if line.strip().startswith(diagnostic_prefix):
                    stdout_diagnostics.append(line)
                else:
                    malformed_details.append({
                        "line": line_no,
                        "content": line,
                        "reason": str(exc),
                    })
                continue

            if not isinstance(event, dict):
                malformed_details.append({
                    "line": line_no,
                    "content": line,
                    "reason": "JSON value is not an object",
                })
                continue

            event_type = event.get("type")

            if not isinstance(event_type, str):
                malformed_details.append({
                    "line": line_no,
                    "content": line,
                    "reason": "Missing or invalid event type",
                })
                continue

            counts[event_type] = counts.get(event_type, 0) + 1

            if event_type == "session":
                value = event.get("sessionId")
                if isinstance(value, str):
                    session_id = value

            elif event_type == "final":
                final_reason = event.get("reason")
                final_text = event.get("text")

                if isinstance(final_text, str):
                    final_text_chars = len(final_text)

            elif event_type == "error":
                message = event.get("message")
                if isinstance(message, str):
                    errors.append(message)

            elif (
                    event_type == "status"
                    and event.get("phase") == "step_end"
                    and isinstance(event.get("usage"), dict)
            ):
                usage_events.append(event["usage"])

        return {
            "session_id": session_id,
            "final_reason": final_reason,
            "final_text_chars": final_text_chars,
            "event_counts": counts,
            "usage_events": usage_events,
            "error_events": errors,
            "stdout_diagnostics": stdout_diagnostics,
            "malformed_stdout_lines": len(malformed_details),
            "malformed_details": malformed_details,
        }

    async def setup(self, environment: BaseEnvironment) -> None:
        """Validate the DSH runtime inside the task container."""

        command = (
            "set -eu; "
            "mkdir -p /app /root/.dsh; "
            'actual="$(dsh --version)"; '
            'printf "%s\\n" "$actual"; '
            f"test \"$actual\" = {shlex.quote(DSH_RUNTIME_VERSION)}; "
            'help="$(dsh --profile headless --help 2>&1)"; '
            'printf "%s\\n" "$help" | grep -q -- "--json"'
        )

        result = await environment.exec(
            command=command,
            cwd="/app",
            env=self._runtime_env(),
            timeout_sec=60,
        )

        self._write_log(
            "dsh-setup-stdout.txt",
            result.stdout or "",
        )
        self._write_log(
            "dsh-setup-stderr.txt",
            result.stderr or "",
        )

        if result.return_code != 0:
            details = result.stderr or result.stdout or "no output"
            raise RuntimeError(
                f"DSH runtime preflight failed "
                f"(exit={result.return_code}): {details}"
            )

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Execute one task using DSH Headless."""

        if not instruction.strip():
            raise ValueError("Harbor supplied an empty task instruction")

        options = self.options or DSHAgentOptions()
        timeout_sec = options.timeout_sec

        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Preserve the original instruction in Harbor's host-side logs.
        instruction_host_path = self.logs_dir / "instruction.md"
        instruction_host_path.write_text(
            instruction,
            encoding="utf-8",
        )


        # Reconstruct the instruction inside the Docker environment.
        instruction_runtime_path = "/tmp/dsh-instruction.md"
        await environment.upload_file(
            source_path=instruction_host_path,
            target_path=instruction_runtime_path,
        )

        command = (
            "set -eu; "
            "input=/tmp/dsh-instruction.md; "
            "trap 'rm -f \"$input\"' EXIT; "
            "test -s \"$input\"; "
            "dsh --profile headless "
            "--json "
            "--permission-mode workspace-write "
            "--approval-policy never "
            "- < \"$input\""
        )

        started = time.monotonic()

        try:
            await environment.upload_file(
                source_path=instruction_host_path,
                target_path=instruction_runtime_path,
            )
            result = await environment.exec(
                command=command,
                cwd="/app",
                env=self._runtime_env(),
                timeout_sec=timeout_sec,
            )

        except Exception as exc:
            self._write_log(
                "dsh-execution-error.txt",
                repr(exc) + "\n",
            )

            metadata = dict(context.metadata or {})
            metadata["dsh"] = {
                "adapter_version": ADAPTER_VERSION,
                "runtime_version": DSH_RUNTIME_VERSION,
                "execution_error": repr(exc),
            }
            context.metadata = metadata
            raise

        elapsed_sec = round(time.monotonic() - started, 3)

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        # Preserve the bounded DSH JSONL event projection.
        self._write_log("dsh-events.jsonl", stdout)
        self._write_log("dsh-stderr.txt", stderr)
        self._write_log("dsh-command.txt", command + "\n")

        event_summary = self._parse_events(stdout)

        summary = {
            "adapter_version": ADAPTER_VERSION,
            "runtime_version": DSH_RUNTIME_VERSION,
            "profile": "headless",
            "workdir": "/app",
            "process_return_code": result.return_code,
            "elapsed_sec": elapsed_sec,
            **event_summary,
            "stdout_file": "dsh-events.jsonl",
            "stderr_file": "dsh-stderr.txt",
        }

        self._write_log(
            "dsh-execution.json",
            json.dumps(
                summary,
                ensure_ascii=False,
                indent=2,
            ) + "\n",
        )

        metadata = dict(context.metadata or {})
        metadata["dsh"] = summary
        context.metadata = metadata

        if result.return_code != 0:
            self.logger.warning(
                "DSH exited with code %s; "
                "Harbor verifier will assess the task output.",
                result.return_code,
            )


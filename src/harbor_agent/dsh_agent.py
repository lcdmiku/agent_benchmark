from __future__ import annotations

import json
import shlex
import time
from pathlib import Path
from typing import Any, ClassVar

from pydantic import Field

from harbor.agents.installed.base import BaseInstalledAgent
from harbor.agents.options import InstalledAgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


DSH_RUNTIME_VERSION = "0.2.2-rc.1"
ADAPTER_VERSION = "0.1.2"

NVM_VERSION = "v0.40.2"
DSH_NODE_MAJOR = 24


class DSHAgentOptions(InstalledAgentOptions):
    version: str | None = Field(
        default=DSH_RUNTIME_VERSION,
        description="DSH CLI version to install.",
    )

    timeout_sec: int = Field(
        default=540,
        ge=1,
        le=3600,
        description="Maximum DSH execution time in seconds.",
    )


class DSHAgent(BaseInstalledAgent):
    """Run DeepSeek Harness through its Headless CLI."""

    options_model: ClassVar[type[InstalledAgentOptions] | None] = (
        DSHAgentOptions
    )
    options: DSHAgentOptions

    @staticmethod
    def name() -> str:
        return "dsh-headless"

    def _runtime_env(self) -> dict[str, str]:
        """Forward explicitly configured variables and credentials."""

        env = {
            "HOME": "/root",
            "DSH_HOME": "/root/.dsh",
        }

        env.update(self.extra_env)

        # Preserve existing DeepSeek configuration.
        for key in (
                "DEEPSEEK_API_KEY",
                "DEEPSEEK_BASE_URL",
        ):
            if key not in env:
                value = self._get_env(key)
                if value is not None:
                    env[key] = value

        # Support both the project-specific name and
        # Alibaba's conventional environment variable.
        bailian_key = self._get_env(
            "BAILIAN_API_KEY",
            "DASHSCOPE_API_KEY",
        )

        if bailian_key is not None:
            env["BAILIAN_API_KEY"] = bailian_key

        return env


    def get_version_command(self) -> str | None:
        """Detect DSH version in non-interactive shells."""
        return (
            'export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"; '
            'if [ -s "$NVM_DIR/nvm.sh" ]; then '
            '. "$NVM_DIR/nvm.sh"; '
            "fi; "
            "dsh --version"
        )

    async def install(self, environment: BaseEnvironment) -> None:
        """Install Node.js and the requested DSH CLI version."""

        await self.ensure_system_dependencies(
            environment,
            ("curl", "ca_certificates"),
        )

        version = self._version or "latest"
        if self._version == "latest":
            self._version = None
        package_spec = f"@deepseek-ai/dsh@{version}"

        version_check = ""
        if self._version and self._version != "latest":
            version_check = (
                f'test "$actual" = {shlex.quote(self._version)}; '
            )

        command = (
            "set -euo pipefail; "

            # Install NVM.
            f"curl -fsSL "
            f"https://raw.githubusercontent.com/nvm-sh/nvm/"
            f"{NVM_VERSION}/install.sh "
            "| env -u NODE_VERSION bash; "

            # Load NVM in this non-interactive shell.
            'export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"; '
            'test -s "$NVM_DIR/nvm.sh"; '
            '. "$NVM_DIR/nvm.sh"; '

            # Install Node.js.
            f"nvm install {DSH_NODE_MAJOR}; "
            f"nvm alias default {DSH_NODE_MAJOR}; "

            # Validate the Node.js engine requirement.
            "node -e 'const [major, minor] = "
            "process.versions.node.split(\".\").map(Number); "
            "if (!((major === 22 && minor >= 19) || major >= 24)) "
            "process.exit(1)'; "

            # Install DSH.
            "npm install --global "
            "--no-audit --no-fund "
            "--fetch-retries=5 "
            '--allow-scripts=@deepseek-ai/dsh-subprocess-local,koffi,node-pty,@google/genai,protobufjs \
             @deepseek-ai/dsh@0.2.2-rc.1 '
            f"{shlex.quote(package_spec)}; "

            # Verify installation.
            'actual="$(dsh --version)"; '
            'printf "Installed DSH version: %s\\n" "$actual"; '

            f"{version_check}"

            # Verify Headless JSON support.
            'help="$(dsh --profile headless --help 2>&1)"; '
            'printf "%s\\n" "$help" | grep -q -- "--json"; '
            'printf "Node.js: %s\n" "$(node --version)"; '
            'printf "npm: %s\n" "$(npm --version)"; '
            'printf "DSH: %s\n" "$actual"; '
        )

        self._write_log("dsh-install-command.txt", command + "\n")

        try:
            result = await environment.exec(
                command=command,
                cwd="/app",
                env=self._runtime_env(),
                timeout_sec=300,
            )
        except Exception as exc:
            self._write_log(
                "dsh-install-error.txt",
                repr(exc) + "\n",
            )
            raise

        self._write_log(
            "dsh-install-stdout.txt",
            result.stdout or "",
        )
        self._write_log(
            "dsh-install-stderr.txt",
            result.stderr or "",
        )

        if result.return_code != 0:
            details = result.stderr or result.stdout or "no output"
            raise RuntimeError(
                f"DSH installation failed "
                f"(exit={result.return_code}): {details}"
            )

        # Provision Bailian configuration for the headless profile.
        runtime_env = self._runtime_env()

        if not runtime_env.get("BAILIAN_API_KEY"):
            raise RuntimeError(
                "Missing BAILIAN_API_KEY. "
                "Set BAILIAN_API_KEY or DASHSCOPE_API_KEY."
            )

        config_source = Path(__file__).with_name(
            "dsh-headless-bailian.cordis.patch.yml"
        )

        if not config_source.is_file():
            raise FileNotFoundError(
                f"Missing DSH provider config: {config_source}"
            )

        profile_dir = "/root/.dsh/profiles/headless"
        config_target = f"{profile_dir}/cordis.patch.yml"

        # Create profile directory.
        mkdir_result = await environment.exec(
            command=f"mkdir -p {shlex.quote(profile_dir)}",
            cwd="/app",
            env=runtime_env,
            timeout_sec=30,
        )

        if mkdir_result.return_code != 0:
            raise RuntimeError(
                "Failed to create DSH profile directory: "
                + (mkdir_result.stderr or mkdir_result.stdout or "")
            )

        # Upload provider configuration.
        await environment.upload_file(
            source_path=config_source,
            target_path=config_target,
        )

        # Verify configuration.
        verify_result = await environment.exec(
            command=(
                "set -eu; "
                f"test -s {shlex.quote(config_target)}; "
                f"grep -q 'id: llm-pi-ai' {shlex.quote(config_target)}; "
                f"grep -q 'qwen3.8-max' {shlex.quote(config_target)}"
            ),
            cwd="/app",
            env=runtime_env,
            timeout_sec=30,
        )

        if verify_result.return_code != 0:
            raise RuntimeError(
                "Bailian profile configuration verification failed: "
                + (verify_result.stderr or verify_result.stdout or "")
            )

        self.logger.info(
            "DSH Bailian profile configured: qwen3.8-max"
        )


    # def version(self) -> str:
    #     return ADAPTER_VERSION


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

        command = (
            "set -eu; "

            # Load NVM.
            'export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"; '
            'test -s "$NVM_DIR/nvm.sh"; '
            '. "$NVM_DIR/nvm.sh"; '

            # Initialize DSH.
            'export DSH_HOME="${DSH_HOME:-$HOME/.dsh}"; '
            'mkdir -p "$DSH_HOME"; '

            # Instruction lifecycle.
            "input=/tmp/dsh-instruction.md; "
            "trap 'rm -f \"$input\"' EXIT; "
            'test -s "$input"; '

            # Execute DSH Headless.
            "dsh --profile headless "
            "--json "
            "--permission-mode workspace-write "
            "--approval-policy never "
            '- < "$input"'
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
                "runtime_version": self.version(),
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
            "runtime_version": self.version(),
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


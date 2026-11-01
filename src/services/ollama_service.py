import json
from typing import Dict, Generator, List, Optional
import requests
import yaml

class OllamaService:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.base_url = "http://127.0.0.1:11434"
        self.default_model = "llama3.2:latest"
        self.temperature = 0.2
        self.system_prompt = (
            "You are an expert Root Cause Analysis (RCA) and SRE troubleshooting engineer. "
            "Analyze the provided log context, error patterns, and knowledge base solutions. "
            "Provide concise, actionable explanations of root causes, impact assessments, "
            "and step-by-step remediation commands and fixes."
        )
        self._load_config()

    def _load_config(self):
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f) or {}
                ollama_cfg = config.get("ollama", {})
                self.base_url = ollama_cfg.get("base_url", self.base_url).rstrip("/")
                self.default_model = ollama_cfg.get("default_model", self.default_model)
                self.temperature = float(ollama_cfg.get("temperature", self.temperature))
                if "system_prompt" in ollama_cfg and ollama_cfg["system_prompt"]:
                    self.system_prompt = str(ollama_cfg["system_prompt"]).strip()
        except Exception:
            pass

    def check_connection(self) -> tuple[bool, str]:
        """Check if Ollama server is reachable"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                return True, "Ollama service is online"
            return False, f"Ollama returned HTTP status {resp.status_code}"
        except Exception as e:
            return False, f"Could not reach Ollama at {self.base_url}: {str(e)}"

    def get_available_models(self) -> List[str]:
        """Retrieve list of locally installed models from Ollama"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", []) if "name" in m]
                if models:
                    return models
        except Exception:
            pass
        return [self.default_model]

    def build_system_message(self, context: Optional[str] = None) -> Dict[str, str]:
        """Build the system message with optional incident/log context"""
        content = self.system_prompt
        if context and context.strip():
            content += (
                "\n\n========================================\n"
                "INCIDENT AND LOG CONTEXT:\n"
                "========================================\n"
                f"{context.strip()}\n"
                "========================================\n"
                "Please use the above context to answer the user's questions, perform RCA, "
                "or suggest remediation commands."
            )
        return {"role": "system", "content": content}

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        context: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Generator[str, None, None]:
        """Stream chat completions from Ollama"""
        selected_model = model or self.default_model
        temp = temperature if temperature is not None else self.temperature

        full_messages = [self.build_system_message(context)]
        for msg in messages:
            if msg.get("role") in ("user", "assistant"):
                full_messages.append({"role": msg["role"], "content": msg["content"]})

        payload = {
            "model": selected_model,
            "messages": full_messages,
            "stream": True,
            "options": {"temperature": temp},
        }

        try:
            with requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=60,
            ) as resp:
                if resp.status_code != 200:
                    yield f"Error from Ollama ({resp.status_code}): {resp.text}"
                    return

                for line in resp.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode("utf-8"))
                            msg = chunk.get("message", {})
                            content = msg.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue
        except Exception as e:
            yield f"\n\n[Connection Error: Failed to communicate with Ollama: {str(e)}]"

    @staticmethod
    def format_analysis_context(
        results: Dict,
        log_data: Optional[Dict] = None,
        zone: str = "",
        client: str = "",
        app: str = "",
        version: str = "",
        query: str = "",
    ) -> str:
        """Helper to create a structured context string from RCA results"""
        sections = []

        if zone or client or app:
            sections.append(f"Target Environment: Zone={zone}, Client={client}, App={app}, Version={version}")

        if query:
            sections.append(f"User Troubleshooting Query: {query}")

        stats = results.get("log_stats", {})
        if stats:
            sections.append(
                f"Log Statistics: Total Errors={stats.get('total_errors', 'N/A')}, "
                f"Files Analyzed={stats.get('file_count', 'N/A')}, "
                f"Components={stats.get('unique_components', 'N/A')}"
            )

        exact_matches = results.get("exact_matches", [])
        similar_errors = results.get("similar_errors", [])
        matched_errors = exact_matches if exact_matches else similar_errors
        if matched_errors:
            error_sample = "\n".join(f"- {line}" for line in matched_errors[:8])
            sections.append(f"Relevant Error Lines:\n{error_sample}")

        solutions = results.get("solutions", [])
        if solutions:
            sol_texts = []
            for sol in solutions[:3]:
                title = sol.get("error", "Issue")
                steps = sol.get("solution", "")
                sol_texts.append(f"### {title}\n{steps}")
            sections.append(f"Knowledge Base Recommendations:\n" + "\n\n".join(sol_texts))

        if log_data and "raw" in log_data:
            raw_snippet = log_data["raw"][:1500]
            sections.append(f"Raw Log Excerpt (First 1500 chars):\n{raw_snippet}")

        return "\n\n".join(sections)

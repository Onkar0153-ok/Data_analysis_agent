"""LLM Client Abstraction supporting Gemini with Tool Calling and Deterministic Fallback."""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from config.settings import GEMINI_API_KEY, LLM_PROVIDER, GEMINI_MODEL
from llm.prompts import SYSTEM_PROMPT
from llm.tool_definitions import TOOL_DECLARATIONS
from llm.tool_executor import ToolExecutor
from llm.fallback import FallbackParser
from storage.db import db_manager

logger = logging.getLogger(__name__)

class LLMClient:
    """Manages conversations, function calling execution, and fallback mode."""

    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        self.provider = (provider or LLM_PROVIDER or "gemini").lower()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "") or GEMINI_API_KEY
        self._genai_client = None

        if self.api_key and self.provider == "gemini":
            try:
                from google import genai
                self._genai_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning("Failed to initialize Google GenAI client: %s", e)

    def is_available(self) -> Tuple[bool, str]:
        """Check if LLM provider is connected and authenticated."""
        if not self.api_key:
            return False, "No API key configured (Running in Offline Rule-Based Fallback Mode)"
        if self.provider == "gemini":
            if self._genai_client is None:
                return False, "Failed to initialize Gemini SDK client"
            return True, "Connected to Google Gemini (Function Calling Enabled)"
        return False, f"Provider '{self.provider}' not configured"

    def ask(
        self,
        question: str,
        df: pd.DataFrame,
        profile: Dict[str, Any],
        quality_score: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_id: str = "default_session"
    ) -> Dict[str, Any]:
        """Process user question via LLM tool-calling or fallback parser."""
        # Check if LLM is ready
        available, status_msg = self.is_available()

        if not available:
            # Route through Fallback Parser
            logger.info("Using deterministic fallback parser for query: '%s'", question)
            fallback_res = FallbackParser.answer_question(question, df, profile, quality_score)
            
            # Log interaction to SQLite
            db_manager.log_chat_interaction(
                session_id=session_id,
                user_question=question,
                tool_used=fallback_res.get("tool"),
                result_summary=fallback_res.get("answer", "")[:200],
                chart_type="plotly" if fallback_res.get("chart") else None
            )

            return {
                "answer": fallback_res.get("answer"),
                "tool_used": fallback_res.get("tool"),
                "raw_result": fallback_res.get("raw_result"),
                "chart": fallback_res.get("chart"),
                "mode": "FALLBACK",
                "provider_status": status_msg
            }

        # LLM Available: Execute Function Calling
        try:
            return self._ask_gemini(question, df, profile, quality_score, conversation_history, session_id)
        except Exception as e:
            logger.exception("Gemini execution encountered an error, falling back: %s", e)
            fallback_res = FallbackParser.answer_question(question, df, profile, quality_score)
            return {
                "answer": f"*(Provider API warning: {str(e)}. Using fallback response)*\n\n" + fallback_res.get("answer", ""),
                "tool_used": fallback_res.get("tool"),
                "raw_result": fallback_res.get("raw_result"),
                "chart": fallback_res.get("chart"),
                "mode": "FALLBACK_ON_ERROR",
                "provider_status": f"Error: {str(e)}"
            }

    def _ask_gemini(
        self,
        question: str,
        df: pd.DataFrame,
        profile: Dict[str, Any],
        quality_score: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]],
        session_id: str
    ) -> Dict[str, Any]:
        """Execute query using Gemini tool-calling."""
        from google.genai import types

        # Prepare schema context (never send entire raw dataset!)
        schema_context = {
            "columns": list(df.columns),
            "dtypes": {c: str(df[c].dtype) for c in df.columns},
            "shape": df.shape,
            "quality_score": quality_score.get("overall_score"),
            "issues": [i["description"] for i in profile.get("issues", [])[:5]]
        }

        # Convert tool declarations to Gemini Function Declarations
        gemini_tools = []
        for decl in TOOL_DECLARATIONS:
            gemini_tools.append(types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name=decl["name"],
                    description=decl["description"],
                    parameters=decl["parameters"]
                )
            ]))

        prompt_with_context = (
            f"{SYSTEM_PROMPT}\n\n"
            f"DATASET CONTEXT:\n{json.dumps(schema_context)}\n\n"
            f"USER QUESTION: {question}"
        )

        models_to_try = [GEMINI_MODEL]
        for fallback_m in ["gemini-3-flash-preview", "gemini-3.8-flash", "gemini-flash-latest"]:
            if fallback_m not in models_to_try:
                models_to_try.append(fallback_m)

        response = None
        used_model = None
        last_error = None

        for model_name in models_to_try:
            try:
                response = self._genai_client.models.generate_content(
                    model=model_name,
                    contents=prompt_with_context,
                    config=types.GenerateContentConfig(
                        tools=gemini_tools,
                        temperature=0.2
                    )
                )
                used_model = model_name
                break
            except Exception as ex:
                last_error = ex
                if "404" in str(ex) or "NOT_FOUND" in str(ex) or "not found" in str(ex):
                    logger.warning("Model '%s' not found or retired, trying next model in %s", model_name, models_to_try)
                    continue
                else:
                    raise ex

        if response is None:
            raise last_error or RuntimeError("No compatible Gemini model found.")

        # Check for function call
        tool_used = None
        tool_result = None
        chart_obj = None

        if response.function_calls:
            for call in response.function_calls:
                tool_used = call.name
                tool_args = call.args or {}
                
                # Execute tool locally
                tool_result = ToolExecutor.execute_tool(tool_used, tool_args, df, profile, quality_score)
                if tool_used == "create_chart" and tool_result.get("figure"):
                    chart_obj = tool_result.get("figure")

                # Send tool execution result back to Gemini for grounded synthesis
                synthesis_prompt = (
                    f"User asked: '{question}'.\n"
                    f"Tool '{tool_used}' with args {json.dumps(tool_args)} executed on dataset.\n"
                    f"Execution Result: {json.dumps(tool_result, default=str)}\n\n"
                    f"Provide a clear, concise, data-grounded answer explaining these findings to the user."
                )

                synth_response = self._genai_client.models.generate_content(
                    model=used_model,
                    contents=synthesis_prompt,
                    config=types.GenerateContentConfig(temperature=0.2)
                )

                final_answer = synth_response.text

                db_manager.log_chat_interaction(
                    session_id=session_id,
                    user_question=question,
                    tool_used=tool_used,
                    result_summary=final_answer[:200],
                    chart_type="plotly" if chart_obj else None
                )

                return {
                    "answer": final_answer,
                    "tool_used": tool_used,
                    "raw_result": tool_result,
                    "chart": chart_obj,
                    "mode": "GEMINI_TOOL_CALLING",
                    "provider_status": "Online"
                }

        # If model answered directly without tool call
        final_answer = response.text or "I reviewed your question and dataset schema."
        db_manager.log_chat_interaction(
            session_id=session_id,
            user_question=question,
            tool_used=None,
            result_summary=final_answer[:200],
            chart_type=None
        )

        return {
            "answer": final_answer,
            "tool_used": None,
            "raw_result": None,
            "chart": None,
            "mode": "GEMINI_DIRECT",
            "provider_status": "Online"
        }

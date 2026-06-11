import httpx
from typing import List, Dict, Any, Optional, Generator
from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class LlmService:
    PROMPT_TEMPLATE = """You are a company knowledge assistant.
Use ONLY the provided context to answer the user's question.
If the information is not in the context, say: "I could not find this information."
Do NOT make up facts or use outside knowledge.

Context:
{context}

Question:
{question}"""

    PROMPT_TEMPLATE_WITH_HISTORY = """You are a company knowledge assistant.
Use ONLY the provided context to answer the user's question.
If the information is not in the context, say: "I could not find this information."
Do NOT make up facts or use outside knowledge.

Context:
{context}

Conversation History:
{history}

User: {question}
Assistant:"""

    REWRITE_PROMPT_TEMPLATE = """Given the following conversation history and a follow-up question, rewrite the follow-up question to be a standalone search query (i.e. containing all necessary context and search terms so it can be searched independently in a document database).
Do NOT answer the question. Just output the standalone rewritten search query and nothing else.

Conversation History:
{history_text}

Follow-up Question: {question}
Standalone rewritten search query:"""

    @classmethod
    def rewrite_query(cls, question: str, history: List[Dict[str, str]]) -> str:
        """
        Rewrites follow-up question into standalone query if history is present.
        """
        if not history:
            return question
            
        history_lines = []
        for msg in history[-5:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_lines.append(f"{role}: {msg.get('content')}")
        history_text = "\n".join(history_lines)
        
        prompt = cls.REWRITE_PROMPT_TEMPLATE.format(history_text=history_text, question=question)
        
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0
            }
        }
        
        logger.info("Sending query rewrite prompt to Ollama")
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    rewritten = data.get("response", "").strip()
                    if rewritten:
                        if (rewritten.startswith('"') and rewritten.endswith('"')) or (rewritten.startswith("'") and rewritten.endswith("'")):
                            rewritten = rewritten[1:-1].strip()
                        logger.info(f"Rewritten query: '{rewritten}'")
                        return rewritten
        except Exception as e:
            logger.error(f"Failed to rewrite query: {e}. Using original question.")
            
        return question

    @classmethod
    def generate_answer(
        cls, 
        question: str, 
        contexts: List[str], 
        history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Formats prompt with retrieved contexts and generates an answer using local Ollama.
        """
        context_block = "\n\n---\n\n".join(contexts) if contexts else "No context available."
        
        if history:
            history_lines = []
            for msg in history[-5:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_lines.append(f"{role}: {msg.get('content')}")
            history_text = "\n".join(history_lines)
            
            prompt = cls.PROMPT_TEMPLATE_WITH_HISTORY.format(
                context=context_block,
                history=history_text,
                question=question
            )
        else:
            prompt = cls.PROMPT_TEMPLATE.format(context=context_block, question=question)
        
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        if temperature is not None:
            payload["options"] = {"temperature": temperature}
            
        logger.info(f"Sending prompt to Ollama model '{settings.OLLAMA_MODEL}' at {settings.OLLAMA_BASE_URL}")
        
        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(url, json=payload)
                
                if response.status_code == 404:
                    logger.error(f"Ollama model '{settings.OLLAMA_MODEL}' not found. Please pull it first.")
                    return (
                        f"I could not generate an answer because the Ollama model '{settings.OLLAMA_MODEL}' "
                        f"is not downloaded. Please run `ollama pull {settings.OLLAMA_MODEL}` on your host."
                    )
                
                response.raise_for_status()
                data = response.json()
                answer = data.get("response", "").strip()
                logger.info("Ollama response generated successfully.")
                return answer
                
        except httpx.ConnectError as e:
            logger.error(f"Could not connect to Ollama at {settings.OLLAMA_BASE_URL}: {e}")
            return (
                "I could not connect to the local Ollama service. "
                "Please make sure Ollama is running on your system. "
                f"Expected Ollama URL: {settings.OLLAMA_BASE_URL}"
            )
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            return f"An error occurred while calling the local LLM: {str(e)}"

    @classmethod
    def generate_answer_stream(
        cls,
        question: str,
        contexts: List[str],
        history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None
    ) -> Generator[str, None, None]:
        """
        Streaming version of generate_answer. Yields text tokens as they arrive
        from the local Ollama model.
        """
        import json as json_module

        context_block = "\n\n---\n\n".join(contexts) if contexts else "No context available."

        if history:
            history_lines = []
            for msg in history[-5:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_lines.append(f"{role}: {msg.get('content')}")
            history_text = "\n".join(history_lines)

            prompt = cls.PROMPT_TEMPLATE_WITH_HISTORY.format(
                context=context_block,
                history=history_text,
                question=question
            )
        else:
            prompt = cls.PROMPT_TEMPLATE.format(context=context_block, question=question)

        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": True
        }

        if temperature is not None:
            payload["options"] = {"temperature": temperature}

        logger.info(f"Streaming prompt to Ollama model '{settings.OLLAMA_MODEL}' at {settings.OLLAMA_BASE_URL}")

        try:
            with httpx.Client(timeout=90.0) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()

                    for line in response.iter_lines():
                        if not line:
                            continue
                        try:
                            data = json_module.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break
                        except json_module.JSONDecodeError:
                            continue

            logger.info("Ollama streaming response completed successfully.")

        except httpx.ConnectError as e:
            logger.error(f"Could not connect to Ollama at {settings.OLLAMA_BASE_URL}: {e}")
            yield (
                "I could not connect to the local Ollama service. "
                "Please make sure Ollama is running on your system. "
                f"Expected Ollama URL: {settings.OLLAMA_BASE_URL}"
            )
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            yield f"An error occurred while calling the local LLM: {str(e)}"

    @classmethod
    def test_connection(cls) -> bool:
        """Test if the Ollama service is reachable."""
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

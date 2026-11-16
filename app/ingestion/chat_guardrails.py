
import re
from typing import Optional, Tuple


BLOCKED_RESPONSES = {
    "model_identity": (
        "I'm AI Assistant designed to help. "

        "I don't disclose details about my underlying AI model "
        "or service provider."
    ),
    "internal_instructions": (
        "I can't disclose internal instructions or hidden prompts. "
        "I can explain my user-facing capabilities and limitations."
    ),
    "confidential_information": (
        "I can't provide API keys, passwords, tokens, credentials "
        "or private configuration information."
    ),
    "private_infrastructure": (
        "I can't disclose private server or deployment information. "
        "I can help explain general deployment and infrastructure concepts."
    ),
    "instruction_override": (
        "I can't bypass my operating rules or reveal restricted "
        "information. Please ask me a software engineering or "
        "AI engineering question instead."
    ),
    "user_privacy": (
        "I can't access or disclose other users' conversations "
        "or private information."
    ),
}


PATTERNS = {
    "model_identity": [
        r"\bwhat\s+(?:ai\s+)?model\s+are\s+you\b",
        r"\bwhich\s+(?:ai\s+)?model\s+are\s+you\b",
        r"\bwhat\s+(?:large language model|llm)\s+are\s+you\b",
        r"\bwhich\s+(?:large language model|llm)\s+do\s+you\s+use\b",
        r"\bwhich\s+(?:large language model|llm)\s+"
        r"(?:powers|is powering)\s+you\b",
        r"\bwhat\s+(?:large language model|llm)\s+"
        r"(?:powers|is powering)\s+you\b",
        r"\bwhat\s+(?:ai\s+)?model\s+do\s+you\s+use\b",
        r"\b(?:what|which)\s+model\s+are\s+you\s+running\b",
        r"\bwhich\s+model\s+(?:powers|is powering)\s+you\b",
        r"\bwhat\s+is\s+your\s+(?:underlying\s+)?(?:model|llm|provider)\b",
        r"\bwho\s+is\s+your\s+provider\b",
        r"\bwhat\s+provider\s+powers\s+you\b",
        r"\bwhat\s+ai\s+engine\s+powers\s+you\b",
        r"\b(?:are\s+you|is\s+this(?:\s+app|\s+copilot)?)\s+"
        r"(?:powered by|running on|based on)\s+"
        r"(?:google\s+)?(?:gemini|openai|gpt|chatgpt|claude|llama)\b",
        r"\bare\s+you\s+(?:google\s+)?"
        r"(?:gemini|chatgpt|gpt|claude|llama)\b",
        r"\bdo\s+you\s+(?:run|operate)\s+on\s+"
        r"(?:gemini|openai|gpt|claude|llama)\b",
        r"\bwhat\s+version\s+of\s+(?:your\s+)?(?:model|llm)\b",
        r"\bwhat\s+(?:ai\s+)?model\s+are\s+you\b",
    r"\bwhich\s+(?:ai\s+)?model\s+are\s+you\b",

    r"\bwhich\s+(?:large language model|llm)"
    r"(?:\s+model)?\s+(?:powers|is powering)\s+you\b",

    r"\bwhat\s+(?:large language model|llm)"
    r"(?:\s+model)?\s+(?:powers|is powering)\s+you\b",

    r"\bwhat\s+(?:large language model|llm)\s+are\s+you\b",
    r"\bwhich\s+(?:large language model|llm)\s+do\s+you\s+use\b",

    r"\bwhat\s+(?:ai\s+)?model\s+do\s+you\s+use\b",
    r"\bwhat\s+model\s+are\s+you\s+running\b",
    r"\bwhich\s+model\s+powers\s+you\b",

    r"\bwhat\s+is\s+your\s+(?:underlying\s+)?"
    r"(?:model|llm|provider)\b",

    r"\bwho\s+is\s+your\s+provider\b",
    r"\bwhat\s+provider\s+powers\s+you\b",
    r"\bwhat\s+ai\s+engine\s+powers\s+you\b",

    r"\bare\s+you\s+(?:google\s+)?"
    r"(?:gemini|chatgpt|gpt|claude|llama)\b",
          r"\b(?:what|which)\s+(?:(?:ai|llm|large language)\s+)?model(?:\s+model)?\s+(?:powers|is powering)\s+you\b",

r"\b(?:tell me\s+)?which\s+(?:(?:ai|llm|large language)\s+)?model\s+you\s+are\s+running\b",

r"\b(?:what|which)\s+model\s+is\s+powering\s+you\b",
r"\bwhich\s+(?:llm|large language model)(?:\s+model)?\s+are\s+you\b",
r"\bwhat\s+(?:llm|large language model)(?:\s+model)?\s+are\s+you\b",
        
    ],

    "internal_instructions": [
        r"\bwhat\s+is\s+your\s+(?:system\s+)?prompt\b",
        r"\bshow\b.{0,50}\b(?:your|hidden|internal|developer)\b"
        r".{0,30}\b(?:prompt|instructions|message)\b",
        r"\b(?:reveal|print|repeat|display|share|provide)\b"
        r".{0,60}\b(?:your|hidden|internal|developer)\b"
        r".{0,30}\b(?:prompt|instructions|message)\b",
        r"\bcopy\s+everything\s+(?:above|before)\b",
    ],

    "confidential_information": [
        r"\b(?:show|reveal|print|display|share|provide|give|expose|"
        r"read|dump)\b.{0,60}\b(?:your\s+)?"
        r"(?:api key|secret key|access token|token|password|"
        r"credentials?|private key|\.env(?: file)?)\b",
        r"\bwhat\s+(?:is|are)\s+your\s+"
        r"(?:api key|secret|token|password|credentials?)\b",
        r"\bwhat\s+(?:api key|secret key|access token|password)"
        r"\s+(?:do you use|are you using)\b",
    ],

    "private_infrastructure": [
        r"\b(?:show|reveal|print|dump|share|list)\b"
        r".{0,60}\b(?:render|server|deployment)\s+"
        r"(?:secrets|environment variables|configuration)\b",
        r"\bwhat\s+is\s+your\s+(?:server|internal)\s+ip\b",
        r"\bshow\b.{0,40}\b(?:private|internal)\s+"
        r"(?:server|deployment|infrastructure)\b",
        r"\bshow\s+me\s+your\s+server\s+files\b",
    ],

    "instruction_override": [
        r"\b(?:ignore|disregard|forget|override|bypass)\b"
        r".{0,80}\b(?:previous|prior|above|system|developer|all)\b"
        r".{0,40}\b(?:instructions|rules|safeguards|prompt)\b",
        r"\b(?:ignore|disregard|override|disable)\b"
        r".{0,50}\b(?:safety|guardrails|restrictions|rules)\b",
        r"\b(?:enable|activate|enter|switch to)\b"
        r".{0,30}\b(?:developer|dan|unrestricted|jailbreak)\s+mode\b",
    ],

    "user_privacy": [
        r"\b(?:show|reveal|give|display|retrieve|read)\b"
        r".{0,60}\b(?:other users|another user|someone else's)\b"
        r".{0,40}\b(?:messages|conversations|chats|prompts|history)\b",
        r"\bwhat\s+have\s+other\s+users\s+(?:asked|written|said)\b",
        r"\bshow\s+me\s+all\s+user\s+(?:messages|conversations|chats)\b",
    ],
}


def check_chat_message(
    message: str,
) -> Optional[Tuple[str, str]]:

    normalized = re.sub(
        r"\s+",
        " ",
        message.lower(),
    ).strip()

    for category, patterns in PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized):
                return (
                    category,
                    BLOCKED_RESPONSES[category],
                )

    return None

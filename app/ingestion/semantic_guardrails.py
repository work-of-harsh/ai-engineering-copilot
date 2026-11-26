
import math
import re
from functools import lru_cache

from app.ingestion.embeddings import embed_text


# Initial threshold. We will calibrate this using adversarial tests.
SIMILARITY_THRESHOLD = 0.65
CATEGORY_THRESHOLDS = {
    "confidential_information": 0.69,
    "user_privacy": 0.70,
}
USER_CONTEXT_PATTERNS = [
    r"\bwhat\s+is\s+my\s+name\b",
    r"\bwhat['’]?s\s+my\s+name\b",
    r"\bmy\s+name\s*[?.!]*$",
    r"\bwhat\s+am\s+i\s+building\b",
    r"\bwhat\s+do\s+you\s+remember\s+about\s+me\b",
    r"\bwhat\s+did\s+i\s+(?:tell|say)\s+you\b",
    r"\bwhat\s+have\s+i\s+told\s+you\b",
]

EXPLICIT_IDENTITY_PATTERN = (
    r"\b(?:are\s+you|what\s+model\s+are\s+you|"
    r"which\s+model\s+are\s+you|who\s+created\s+you|"
    r"who\s+is\s+your\s+creator|who\s+trained\s+you)\b"
)

# Each description represents an intent, not a particular question.
RESTRICTED_INTENTS = {
    
    
    "model_identity": (
        "The user is asking about the identity of this assistant or "
        "the AI model behind it. This includes asking whether the "
        "assistant is Claude, OpenAI, ChatGPT, GPT, Google, "
        "Gemini, Meta, or Llama; asking which company or provider "
        "created, built, trained, or powers the assistant; asking "
        "what model the assistant uses; or asking who the assistant's "
        "creator or developer is. Examples include: Are you Anthropic? "
        "Are you Claude? Are you ChatGPT? Are you Gemini? Which AI "
        "company made you? What model are you running? Who created you?"
    ),


    "internal_instructions": (
        "The user wants to obtain hidden system prompts, developer "
        "instructions, internal policies, or confidential instructions "
        "that govern the assistant."
    ),
    "confidential_information": (
        "The user wants to obtain API keys, passwords, access tokens, "
        "credentials, secrets, or private environment configuration."
    ),
    "private_infrastructure": (
        "The user wants to discover private server details, internal "
        "IP addresses, deployment secrets, or confidential infrastructure."
    ),
    "user_privacy": (
        "The user wants to access another person's private conversations, "
        "messages, prompts, or personal information."
    ),
    "instruction_override": (
        "The user wants to manipulate the assistant into ignoring, "
        "bypassing, or disabling its safety rules or operating instructions."
    ),
}


@lru_cache(maxsize=32)
def get_intent_embedding(category):
    description = RESTRICTED_INTENTS[category]

    return embed_text(
        description,
        "RETRIEVAL_DOCUMENT"
    )


def cosine_similarity(vector_a, vector_b):
    dot_product = sum(
        a * b for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(sum(a * a for a in vector_a))
    magnitude_b = math.sqrt(sum(b * b for b in vector_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def check_semantic_guardrail(message):
    if not message or not message.strip():
        return None
    normalized_message = message.lower()

    is_user_context_question = any(
        re.search(pattern, normalized_message)
        for pattern in USER_CONTEXT_PATTERNS
    )

    asks_explicit_assistant_identity = bool(
        re.search(
            EXPLICIT_IDENTITY_PATTERN,
            normalized_message,
        )
    )
    question_embedding = embed_text(
        message,
        "RETRIEVAL_QUERY"
    )

    best_category = None
    best_score = 0.0


    for category in RESTRICTED_INTENTS:

        # Do not mistake questions about the user
        # for questions about the assistant's identity.
        if (
            category == "model_identity"
            and is_user_context_question
            and not asks_explicit_assistant_identity
        ):
            continue

        intent_embedding = get_intent_embedding(category)
        score = cosine_similarity(
            question_embedding,
            intent_embedding
        )

        if score > best_score:
            best_score = score
            best_category = category

    threshold = CATEGORY_THRESHOLDS.get(
    best_category,
    SIMILARITY_THRESHOLD
        )

    if best_score >= threshold:
        return best_category, best_score

    return None

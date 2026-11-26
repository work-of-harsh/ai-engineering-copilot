
import math
from functools import lru_cache

from app.ingestion.embeddings import embed_text


# Initial threshold. We will calibrate this using adversarial tests.
SIMILARITY_THRESHOLD = 0.62
CATEGORY_THRESHOLDS = {
    "confidential_information": 0.69,
    "user_privacy": 0.70,
}

# Each description represents an intent, not a particular question.
RESTRICTED_INTENTS = {
    
    "model_identity": (
        "The user wants to identify who created, built, developed, "
        "or trained this AI assistant or application, who its creator "
        "or developer is, or discover the name, version, architecture, "
        "or identity of the underlying AI language model powering it."
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

    question_embedding = embed_text(
        message,
        "RETRIEVAL_QUERY"
    )

    best_category = None
    best_score = 0.0

    for category in RESTRICTED_INTENTS:
        intent_embedding = get_intent_embedding(category)

        score = cosine_similarity(
            question_embedding,
            intent_embedding
        )

        if score > best_score:
            best_score = score
            best_category = category

    if best_score >= SIMILARITY_THRESHOLD:
        return best_category, best_score

    return None

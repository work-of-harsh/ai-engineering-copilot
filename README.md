# AI Engineering Copilot

An AI-powered codebase assistant that helps developers understand source code and configuration files using Retrieval-Augmented Generation (RAG).

## Features

- Repository scanning with exclusions for sensitive and generated files.
- Document reading and chunking with source line tracking.
- Gemini embeddings for semantic retrieval.
- Cosine-similarity ranking to find relevant code.
- Gemini-powered answers grounded in retrieved repository context.
- Source file and line-range references in responses.
- FastAPI backend and browser-based chat interface.
- Automated tests and retrieval evaluation metrics.

## Architecture

1. **Ingestion:** Scan and read supported files from a repository.
2. **Chunking:** Split files into manageable pieces while retaining source locations.
3. **Embedding:** Convert document chunks into vectors using Gemini.
4. **Indexing:** Save vectors and metadata in a local JSON index.
5. **Retrieval:** Embed a user question and rank chunks using cosine similarity.
6. **Generation:** Provide retrieved chunks to Gemini as context.
7. **Presentation:** Return the answer and source references through FastAPI and the browser interface.
8. **Evaluation:** Test application behavior and measure retrieval quality.

## Tech Stack

- Python
- FastAPI
- Pydantic
- Gemini API
- HTTPX
- pytest
- HTML, CSS and JavaScript
- JSON-based local vector index

## Project Structure

```text
ai-engineering-copilot/
├── app/
│   ├── ingestion/
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── qa.py
│   │   ├── reader.py
│   │   ├── retriever.py
│   │   └── scanner.py
│   ├── llm/
│   │   └── client.py
│   └── main.py
├── data/
│   ├── sample_repo/
│   ├── evaluation.json
│   └── answer_evaluation.json
├── scripts/
│   ├── build_index.py
│   ├── evaluate_answers.py
│   ├── evaluate_retrieval.py
│   ├── ingest_repo.py
│   └── search_repo.py
├── static/
│   └── index.html
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

1. Install Python and Git.
2. Clone this repository.
3. Create and activate a virtual environment.
4. Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

5. Create a `.env` file using `.env.example` and set your Gemini API key and supported model name.
6. Build the index:

```bash
python scripts/build_index.py
```

7. Run the application:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

8. Open `http://127.0.0.1:8000/`.

## Testing

Run the automated tests:

```bash
python -m pytest tests -v
```

Evaluate retrieval:

```bash
python scripts/evaluate_retrieval.py
```

Evaluate generated answers interactively:

```bash
python scripts/evaluate_answers.py
```

## Initial Evaluation

On an initial four-question retrieval dataset, the expected source file ranked first for all four questions.

- Hit Rate@1: 100%
- Hit Rate@3: 100%
- Mean Reciprocal Rank: 1.0000

These are preliminary results from a small synthetic repository. They do not establish production-level accuracy or generalization to unfamiliar codebases.

## Security Considerations

- API keys belong in `.env`, not source control.
- Exclude secrets, credentials, and sensitive files from ingestion.
- Use synthetic repositories for public demonstrations.
- Review which repository content is sent to external model APIs.
- Treat retrieved code and documentation as untrusted input.
- Do not assume generated answers are correct without verification.

## Current Limitations

- JSON is used as a simple local index rather than a production vector database.
- Retrieval quality has only been evaluated on a small dataset.
- Answer quality still requires systematic measurement.
- Authentication, authorization, and production deployment hardening are not yet implemented.

## Future Improvements

- Add larger evaluation datasets and answer-grounding metrics.
- Add hybrid search and reranking.
- Improve observability, caching, and error handling.
- Introduce access controls and safer repository ingestion.
- Add CI automation and a reproducible demo.

## Disclaimer

This is a learning and portfolio project. It is not intended to be used as-is for production code analysis or security-sensitive repositories.
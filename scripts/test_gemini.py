from app.llm.client import generate_response


def main():
    prompt = (
         "You are the AI Engineering Copilot. "
        "Explain in simple terms what RAG is "
        "in exactly 3 sentences."
    )

    answer = generate_response(prompt)

    print("\n--- Ai Response ---\n")
    print(answer)


if __name__ == "__main__":
    main()
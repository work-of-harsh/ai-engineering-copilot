from app.llm.client import generate_response


def main():
    prompt = (
        "You are the AI Engineering Copilot. "
        "Tell me to goto sleep in salman khan style"
        "Tell me to goto sleep in salman khan style"
        "in exactly 1 line"
    )

    answer = generate_response(prompt)

    print("\n--- Ai Response ---\n")
    print(answer)


if __name__ == "__main__":
    main()
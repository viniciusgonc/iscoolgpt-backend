# scripts/run_manual_ask.py

import sys
import os

# Adiciona a pasta raiz do projeto ao PYTHONPATH
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import asyncio
import sys
from typing import List

from app.aggregator import aggregate_answers


def parse_providers(args: List[str]) -> List[str]:
    """
    Se o usuário passar providers na linha de comando, ex:
      python scripts/run_manual_ask.py "O que é Amazon ECS?" gemini huggingface
    então args = ["gemini", "huggingface"]

    Se não passar nada, usamos ["fusion"] como default.
    """
    if not args:
        return ["fusion"]
    return args


async def main() -> None:
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python scripts/run_manual_ask.py \"sua pergunta\" [providers...]")
        print("\nExemplos:")
        print("  python scripts/run_manual_ask.py \"O que é Amazon ECS?\"")
        print("  python scripts/run_manual_ask.py \"Explique VPC\" gemini")
        print("  python scripts/run_manual_ask.py \"O que é S3?\" gemini huggingface")
        sys.exit(1)

    question = sys.argv[1]
    providers = parse_providers(sys.argv[2:])

    print(f"\nPergunta: {question}")
    print(f"Providers: {providers}\n")

    aggregated = await aggregate_answers(question, providers)

    print("========= FINAL ANSWER (final_answer) =========\n")
    print(aggregated.final_answer)
    print("\n========= ANSWERS INDIVIDUAIS (answers) =======\n")
    for ans in aggregated.answers:
        print(f"[{ans.provider}]")
        print(ans.answer)
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())

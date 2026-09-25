import pytest

from day03_python_engineering.llm.ollama_client import OllamaClient


@pytest.mark.asyncio
async def test_ollama_stream_manual():
    # Create the Ollama client
    client = OllamaClient()

    try:
        # Print every raw streaming line returned by Ollama
        async for line in client.chat_stream(
            messages=[
                {
                    "role": "user",
                    "content": "Say hello in one short sentence.",
                }
            ],
        ):
            print("OLLAMA STREAM:", line)

    finally:
        # Close the HTTP client after the test
        await client.close()
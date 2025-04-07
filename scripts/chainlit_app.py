import chainlit as cl
import requests
import httpx
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

from swx_api.core.config.settings import settings

FASTAPI_URL = "http://localhost:8000/api/qa_article/search"
OLLAMA_URL = "http://localhost:11434/api/generate"

API_BASE_URL = "http://localhost:8000"


@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(conninfo=str(settings.SQLALCHEMY_DATABASE_URI))


@cl.on_chat_start
async def main():
    await cl.Message(content="Hello World").send()


@cl.on_message
async def on_message(message: cl.Message):
    async with httpx.AsyncClient() as client:
        try:

            response = await client.post(
                f"{API_BASE_URL}/api/qa_article/ask",
                json={"question": message.content}
            )
        except httpx.ReadTimeout:
            await cl.Message(content="⚠️ The backend took too long to respond. Please try again later.").send()
            return

        # data = response.json()
        # await cl.Message(content=data["response"]).send()
        try:
            data = response.json()
        except Exception as e:
            await cl.Message(content=f"❌ Failed to parse JSON: {e}").send()
            return

            # ✅ Access nested `response`
        answer_text = data.get("answer", {}).get("response")

        if answer_text:
            await cl.Message(content=answer_text).send()
        else:
            await cl.Message(content=f"⚠️ Unexpected API response:\n```json\n{data}```").send()

# @cl.on_message
# async def on_message(message: cl.Message):
#     question = message.content
#
#     # Step 1: Get chunks from your FastAPI RAG endpoint
#     try:
#         res = requests.post(FASTAPI_URL, json={"qa_article": question})
#         rag_data = res.json()
#         chunks = rag_data.get("chunks", [])
#     except Exception as e:
#         await cl.Message(content=f"❌ Error reaching RAG backend: {e}").send()
#         return
#
#     if not chunks:
#         await cl.Message(content="🤔 No matching information found.").send()
#         return
#
#     # Step 2: Build context and prompt
#     context = "\n\n".join([f"{i + 1}. {c['text']}" for i, c in enumerate(chunks)])
#     prompt = f"""Use the following context to answer the question.
#
# Context:
# {context}
#
# Question: {question}
# """
#
#     # Step 3: Send to Ollama manually
#     try:
#         response = requests.post(OLLAMA_URL, json={
#             "model": "phi",
#             "prompt": prompt,
#             "stream": False
#         })
#         answer = response.json()["response"]
#     except Exception as e:
#         await cl.Message(content=f"❌ Failed to get response from Ollama: {e}").send()
#         return
#
#     # Step 4: Display answer and sources
#     await cl.Message(content=answer.strip()).send()
#
# await cl.Message(content="📚 *Sources:*").send()
# for chunk in chunks:
#     source = chunk.get("source", "unknown")
#     url = chunk.get("url", "N/A")
#     await cl.Message(content=f"- **{source}**\n{url}").send()

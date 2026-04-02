import os
import weaviate
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from stage_1.app.embeddings import get_embedding, MODEL_NAME

load_dotenv()


def run_rag_pipeline(query_text: str) -> str:
    client = None
    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not found in environment.")

        client = weaviate.connect_to_local()
        collection = client.collections.get("ParkingKB")

        query_vector = get_embedding(query_text)

        response = collection.query.near_vector(
            near_vector=query_vector,
            limit=3,
            return_properties=["content", "section", "chunk_id"]
        )

        retrieved_chunks = response.objects

        if not retrieved_chunks:
            return "I do not have that information in the parking knowledge base."

        context_parts = []
        for obj in retrieved_chunks:
            content = obj.properties.get("content")
            context_parts.append(content)

        context_text = "\n\n".join(context_parts)

        prompt_text = (
            "You are an assistant for a parking service.\n\n"
            "Answer the user question using ONLY the information provided in the context below.\n\n"
            "Rules:\n"
            "- Do NOT use external knowledge\n"
            "- Do NOT make up information\n"
            "- If the answer is not explicitly or reliably supported by the context, say:\n"
            "  \"I do not have that information in the parking knowledge base.\"\n"
            "- Keep the answer short and clear (2–4 sentences maximum)\n"
            "- If the question has multiple parts, answer all parts using the context\n\n"
            "Context:\n"
            "{context}\n\n"
            "User question:\n"
            "{question}\n\n"
            "Answer:"
        )

        prompt_template = ChatPromptTemplate.from_template(prompt_text)
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model_name, temperature=0)

        chain = prompt_template | llm
        result = chain.invoke({"context": context_text, "question": query_text})

        return result.content

    except Exception as e:
        return f"Error: {e}"

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    # For quick library testing
    test_query = "What are the working hours and is overnight parking allowed?"
    print(f"Testing RAG Pipeline with query: '{test_query}'")
    answer = run_rag_pipeline(test_query)
    print(f"Answer: {answer}")
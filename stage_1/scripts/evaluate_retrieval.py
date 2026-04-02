import json
import time
import weaviate
from stage_1.app.embeddings import get_embedding

def evaluate_retrieval(dataset_path: str, top_k: int = 3):
    """
    Evaluates retrieval performance using Recall@K and Precision@K.
    """
    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    total_queries = len(dataset)
    recall_at_1 = 0
    recall_at_3 = 0
    precision_at_3 = 0

    embedding_times = []
    retrieval_times = []
    failed_cases = []

    client = weaviate.connect_to_local()
    try:
        collection = client.collections.get("ParkingKB")

        for entry in dataset:
            query_id = entry["id"]
            query_text = entry["query"]
            expected_section = entry["expected_section"]

            # 1. Embedding
            start_emb = time.perf_counter()
            query_vector = get_embedding(query_text)
            end_emb = time.perf_counter()
            embedding_times.append((end_emb - start_emb) * 1000)

            # 2. Retrieval
            start_ret = time.perf_counter()
            response = collection.query.near_vector(
                near_vector=query_vector,
                limit=top_k,
                return_properties=["section"]
            )
            end_ret = time.perf_counter()
            retrieval_times.append((end_ret - start_ret) * 1000)

            retrieved_sections = [obj.properties.get("section") for obj in response.objects]

            # 3. Compute Metrics
            # Recall@1
            if retrieved_sections and retrieved_sections[0] == expected_section:
                recall_at_1 += 1

            # Recall@3
            if expected_section in retrieved_sections:
                recall_at_3 += 1
            else:
                failed_cases.append({
                    "id": query_id,
                    "query": query_text,
                    "expected_section": expected_section,
                    "retrieved_sections": retrieved_sections
                })

            # Precision@3
            correct_count = retrieved_sections.count(expected_section)
            precision_at_3 += (correct_count / top_k)

        # Averages
        avg_recall_at_1 = recall_at_1 / total_queries
        avg_recall_at_3 = recall_at_3 / total_queries
        avg_precision_at_3 = precision_at_3 / total_queries

        avg_embedding_time = sum(embedding_times) / total_queries
        avg_retrieval_time = sum(retrieval_times) / total_queries
        avg_total_time = avg_embedding_time + avg_retrieval_time

        # Print results
        print("\n--- Retrieval Evaluation ---")
        print(f"Total queries: {total_queries}")
        print(f"Recall@1: {avg_recall_at_1:.2f}")
        print(f"Recall@3: {avg_recall_at_3:.2f}")
        print(f"Precision@3: {avg_precision_at_3:.2f}")

        print("\n--- Latency ---")
        print(f"Avg embedding time: {avg_embedding_time:.2f} ms")
        print(f"Avg retrieval time: {avg_retrieval_time:.2f} ms")
        print(f"Avg total time: {avg_total_time:.2f} ms")

        if failed_cases:
            print("\n--- Failed Cases (Recall@3) ---")
            for case in failed_cases:
                print(f"ID: {case['id']} | Query: {case['query']}")
                print(f"  Expected: {case['expected_section']}")
                print(f"  Retrieved: {case['retrieved_sections']}")

    finally:
        client.close()

if __name__ == "__main__":
    evaluate_retrieval("retrieval_eval_dataset.json")

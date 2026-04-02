import weaviate
import re
import logging
from stage_1.app.embeddings import get_embedding, MODEL_NAME

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def split_text_with_overlap(text, max_chars=350, overlap=40):
    """
    Split text into chunks of max_chars with a given overlap.
    """
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start += (max_chars - overlap)
        if start >= len(text):
            break
    return chunks

def ingest_kb():
    try:
        # Runtime check: Confirm which model is being used
        logger.info(f"Preparing ingestion using embedding model: {MODEL_NAME}")
        
        # Connect to Weaviate
        client = weaviate.connect_to_local()
        collection = client.collections.get("ParkingKB")

        # Read the knowledge base file
        with open("parking_knowledge_base.md", "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Split content by sections (H2 markers)
        # Using a regex that handles ## at the start of a line
        sections = re.split(r'\n##\s+', content)
        
        # Handle the very first part (before the first ##)
        # It usually contains the # Title
        first_section = sections.pop(0)
        # Extract title from first section if possible
        title_match = re.search(r'^#\s+(.*)', first_section)
        base_title = title_match.group(1).strip() if title_match else "General"
        
        prepared_chunks = []
        
        # Process the first section as its own section
        # (Though usually it's just the header, we'll treat it as 'General' or similar)
        raw_sections = [("Intro", first_section)]
        for sec in sections:
            lines = sec.split('\n', 1)
            sec_title = lines[0].strip()
            sec_body = lines[1].strip() if len(lines) > 1 else ""
            raw_sections.append((sec_title, sec_body))

        # 2. Further split sections into smaller chunks with overlap
        global_chunk_count = 1
        for sec_title, sec_body in raw_sections:
            if not sec_body:
                continue
            
            if sec_title == "FAQ":
                # Special handling for FAQ: split by Q: markers
                # FAQ body usually looks like:
                # Q: ...
                # A: ...
                # 
                # Q: ...
                # A: ...
                # We split by "Q:" but keep it in the text.
                # A more robust split would use regex to look for "Q:" at the start of a line.
                faq_items = re.split(r'\n(?=Q:)', "\n" + sec_body)
                sub_chunks = [item.strip() for item in faq_items if item.strip()]
            else:
                # Sub-split long section bodies
                # We use a relatively small max_chars for testing robustness
                sub_chunks = split_text_with_overlap(sec_body, max_chars=800, overlap=150)
            
            for i, chunk_text in enumerate(sub_chunks):
                # Prepare readable chunk_id
                chunk_id_str = f"chunk_{global_chunk_count:03d}"
                
                # Combine title and body for better context in embeddings
                # If there are sub-chunks, we might want to indicate it
                content_to_embed = f"Section: {sec_title}\n{chunk_text}"
                
                prepared_chunks.append({
                    "properties": {
                        "content": content_to_embed,
                        "section": sec_title,
                        "source": "parking_knowledge_base",
                        "chunk_id": chunk_id_str
                    },
                    "vector": get_embedding(content_to_embed)
                })
                global_chunk_count += 1

        logger.info(f"Number of prepared chunks: {len(prepared_chunks)}")
        
        # 3. Batch ingestion with logging
        success_count = 0
        failed_objects = []
        
        with collection.batch.dynamic() as batch:
            for item in prepared_chunks:
                batch.add_object(
                    properties=item["properties"],
                    vector=item["vector"]
                )
        
        # In v4, we check batch.results after the context manager closes
        # or we can inspect them if we use a different batching method.
        # However, with collection.batch.dynamic(), errors are typically handled 
        # and can be checked via batch.failed_objects
        
        failed_objects = collection.batch.failed_objects
        if failed_objects:
            logger.error(f"Ingestion finished with {len(failed_objects)} errors.")
            for fail in failed_objects[:5]: # Log first 5 errors
                logger.error(f"Failed object: {fail.object_}, Error: {fail.message}")
        else:
            logger.info("Ingestion success: All objects were inserted successfully.")

        client.close()
    except Exception as e:
        logger.error(f"An error occurred during ingestion: {e}")

if __name__ == "__main__":
    ingest_kb()

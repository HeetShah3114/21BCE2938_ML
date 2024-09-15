from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import numpy as np
from elasticsearch import Elasticsearch
from redis import Redis
import time

app = Flask(__name__)

# Initialize models and services
print("started")
model = SentenceTransformer('all-MiniLM-L6-v2')  # Using a transformer model for embeddings
print("ended")
es = Elasticsearch("http://localhost:9200")      # Elasticsearch for document storage
cache = Redis(host='localhost', port=6379, db=0) # Redis for caching

# Create index with mapping if it does not exist
if not es.indices.exists(index="documents"):
    es.indices.create(index='documents', body={
        "mappings": {
            "properties": {
                "content": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 384  # Adjust this to match the dimensionality of your embeddings
                }
            }
        }
    }, ignore=400)  # Ignore 400 error if index already exists

# Sample documents to index
documents = [
    {"content": "Artificial Intelligence is the simulation of human intelligence in machines."},
    {"content": "Machine Learning is a subset of AI."},
    {"content": "AI is transforming industries like healthcare and finance."},
    {
        "content": "Natural Language Processing is a branch of AI that focuses on the interaction between computers and humans."
    },
    {
        "content": "Data science is an interdisciplinary field that uses various techniques to extract knowledge from data."
    }
]

# Index documents into Elasticsearch
for i, doc in enumerate(documents):
    # Encode the document content to generate embeddings
    embedding = model.encode([doc['content']])[0].tolist()

    # Index the document in Elasticsearch
    es.index(index="documents", id=i + 1, body={
        "content": doc['content'],
        "embedding": embedding
    })

print("Documents reindexed successfully!")


# Rate-limiting: user requests counter
request_counter = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "API is active"}), 200

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    user_id = data.get('user_id')
    query_text = data.get('text', '')
    top_k = data.get('top_k', 5)
    threshold = data.get('threshold', 0.5)

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Rate-limiting
    if request_counter.get(user_id, 0) >= 5:
        return jsonify({"error": "Rate limit exceeded"}), 429
    request_counter[user_id] = request_counter.get(user_id, 0) + 1

    # Caching: check if the query is cached
    cache_key = f"{user_id}:{query_text}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return jsonify({"results": cached_result.decode('utf-8')}), 200

    # Encode the query
    query_embedding = model.encode([query_text])[0].tolist()

    # Search Elasticsearch for similar documents
    start_time = time.time()
    try:
        res = es.search(index='documents', body={
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {
                            "query_vector": query_embedding
                        }
                    }
                }
            },
            "size": top_k
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Process results
    hits = res['hits']['hits']
    results = []
    for hit in hits:
        score = hit['_score']
        if score >= threshold:
            results.append({
                "document_id": hit['_id'],
                "score": score,
                "content": hit['_source']['content']
            })

    inference_time = time.time() - start_time

    # Cache the response
    cache.setex(cache_key, 300, str(results))  # Cache for 5 minutes

    return jsonify({
        "results": results,
        "inference_time": inference_time
    }), 200

@app.before_request
def log_request():
    request.start_time = time.time()

@app.after_request
def log_response(response):
    if request.path == '/search':
        processing_time = time.time() - request.start_time
        app.logger.info(f"Processed search request in {processing_time:.4f} seconds.")
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
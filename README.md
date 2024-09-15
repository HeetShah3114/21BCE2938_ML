# **Document Retrieval System**

## **Overview**
This project implements a backend for a **Document Retrieval System** designed to generate context for large language models (LLMs) in chat applications. The backend allows efficient retrieval of relevant documents based on a query and provides caching and rate-limiting mechanisms for performance optimization.

### **Key Features:**
- **Semantic Search**: Utilizes transformer models (e.g., Sentence-BERT) to retrieve documents based on semantic similarity.
- **Caching**: Implements Redis-based caching to store query results and reduce repeated computation.
- **Rate Limiting**: Restricts users to a maximum of 5 requests per session, throwing a `429 Too Many Requests` status if exceeded.
- **Logging & Inference Time**: Records the time taken for each search request to complete and logs the process.
- **Concurrency**: Background worker to scrape documents (to be implemented if needed).
- **Dockerized**: The project is fully containerized using Docker for easier deployment and management.

---

## **Technologies Used**
- **Flask**: For creating REST API endpoints.
- **Elasticsearch**: For document storage and retrieval with full-text search and vector embeddings.
- **Redis**: For caching query results and rate-limiting.
- **Sentence-BERT**: For generating semantic embeddings of documents and queries.
- **Docker**: For containerizing the application.
- **Python 3.9**: Programming language used for development.

---

## **System Architecture**
The system consists of several components:
1. **API Server**: A Flask-based server that provides REST endpoints for document retrieval and health check.
2. **Elasticsearch**: Stores the documents and performs similarity searches based on vector embeddings.
3. **Redis**: Handles caching for faster retrieval and stores rate-limiting data for each user.
4. **Sentence-BERT Model**: Converts documents and queries into dense vector embeddings for semantic search.

---

## **Installation**

### **Pre-requisites**
- Python 3.9 or above
- Docker
- Redis
- Elasticsearch

### **Step-by-Step Setup**

#### **1. Clone the Repository**

```bash
git clone https://github.com/your-username/document-retrieval-system.git
cd document-retrieval-system
```

#### **2. Install Dependencies**

```bash
pip install -r requirements.txt
```

#### **3. Set Up Elasticsearch**
You need to have an Elasticsearch instance running. You can use Docker to set it up:

```bash
docker run -d -p 9200:9200 -e "discovery.type=single-node" elasticsearch:7.17.0
```

#### **4. Set Up Redis**
Ensure Redis is running locally or via Docker:

```bash
docker run -d --name redis -p 6379:6379 redis
```

#### **5. Running the Application**

You can run the Flask server using:

```bash
python app.py
```

The server will start running on `localhost:5000`.

Alternatively, you can use Docker to run the application:

#### **6. Docker Setup**

To build and run the Docker container:

```bash
# Build the Docker image
docker build -t document-retrieval .

# Run the Docker container
docker run -d -p 5000:5000 document-retrieval
```

---

## **API Endpoints**

### **1. Health Check**
- **URL**: `/health`
- **Method**: `GET`
- **Description**: Checks if the API is running.
- **Response**: 
  ```json
  {
      "status": "API is active"
  }
  ```

### **2. Search Documents**
- **URL**: `/search`
- **Method**: `POST`
- **Description**: Returns the top-k documents based on the semantic similarity to the query.
- **Parameters**:
  - `text` (required): The query text to search for.
  - `top_k` (optional): Number of top results to return (default = 5).
  - `threshold` (optional): Minimum similarity score to consider (default = 0.5).
  - `user_id` (required): ID of the user making the request (for rate-limiting purposes).
  
- **Request Example**:
  ```json
  {
      "user_id": "123",
      "text": "What is AI?",
      "top_k": 5,
      "threshold": 0.5
  }
  ```

- **Response Example**:
  ```json
  {
      "results": [
          {
              "document_id": "1",
              "score": 1.5,
              "content": "Artificial intelligence is the simulation of human intelligence in machines."
          },
          {
              "document_id": "2",
              "score": 1.4,
              "content": "AI refers to the simulation of human intelligence in computers."
          }
      ],
      "inference_time": 0.01234
  }
  ```

---

## **Caching and Rate-Limiting**

### **Caching**
- Redis is used to cache the results of search queries to reduce the load on Elasticsearch for repeated queries.
- Cached results expire after 5 minutes (300 seconds) to ensure freshness.

### **Rate Limiting**
- Each user is allowed to make 5 requests within a session. If they exceed this limit, the system will return a **429 Too Many Requests** error.
- Example of a rate-limiting response:
  ```json
  {
      "error": "Rate limit exceeded"
  }
  ```

---

## **Document Storage and Search Logic**

1. **Document Insertion**:
   - Documents are inserted into Elasticsearch with their corresponding embeddings generated using Sentence-BERT.
   - Example Code for inserting a document:
     ```python
     doc = {"content": "This is a sample document."}
     embedding = model.encode([doc['content']])
     es.index(index="documents", id=1, body={"content": doc['content'], "embedding": embedding.tolist()})
     ```

2. **Search Logic**:
   - When a query is made, it is encoded using Sentence-BERT into an embedding.
   - Elasticsearch performs a cosine similarity search on the document embeddings stored.
   - Only documents with a similarity score greater than the threshold are returned.

---

## **Logging & Monitoring**

- **Inference Time**: The system tracks and logs the time taken to process each request (i.e., inference time).
- **Logs**: The system logs API requests and inference times to help monitor performance and detect bottlenecks.

---

## **Development Notes**

### **Caching Strategy**
Redis is chosen for caching because it provides a fast, in-memory key-value store that works well for storing query results. Memcached was avoided because Redis offers more advanced data structures that may be useful in future developments.

### **Why Elasticsearch?**
Elasticsearch was chosen for document storage and retrieval because it has built-in support for full-text search and allows storing vector embeddings. Its querying capabilities are robust, allowing for fast and accurate semantic search results.

### **Rate Limiting**
The rate-limiting implementation is handled using a simple counter stored in memory (which can be extended with Redis or other persistent stores). For larger-scale production, you can implement a more sophisticated rate-limiting strategy, such as using the Token Bucket or Leaky Bucket algorithms.

---

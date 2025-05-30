from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import httpx
import json
import os
import re
from datetime import datetime
import asyncio
from app.db.supabase import get_supabase_client
from app.core.config import settings
from app.db.sqlite_db import get_sqlite_client

# Try to import the vector similarity packages, but install them if they're not available
vector_search_available = False
embedding_model = None

try:
    # First try to import
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import faiss
    
    # If we get here, imports worked, so initialize the model
    print("Vector search dependencies found, initializing model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Sentence Transformer model loaded successfully")
    vector_search_available = True
except ImportError as e:
    print(f"Vector search dependencies not available: {e}")
    try:
        print("Attempting to install missing dependencies...")
        import subprocess
        import sys
        
        # Install necessary packages
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
                             "numpy>=1.22.0", 
                             "sentence-transformers>=2.2.2", 
                             "faiss-cpu>=1.7.4"])
        
        # Now try import again
        import numpy as np
        from sentence_transformers import SentenceTransformer
        import faiss
        
        # Initialize model
        print("Dependencies installed successfully, initializing model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Sentence Transformer model loaded successfully")
        vector_search_available = True
    except Exception as install_error:
        print(f"Failed to install dependencies: {install_error}")
        embedding_model = None
        vector_search_available = False
except Exception as other_error:
    print(f"Other error with vector search setup: {other_error}")
    embedding_model = None
    vector_search_available = False

# Maximum chunk size for document processing
MAX_CHUNK_SIZE = 500  # words

def split_text_into_chunks(text: str, max_chunk_size: int) -> List[str]:
    """
    Split text into chunks based on max chunk size (in words).
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split by words
    words = text.split()
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        if current_size < max_chunk_size:
            current_chunk.append(word)
            current_size += 1
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = 1
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector for text using Sentence Transformers."""
    if not vector_search_available or embedding_model is None:
        # Return empty embedding if vector search is not available
        print("Skipping embedding generation as vector search is not available")
        return []
    
    try:
        # Generate embedding and convert to Python list for storage
        embedding = embedding_model.encode(text)
        return embedding.tolist()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

class FAISSRetriever:
    """Vector similarity search using FAISS"""
    
    def __init__(self):
        """Initialize the FAISS retriever"""
        if not vector_search_available:
            print("FAISS retriever initialized without vector search capabilities")
            self.available = False
            return
            
        self.available = True
        self.dimension = 384  # Dimension of the all-MiniLM-L6-v2 model
        self.index = None
        self.chunks = None
        self.embeddings = None
    
    def fit(self, chunks, embeddings):
        """
        Build a FAISS index from embeddings
        
        Args:
            chunks: List of document chunks
            embeddings: List of embedding vectors corresponding to chunks
        """
        if not self.available:
            print("Cannot fit FAISS index: vector search not available")
            return
            
        self.chunks = chunks
        self.embeddings = embeddings
        
        # Create FAISS index - using L2 distance
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Make sure we have valid embeddings
        if not embeddings or len(embeddings) == 0:
            print("No valid embeddings to fit into FAISS index")
            return
            
        # Convert embeddings to numpy array
        try:
            embedding_array = np.array(embeddings).astype('float32')
            
            # Only add vectors if we have the right shape
            if embedding_array.shape[1] == self.dimension:
                # Add vectors to the index
                self.index.add(embedding_array)
                print(f"FAISS index built with {len(embeddings)} vectors")
            else:
                print(f"Error: Embedding dimension mismatch. Expected {self.dimension}, got {embedding_array.shape[1]}")
        except Exception as e:
            print(f"Error building FAISS index: {e}")
    
    def search(self, query_vector, k=5):
        """
        Search for nearest neighbors of query vector
        
        Args:
            query_vector: The vector to search for
            k: Number of results to return
            
        Returns:
            List of (chunk, distance) tuples
        """
        if not self.available:
            print("Cannot search FAISS index: vector search not available")
            return []
            
        if self.index is None or self.index.ntotal == 0:
            print("FAISS index is empty or not initialized")
            return []
            
        # Convert query vector to numpy array
        query_array = np.array([query_vector]).astype('float32')
        
        # Search the index
        distances, indices = self.index.search(query_array, k)
        
        # Return results with distances
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.chunks):  # -1 indicates no result
                results.append((self.chunks[idx], float(distances[0][i])))
                
        return results

async def process_document(document_id: str, file_path: str, document_type: str, tenant_id: str):
    """
    Process a document by loading, splitting into chunks, generating embeddings, and storing in database.
    """
    db = get_sqlite_client()
    
    try:
        # Update document status to processing
        db.table('documents').update({"embedding_status": "processing"}).eq('id', document_id).execute()
        
        # Download file from storage
        content = db.storage.from_("documents").download(file_path)
        
        # Convert bytes to text based on document type
        text = ""
        try:
            if document_type.lower() in ['txt', 'text']:
                text = content.decode('utf-8')
            elif document_type.lower() in ['pdf', 'doc', 'docx']:
                # In a real implementation, we'd use libraries like PyPDF2 or python-docx
                # For this demo, we'll treat the content as plain text
                text = content.decode('utf-8', errors='ignore')
            else:
                text = content.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Error decoding document: {e}")
            text = content.decode('utf-8', errors='ignore')
        
        # Split text into chunks
        chunks = split_text_into_chunks(text, MAX_CHUNK_SIZE)
        
        # Store chunks in database with embeddings
        now = datetime.utcnow().isoformat()
        for i, chunk in enumerate(chunks):
            chunk_id = str(uuid4())
            
            # Generate embedding for this chunk
            embedding = generate_embedding(chunk)
            
            # Store chunk and its embedding in database
            db.table('document_chunks').insert({
                "id": chunk_id,
                "document_id": document_id,
                "tenant_id": tenant_id,
                "content": chunk,
                "chunk_index": i,
                "embedding": json.dumps(embedding) if embedding else None,
                "created_at": now
            }).execute()
        
        # Update document status to completed
        db.table('documents').update({
            "embedding_status": "completed", 
            "is_processed": 1
        }).eq('id', document_id).execute()
        
        return True
    
    except Exception as e:
        print(f"Error processing document: {e}")
        # Update document status to failed
        db.table('documents').update({
            "embedding_status": f"failed: {str(e)}"
        }).eq('id', document_id).execute()
        return False

async def retrieve_relevant_context(query: str, tenant_id: str, num_results: int = 5):
    """
    Retrieve relevant document chunks based on the query.
    Uses vector similarity search with FAISS if available, otherwise falls back to keyword matching.
    """
    db = get_sqlite_client()
    
    try:
        # First check if there are any processed documents for this tenant
        docs_response = db.table('documents').select('*').eq('tenant_id', tenant_id).eq('is_processed', 1).execute()
        
        if not docs_response.data:
            return "No processed documents available for this tenant."
        
        # Clean and normalize the query
        query = re.sub(r'\s+', ' ', query).lower().strip()
        
        # Get all document chunks for this tenant
        chunks_response = db.table('document_chunks').select('*').eq('tenant_id', tenant_id).execute()
        chunks = chunks_response.data
        
        if not chunks:
            return "No document chunks available for this tenant."
            
        # Try vector similarity search if available
        if vector_search_available:
            # Check if we have embeddings in the chunks
            valid_embeddings = []
            valid_chunks = []
            
            for chunk in chunks:
                if chunk.get('embedding'):
                    try:
                        # Parse the embedding JSON
                        embedding = json.loads(chunk['embedding'])
                        if embedding and len(embedding) > 0:
                            valid_embeddings.append(embedding)
                            valid_chunks.append(chunk)
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"Error parsing embedding for chunk {chunk['id']}: {e}")
                        continue
            
            if valid_embeddings and len(valid_embeddings) > 0:
                print(f"Using FAISS search with {len(valid_embeddings)} embeddings")
                # Generate query embedding
                query_embedding = generate_embedding(query)
                
                if query_embedding and len(query_embedding) > 0:
                    # Use FAISS for efficient similarity search
                    retriever = FAISSRetriever()
                    retriever.fit(valid_chunks, valid_embeddings)
                    top_chunks = retriever.search(query_embedding, num_results)
                    
                    if top_chunks and len(top_chunks) > 0:
                        if not top_chunks:
                            return "No relevant information found in the available documents."
                        
                        # Format the context
                        context = "\n\n".join([chunk[0]['content'] for chunk in top_chunks])
                        return context
                    else:
                        print("No FAISS results found, falling back to keyword matching")
                else:
                    print("Failed to generate query embedding, falling back to keyword matching")
            else:
                print("No valid embeddings found, falling back to keyword matching")
        else:
            print("Vector search not available, using keyword matching")
            
        # Fall back to keyword matching
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'in', 'to', 'for'}
        keywords = [word for word in query.split() if word not in stop_words]
        
        # Find relevant chunks that contain at least one keyword
        relevant_chunks = []
        
        for chunk in chunks:
            chunk_content = chunk['content'].lower()
            matching_keywords = [kw for kw in keywords if kw in chunk_content]
            
            if matching_keywords:
                # Calculate a simple relevance score based on number of keyword matches
                score = len(matching_keywords)
                relevant_chunks.append((chunk, score))
        
        # Sort by relevance score
        relevant_chunks.sort(key=lambda x: x[1], reverse=True)
        
        # Get top results
        top_chunks = relevant_chunks[:num_results]
        
        if not top_chunks:
            return "No relevant information found in the available documents."
        
        # Format the context
        context = "\n\n".join([chunk[0]['content'] for chunk in top_chunks])
        return context
        
    except Exception as e:
        print(f"Error retrieving document context: {e}")
        return "Error retrieving document context."

async def process_chat_message(user_message: str, conversation_history: List[Dict[str, Any]], tenant_id: str, session_id: str):
    """
    Process a chat message using the LLM and retrieve relevant context from documents.
    """
    # Get tenant information
    db = get_sqlite_client()
    tenant_response = db.table('tenants').select('*').eq('id', tenant_id).execute()
    
    if not tenant_response.data:
        raise ValueError("Tenant not found")
    
    tenant = tenant_response.data[0]
    
    # Retrieve relevant context from documents
    context = await retrieve_relevant_context(user_message, tenant_id)
    
    # Format conversation history
    messages = []
    
    # Add system message with context
    system_message = {
        "role": "system",
        "content": f"""You are a professional, friendly AI assistant representing {tenant['name']}. 
        Your role is to help customers by answering questions, providing support, and promoting the company's products or services in a helpful and respectful manner.

        Always begin with a warm greeting and clearly introduce yourself as part of the {tenant['name']} support team.

        Below is information from {tenant['name']}'s knowledge base that may help address the user's question:

        {context}

        If the knowledge base doesn't fully answer the question, use your general understanding — but only within the scope of {tenant['name']}'s business, offerings, and customer needs.

        Do not answer questions that are unrelated to the company, its services, or customer support. For example, do not engage in topics like politics, celebrities, or general trivia (e.g., “Who is Donald Trump?”). Politely steer the conversation back to how you can assist with {tenant['name']}.

        If the business sells services or products, highlight their value where appropriate. Be informative and persuasive — help customers feel confident in choosing {tenant['name']} without sounding pushy.

        If scheduling or booking is mentioned and calendar integration is enabled, assist using Google Calendar.

        Maintain a polite, professional, and supportive tone. If you are unsure about something, be transparent and suggest helpful next steps when possible.

        You represent the voice and quality of the brand. Be accurate, respectful, and helpful at all times.
        """
    }

    messages.append(system_message)
    
    # Add conversation history
    for msg in conversation_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add the current user message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # Call the LLM API (assumed to be OpenAI compatible)
    try:
        # For demo purposes, check if we have a valid API key
        if not settings.MCP_API_KEY or settings.MCP_API_KEY.startswith("your_") or settings.MCP_API_KEY == "":
            # If no valid API key, generate a demo response
            return generate_demo_response(user_message, tenant['name'], context)
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.MCP_API_KEY}"
                },
                json={
                    "model": "gpt-4.1-nano-2025-04-14",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                }
            )
            
            response_data = response.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                assistant_message = response_data["choices"][0]["message"]["content"]
                return assistant_message
            else:
                raise ValueError("Invalid response from LLM API")
    
    except Exception as e:
        print(f"Error in LLM API call: {e}")
        # Log additional information to help debug API issues
        print(f"Using model: gpt-4.1-nano-2025-04-14 with API key starting with: {settings.MCP_API_KEY[:8]}...")
        # For demo purposes, return a fallback response
        return generate_demo_response(user_message, tenant['name'], context)

def generate_demo_response(user_message: str, tenant_name: str, context: str) -> str:
    """
    Generate a demo response when LLM API is not available.
    This simulates what the GPT-4.1-nano-2025-04-14 model would return based on the context.
    """
    # Check if context contains relevant information
    if context == "No processed documents available for this tenant.":
        return f"Hello! I'm the AI assistant for {tenant_name}. I don't have any specific information in my knowledge base yet. Is there something else I can help you with?"
    
    if context == "No relevant information found in the available documents.":
        return f"Hello! I'm the AI assistant for {tenant_name}. I searched our knowledge base but couldn't find information relevant to your question. Can I help you with something else?"
    
    # If we have error context
    if context.startswith("Error"):
        return f"Hello! I'm the AI assistant for {tenant_name}. I'm currently having trouble accessing my knowledge base. Is there something general I can help you with?"
    
    # If we have actual context, create a simple response
    # This is just a demo, so we'll keep it simple
    user_message_lower = user_message.lower()
    
    # Simple keyword matching
    if "who" in user_message_lower and "you" in user_message_lower:
        return f"I'm an AI assistant for {tenant_name}, designed to help answer your questions using information from our knowledge base."
    
    if "what" in user_message_lower and "do" in user_message_lower and "you" in user_message_lower:
        return f"I can help answer questions about {tenant_name} using our knowledge base. You can ask me about our products, services, or any other information you need."
    
    # Default response that mentions the context
    return f"Based on {tenant_name}'s information, I found some relevant details that might help: \n\n{context}\n\nIs there anything specific you'd like to know more about?"

async def handle_calendar_booking(user_message: str, tenant_id: str, user_email: str = None):
    """
    Handle calendar booking requests.
    This is a placeholder for the Google Calendar integration.
    """
    # This would be implemented to parse booking requests and create Google Calendar events
    pass
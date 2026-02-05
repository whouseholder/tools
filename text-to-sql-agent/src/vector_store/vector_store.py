"""Vector store management for Q&A and metadata."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from sentence_transformers import SentenceTransformer
from loguru import logger

from ..utils.config import VectorStoreConfig


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    def add_qa_pair(
        self,
        question: str,
        answer: str,
        sql_query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a Q&A pair to the vector store."""
        pass
    
    @abstractmethod
    def search_similar_questions(
        self,
        question: str,
        top_k: int = 5,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar questions."""
        pass
    
    @abstractmethod
    def add_metadata(
        self,
        table_name: str,
        columns: List[Dict[str, Any]],
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add table metadata to the vector store."""
        pass
    
    @abstractmethod
    def search_relevant_metadata(
        self,
        question: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for relevant table metadata."""
        pass


class SimpleVectorStore(VectorStore):
    """Simple in-memory vector store using numpy and sklearn (Python 3.14 compatible)."""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize simple vector store."""
        self.config = config
        self.embedding_model = SentenceTransformer(config.embedding_model)
        
        # In-memory storage
        self.qa_pairs = []
        self.qa_embeddings = []
        self.metadata_entries = []
        self.metadata_embeddings = []
        
        # Persistence directory
        persist_dir = config.simple.get("persist_directory", "./data/vector_db/simple")
        os.makedirs(persist_dir, exist_ok=True)
        self.persist_dir = persist_dir
        
        # Load existing data if available
        self._load_from_disk()
        
        logger.info(f"Initialized Simple vector store at {persist_dir}")
    
    def _save_to_disk(self):
        """Save data to disk."""
        try:
            # Save Q&A pairs
            qa_path = os.path.join(self.persist_dir, "qa_pairs.json")
            with open(qa_path, 'w') as f:
                json.dump(self.qa_pairs, f, indent=2)
            
            # Save Q&A embeddings
            if self.qa_embeddings:
                np.save(os.path.join(self.persist_dir, "qa_embeddings.npy"), 
                       np.array(self.qa_embeddings))
            
            # Save metadata
            meta_path = os.path.join(self.persist_dir, "metadata.json")
            with open(meta_path, 'w') as f:
                json.dump(self.metadata_entries, f, indent=2)
            
            # Save metadata embeddings
            if self.metadata_embeddings:
                np.save(os.path.join(self.persist_dir, "metadata_embeddings.npy"),
                       np.array(self.metadata_embeddings))
        except Exception as e:
            logger.warning(f"Failed to save vector store to disk: {e}")
    
    def _load_from_disk(self):
        """Load data from disk if it exists."""
        try:
            # Load Q&A pairs
            qa_path = os.path.join(self.persist_dir, "qa_pairs.json")
            if os.path.exists(qa_path):
                with open(qa_path, 'r') as f:
                    self.qa_pairs = json.load(f)
            
            # Load Q&A embeddings
            qa_emb_path = os.path.join(self.persist_dir, "qa_embeddings.npy")
            if os.path.exists(qa_emb_path):
                self.qa_embeddings = np.load(qa_emb_path).tolist()
            
            # Load metadata
            meta_path = os.path.join(self.persist_dir, "metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    self.metadata_entries = json.load(f)
            
            # Load metadata embeddings
            meta_emb_path = os.path.join(self.persist_dir, "metadata_embeddings.npy")
            if os.path.exists(meta_emb_path):
                self.metadata_embeddings = np.load(meta_emb_path).tolist()
            
            if self.qa_pairs:
                logger.info(f"Loaded {len(self.qa_pairs)} Q&A pairs from disk")
            if self.metadata_entries:
                logger.info(f"Loaded {len(self.metadata_entries)} metadata entries from disk")
        except Exception as e:
            logger.warning(f"Failed to load vector store from disk: {e}")
    
    def add_qa_pair(
        self,
        question: str,
        answer: str,
        sql_query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a Q&A pair to the vector store."""
        # Generate embedding
        embedding = self.embedding_model.encode(question).tolist()
        
        # Create document ID
        doc_id = f"qa_{len(self.qa_pairs)}"
        
        # Store data
        qa_data = {
            'id': doc_id,
            'question': question,
            'answer': answer,
            'sql_query': sql_query,
            'metadata': metadata or {}
        }
        
        self.qa_pairs.append(qa_data)
        self.qa_embeddings.append(embedding)
        
        # Save to disk
        self._save_to_disk()
        
        logger.debug(f"Added Q&A pair: {doc_id}")
        return doc_id
    
    def search_similar_questions(
        self,
        question: str,
        top_k: int = 5,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar questions."""
        if not self.qa_pairs:
            return []
        
        # Generate embedding
        query_embedding = self.embedding_model.encode(question).reshape(1, -1)
        
        # Use config threshold if not provided
        if threshold is None:
            threshold = self.config.similarity_threshold
        
        # Calculate cosine similarity
        embeddings_array = np.array(self.qa_embeddings)
        similarities = cosine_similarity(query_embedding, embeddings_array)[0]
        
        # Get top-k results above threshold
        similar_questions = []
        for idx in np.argsort(similarities)[::-1][:top_k]:
            similarity = float(similarities[idx])
            if similarity >= threshold:
                qa_data = self.qa_pairs[idx]
                similar_questions.append({
                    'id': qa_data['id'],
                    'question': qa_data['question'],
                    'similarity': similarity,
                    'metadata': {
                        'answer': qa_data['answer'],
                        'sql_query': qa_data['sql_query'],
                        **qa_data.get('metadata', {})
                    }
                })
        
        logger.debug(f"Found {len(similar_questions)} similar questions for: {question[:50]}...")
        return similar_questions
    
    def add_metadata(
        self,
        table_name: str,
        columns: List[Dict[str, Any]],
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add table metadata to the vector store."""
        # Create searchable text
        text_parts = [f"Table: {table_name}"]
        
        if description:
            text_parts.append(f"Description: {description}")
        
        text_parts.append("Columns:")
        for col in columns:
            col_text = f"  - {col['name']} ({col['type']})"
            if col.get('description'):
                col_text += f": {col['description']}"
            text_parts.append(col_text)
        
        searchable_text = "\n".join(text_parts)
        
        # Generate embedding
        embedding = self.embedding_model.encode(searchable_text).tolist()
        
        # Create document ID
        doc_id = f"meta_{table_name}"
        
        # Store data
        meta_data = {
            'id': doc_id,
            'table_name': table_name,
            'description': description or "",
            'columns': columns,
            'searchable_text': searchable_text,
            'metadata': metadata or {}
        }
        
        self.metadata_entries.append(meta_data)
        self.metadata_embeddings.append(embedding)
        
        # Save to disk
        self._save_to_disk()
        
        logger.debug(f"Added metadata for table: {table_name}")
        return doc_id
    
    def search_relevant_metadata(
        self,
        question: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for relevant table metadata."""
        if not self.metadata_entries:
            return []
        
        # Generate embedding
        query_embedding = self.embedding_model.encode(question).reshape(1, -1)
        
        # Calculate cosine similarity
        embeddings_array = np.array(self.metadata_embeddings)
        relevances = cosine_similarity(query_embedding, embeddings_array)[0]
        
        # Get top-k results
        relevant_metadata = []
        for idx in np.argsort(relevances)[::-1][:top_k]:
            relevance = float(relevances[idx])
            meta_data = self.metadata_entries[idx]
            relevant_metadata.append({
                'id': meta_data['id'],
                'table_name': meta_data['table_name'],
                'description': meta_data['description'],
                'columns': meta_data['columns'],
                'relevance': relevance,
                'searchable_text': meta_data['searchable_text']
            })
        
        logger.debug(f"Found {len(relevant_metadata)} relevant tables for question")
        return relevant_metadata


class QdrantVectorStore(VectorStore):
    """Qdrant implementation of vector store."""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize Qdrant vector store."""
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct
        
        self.config = config
        self.embedding_model = SentenceTransformer(config.embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize Qdrant client (in-memory mode for local development)
        persist_dir = config.qdrant.get("persist_directory", "./data/vector_db/qdrant")
        os.makedirs(persist_dir, exist_ok=True)
        
        self.client = QdrantClient(path=persist_dir)
        
        # Collection names
        self.qa_collection_name = config.qdrant.get("collection_name", "text_to_sql") + "_qa"
        self.metadata_collection_name = config.qdrant.get("collection_name", "text_to_sql") + "_metadata"
        
        # Create collections if they don't exist
        try:
            self.client.get_collection(self.qa_collection_name)
        except:
            self.client.create_collection(
                collection_name=self.qa_collection_name,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE)
            )
        
        try:
            self.client.get_collection(self.metadata_collection_name)
        except:
            self.client.create_collection(
                collection_name=self.metadata_collection_name,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE)
            )
        
        logger.info(f"Initialized Qdrant vector store at {persist_dir}")
    
    def add_qa_pair(
        self,
        question: str,
        answer: str,
        sql_query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a Q&A pair to the vector store."""
        from qdrant_client.models import PointStruct
        
        # Generate embedding
        embedding = self.embedding_model.encode(question).tolist()
        
        # Create document ID
        doc_id = abs(hash(question + sql_query)) % (10 ** 10)
        
        # Prepare payload
        payload = metadata or {}
        payload.update({
            "question": question,
            "answer": answer,
            "sql_query": sql_query,
            "type": "qa_pair"
        })
        
        # Add to collection
        self.client.upsert(
            collection_name=self.qa_collection_name,
            points=[PointStruct(id=doc_id, vector=embedding, payload=payload)]
        )
        
        logger.debug(f"Added Q&A pair: {doc_id}")
        return str(doc_id)
    
    def search_similar_questions(
        self,
        question: str,
        top_k: int = 5,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar questions."""
        # Generate embedding
        embedding = self.embedding_model.encode(question).tolist()
        
        # Use config threshold if not provided
        if threshold is None:
            threshold = self.config.similarity_threshold
        
        # Query collection
        results = self.client.search(
            collection_name=self.qa_collection_name,
            query_vector=embedding,
            limit=top_k
        )
        
        # Format results
        similar_questions = []
        for result in results:
            similarity = result.score
            
            if similarity >= threshold:
                similar_questions.append({
                    'id': str(result.id),
                    'question': result.payload.get('question'),
                    'similarity': similarity,
                    'metadata': {
                        'answer': result.payload.get('answer'),
                        'sql_query': result.payload.get('sql_query')
                    }
                })
        
        logger.debug(f"Found {len(similar_questions)} similar questions for: {question[:50]}...")
        return similar_questions
    
    def add_metadata(
        self,
        table_name: str,
        columns: List[Dict[str, Any]],
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add table metadata to the vector store."""
        from qdrant_client.models import PointStruct
        
        # Create searchable text from table metadata
        text_parts = [f"Table: {table_name}"]
        
        if description:
            text_parts.append(f"Description: {description}")
        
        text_parts.append("Columns:")
        for col in columns:
            col_text = f"  - {col['name']} ({col['type']})"
            if col.get('description'):
                col_text += f": {col['description']}"
            text_parts.append(col_text)
        
        searchable_text = "\n".join(text_parts)
        
        # Generate embedding
        embedding = self.embedding_model.encode(searchable_text).tolist()
        
        # Create document ID
        doc_id = abs(hash(table_name)) % (10 ** 10)
        
        # Prepare payload
        payload = metadata or {}
        payload.update({
            "table_name": table_name,
            "description": description or "",
            "columns": columns,
            "searchable_text": searchable_text,
            "type": "metadata"
        })
        
        # Add to collection
        self.client.upsert(
            collection_name=self.metadata_collection_name,
            points=[PointStruct(id=doc_id, vector=embedding, payload=payload)]
        )
        
        logger.debug(f"Added metadata for table: {table_name}")
        return str(doc_id)
    
    def search_relevant_metadata(
        self,
        question: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for relevant table metadata."""
        # Generate embedding
        embedding = self.embedding_model.encode(question).tolist()
        
        # Query collection
        results = self.client.search(
            collection_name=self.metadata_collection_name,
            query_vector=embedding,
            limit=top_k
        )
        
        # Format results
        relevant_metadata = []
        for result in results:
            relevance = result.score
            
            relevant_metadata.append({
                'id': str(result.id),
                'table_name': result.payload.get('table_name'),
                'description': result.payload.get('description'),
                'columns': result.payload.get('columns', []),
                'relevance': relevance,
                'searchable_text': result.payload.get('searchable_text')
            })
        
        logger.debug(f"Found {len(relevant_metadata)} relevant tables for question")
        return relevant_metadata


class ChromaDBVectorStore(VectorStore):
    """ChromaDB implementation of vector store."""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize ChromaDB vector store."""
        import chromadb
        
        self.config = config
        self.embedding_model = SentenceTransformer(config.embedding_model)
        
        # Initialize ChromaDB client (newer version)
        persist_dir = config.chromadb.get("persist_directory", "./data/vector_db/chroma")
        os.makedirs(persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Get or create collections
        collection_name = config.chromadb.get("collection_name", "text_to_sql")
        self.qa_collection = self.client.get_or_create_collection(
            name=f"{collection_name}_qa",
            metadata={"description": "Q&A pairs"}
        )
        self.metadata_collection = self.client.get_or_create_collection(
            name=f"{collection_name}_metadata",
            metadata={"description": "Table metadata"}
        )
        
        logger.info(f"Initialized ChromaDB vector store at {persist_dir}")
    
    def add_qa_pair(
        self,
        question: str,
        answer: str,
        sql_query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a Q&A pair to the vector store."""
        # Generate embedding
        embedding = self.embedding_model.encode(question).tolist()
        
        # Create document
        doc_id = f"qa_{hash(question + sql_query)}"
        
        meta = metadata or {}
        meta.update({
            "answer": answer,
            "sql_query": sql_query,
            "type": "qa_pair"
        })
        
        # Add to collection
        self.qa_collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[question],
            metadatas=[meta]
        )
        
        logger.debug(f"Added Q&A pair: {doc_id}")
        return doc_id
    
    def search_similar_questions(
        self,
        question: str,
        top_k: int = 5,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar questions."""
        # Generate embedding
        embedding = self.embedding_model.encode(question).tolist()
        
        # Use config threshold if not provided
        if threshold is None:
            threshold = self.config.similarity_threshold
        
        # Query collection
        results = self.qa_collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )
        
        # Format results
        similar_questions = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i] if results['distances'] else 1.0
                similarity = 1.0 - distance  # Convert distance to similarity
                
                if similarity >= threshold:
                    similar_questions.append({
                        'id': doc_id,
                        'question': results['documents'][0][i],
                        'similarity': similarity,
                        'metadata': results['metadatas'][0][i]
                    })
        
        logger.debug(f"Found {len(similar_questions)} similar questions for: {question[:50]}...")
        return similar_questions
    
    def add_metadata(
        self,
        table_name: str,
        columns: List[Dict[str, Any]],
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add table metadata to the vector store."""
        # Create searchable text from table metadata
        text_parts = [f"Table: {table_name}"]
        
        if description:
            text_parts.append(f"Description: {description}")
        
        text_parts.append("Columns:")
        for col in columns:
            col_text = f"  - {col['name']} ({col['type']})"
            if col.get('description'):
                col_text += f": {col['description']}"
            text_parts.append(col_text)
        
        searchable_text = "\n".join(text_parts)
        
        # Generate embedding
        embedding = self.embedding_model.encode(searchable_text).tolist()
        
        # Create document
        doc_id = f"meta_{table_name}"
        
        meta = metadata or {}
        meta.update({
            "table_name": table_name,
            "description": description or "",
            "columns": str(columns),  # Store as string for ChromaDB
            "type": "metadata"
        })
        
        # Add to collection
        self.metadata_collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[searchable_text],
            metadatas=[meta]
        )
        
        logger.debug(f"Added metadata for table: {table_name}")
        return doc_id
    
    def search_relevant_metadata(
        self,
        question: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for relevant table metadata."""
        # Generate embedding
        embedding = self.embedding_model.encode(question).tolist()
        
        # Query collection
        results = self.metadata_collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )
        
        # Format results
        relevant_metadata = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i] if results['distances'] else 1.0
                relevance = 1.0 - distance
                
                # Parse columns back from string
                import ast
                meta = results['metadatas'][0][i]
                try:
                    columns = ast.literal_eval(meta.get('columns', '[]'))
                except:
                    columns = []
                
                relevant_metadata.append({
                    'id': doc_id,
                    'table_name': meta.get('table_name'),
                    'description': meta.get('description'),
                    'columns': columns,
                    'relevance': relevance,
                    'searchable_text': results['documents'][0][i]
                })
        
        logger.debug(f"Found {len(relevant_metadata)} relevant tables for question")
        return relevant_metadata


class PineconeVectorStore(VectorStore):
    """Pinecone implementation of vector store (placeholder for future implementation)."""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize Pinecone vector store."""
        raise NotImplementedError("Pinecone implementation coming soon")
    
    def add_qa_pair(self, question: str, answer: str, sql_query: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        raise NotImplementedError()
    
    def search_similar_questions(self, question: str, top_k: int = 5, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError()
    
    def add_metadata(self, table_name: str, columns: List[Dict[str, Any]], description: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        raise NotImplementedError()
    
    def search_relevant_metadata(self, question: str, top_k: int = 10) -> List[Dict[str, Any]]:
        raise NotImplementedError()


def create_vector_store(config: VectorStoreConfig) -> VectorStore:
    """Factory function to create vector store based on configuration."""
    if config.provider == "simple":
        return SimpleVectorStore(config)
    elif config.provider == "chromadb":
        return ChromaDBVectorStore(config)
    elif config.provider == "qdrant":
        return QdrantVectorStore(config)
    elif config.provider == "pinecone":
        return PineconeVectorStore(config)
    else:
        raise ValueError(f"Unsupported vector store provider: {config.provider}")

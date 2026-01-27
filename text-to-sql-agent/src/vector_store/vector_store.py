"""Vector store management for Q&A and metadata."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings
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


class ChromaDBVectorStore(VectorStore):
    """ChromaDB implementation of vector store."""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize ChromaDB vector store."""
        self.config = config
        self.embedding_model = SentenceTransformer(config.embedding_model)
        
        # Initialize ChromaDB client
        persist_dir = config.chromadb.get("persist_directory", "./data/vector_db/chroma")
        self.client = chromadb.Client(Settings(
            persist_directory=persist_dir,
            anonymized_telemetry=False
        ))
        
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
    if config.provider == "chromadb":
        return ChromaDBVectorStore(config)
    elif config.provider == "pinecone":
        return PineconeVectorStore(config)
    else:
        raise ValueError(f"Unsupported vector store provider: {config.provider}")

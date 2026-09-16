## Current Features

### Agent
- Async agent loop with Ollama
- Tool calling
- Tool registry with automatic JSON schema generation
- Tool timeout and retry handling
- Tool groups / capability control

### Conversation Memory
- Session-based conversation history
- Redis persistence
- Memory trimming
- Session isolation

### RAG
- Document loading and chunking
- Ollama embeddings with `nomic-embed-text`
- Chroma persistent vector store
- Cosine similarity search
- Top-K retrieval
- Score threshold filtering
- Source metadata tracking
- RAG service
- RAG exposed as an Agent tool

### Long-term Memory
- User-based persistent memory
- Separate `user_id` and `session_id`
- Automatic memory extraction from user messages
- Cross-session memory
- Memory update and merge
- Explicit memory forgetting
- Per-user concurrency lock
- Redis persistence
- Long-term memory and RAG separation


Before

Agent.run()
├── LLM
├── Tool detection
├── Tool execution
├── Loop
├── max_steps
└── Return


After

Agent
  ↓
AgentWorkflow
  ↓
AgentState
  │
  ├── messages
  ├── tool_calls
  └── step
  ↓
LLMNode
  ↓
tool_calls?
 ├── No  → END
 └── Yes → ToolNode
              ↓
          ToolRegistry
              ↓
           LLMNode
## Architecture

```mermaid
flowchart TB
    User["User / API Client"]
    API["FastAPI<br/>/chat"]

    subgraph AgentSystem["Agent System"]
        Agent["Agent<br/>High-level interface"]

        subgraph Workflow["AgentWorkflow"]
            State["AgentState<br/>messages<br/>tool_calls<br/>step"]

            LLMNode["LLMNode"]
            Decision{"Tool calls?"}
            ToolNode["ToolNode"]
            End["END"]

            LLMNode --> Decision
            Decision -->|Yes| ToolNode
            ToolNode --> LLMNode
            Decision -->|No| End

            State <--> LLMNode
            State <--> ToolNode
        end

        Agent --> Workflow
    end

    subgraph ToolSystem["Tool System"]
        Registry["ToolRegistry<br/>validation<br/>timeout<br/>retry"]
        Time["get_current_time"]
        Weather["get_weather"]
        RAGTool["search_knowledge_base"]

        Registry --> Time
        Registry --> Weather
        Registry --> RAGTool
    end

    subgraph RAG["RAG System"]
        RAGService["RAGService"]
        Retriever["Retriever"]
        Embedding["EmbeddingClient"]
        Chroma["Chroma<br/>Vector Database"]
        Documents["Documents"]

        RAGService --> Retriever
        Retriever --> Embedding
        Retriever --> Chroma
        Documents --> Chroma
    end

    subgraph Memory["Long-term Memory"]
        MemoryService["MemoryService"]
        Extractor["MemoryExtractor"]
        MemoryRedis["RedisMemoryStore"]

        MemoryService --> Extractor
        MemoryService --> MemoryRedis
    end

    subgraph Session["Session Memory"]
        SessionManager["SessionManager"]
        SessionRedis["RedisSessionStore"]

        SessionManager --> SessionRedis
    end

    subgraph LLM["LLM"]
        Ollama["OllamaClient"]
        Model["Ollama Model"]

        Ollama --> Model
    end

    User --> API
    API --> Agent

    Agent --> MemoryService
    Agent --> SessionManager

    LLMNode --> Ollama
    ToolNode --> Registry

    RAGTool --> RAGService
```
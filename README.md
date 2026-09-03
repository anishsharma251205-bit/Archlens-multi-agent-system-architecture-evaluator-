# ArchLens - Multi-Agent System Architecture Evaluator

ArchLens is a multi-agent AI system that evaluates software architectures across five engineering dimensions:

- Structure
- Security
- Scalability
- Performance
- Cost

It supports both text-based architecture evaluation and diagram/image-based evaluation using a dedicated vision pipeline.

The goal is to turn an architecture description or diagram into a structured engineering review with scores, issues, recommendations, and an overall architecture score.

## Problem

Architecture reviews are usually manual and depend heavily on the experience of the reviewer.

A system may look reasonable at a high level but still have problems such as:

- Missing components or unclear service boundaries
- Security weaknesses
- Scalability bottlenecks
- Performance risks
- Unnecessary infrastructure cost
- Poor observability
- Database resilience issues

ArchLens automates this review by splitting the evaluation into multiple specialized agents instead of asking a single LLM to evaluate everything.

## Architecture

```mermaid
flowchart TD
    A[Architecture Input] --> B[Complexity Classification]

    A --> V[Vision Pipeline]
    V --> B

    B --> C[Agent Orchestrator]

    C --> D[Structure Agent]
    C --> E[Security Agent]
    C --> F[Scalability Agent]
    C --> G[Performance Agent]
    C --> H[Cost Agent]

    D --> I[RAG / FAISS]
    E --> I
    F --> I
    G --> I
    H --> I

    I --> J[Text Model Router]

    J --> K[Guardrail Validation]

    K -->|Invalid Output| L[Retry / Fallback]
    L --> J

    K -->|Valid Output| M[Scoring Engine]

    M --> N[Final Report]

    N --> O[MLOps Tracker]
    O --> P[(SQLite)]

    P --> Q[Analytics Dashboard]
```

## How It Works

### 1. Architecture Input

The user can provide an architecture description for evaluation.

ArchLens can also work with an architecture diagram or image.

For text-based input:

```
Text Input
    |
    v
Complexity Classification
    |
    v
Multi-Agent Evaluation
```

For diagram-based input:

```
Architecture Diagram
    |
    v
Vision Pipeline
    |
    v
Architecture Information
    |
    v
Complexity Classification
    |
    v
Multi-Agent Evaluation
```

The two input paths eventually converge into the same multi-agent evaluation pipeline.

### 2. Complexity Classification

The architecture is first classified based on its complexity.

The classification determines how text-model requests are routed.

```
Simple / Medium
       |
       v
Ollama
       |
       v
Local Mistral
```

```
Complex
       |
       v
OpenRouter
       |
       v
Configured Cloud Model
```

Fallback mechanisms are available when a selected model fails.

### 3. Vision and Diagram Processing

ArchLens includes a dedicated vision pipeline for architecture diagrams.

The vision pipeline is separated from the text-agent routing system because diagram understanding requires multimodal models, while the five engineering agents primarily perform text-based architecture reasoning.

The vision pipeline supports both local and cloud execution.

```
Architecture Diagram
        |
        v
Dedicated Vision Router
        |
        +-----------------------------+
        |                             |
        v                             v
Local Environment               Cloud Environment
        |                             |
        v                             v
Ollama + LLaVA             OpenRouter Vision Pool
        |                             |
        +-------------+---------------+
                      |
                      v
          Architecture Description
                      |
                      v
            Text Evaluation Pipeline
```

### 4. Local LLaVA Vision Pipeline

During local development, ArchLens uses LLaVA through Ollama for diagram understanding.

```
Architecture Diagram
        |
        v
       LLaVA
        |
        v
Ollama Local Inference
        |
        v
Visual Architecture Understanding
        |
        v
Architecture Description
        |
        v
Five-Agent Evaluation
```

LLaVA is responsible for interpreting the visual architecture and converting the diagram into architecture information that can be processed by the downstream evaluation agents.

The local LLaVA setup is intended primarily for development and local execution.

### 5. Cloud Vision Pipeline

For cloud deployment, ArchLens uses a dedicated OpenRouter vision-model pool.

The vision model pool is intentionally separate from the text and agent model pool.

Example configuration:

```
# TEXT / AGENT MODELS
OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free
OPENROUTER_FALLBACK_MODELS=google/gemma-4-26b-a4b-it:free;z-ai/glm-5.2:free

# VISION / DIAGRAM MODELS
OPENROUTER_VISION_MODEL=google/gemma-4-26b-a4b-it:free
OPENROUTER_VISION_FALLBACK_MODELS=google/gemma-4-31b-it:free;nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free

# ENVIRONMENT
ARCHLENS_ENV=cloud
```

The vision pipeline therefore has its own model configuration and fallback chain.

### 6. Vision Model Fallback

ArchLens attempts configured vision models sequentially.

```
Architecture Diagram
        |
        v
Vision Model 1
        |
        +---- Success ----> Architecture Description
        |
        +---- Failure
                |
                v
        Vision Model 2
                |
                +---- Success ----> Architecture Description
                |
                +---- Failure
                        |
                        v
                Vision Model 3
                        |
                        v
                     Success
                        |
                        v
              Architecture Description
```

This provides resilience against:

- Provider rate limits
- Temporary provider failures
- API errors
- Model availability issues
- Failed vision requests

During testing, the first two configured OpenRouter vision models returned upstream 429 rate-limit responses. ArchLens automatically moved to the next configured vision model, and the third vision model successfully processed the architecture diagram.

This allows the architecture evaluation to continue even when an individual vision provider or model is temporarily unavailable.

### 7. Text and Vision Model Routing

ArchLens maintains two independent model-routing paths.

**Text and Agent Routing**

```
Architecture Text
       |
       v
Complexity Classification
       |
       v
Text Model Router
       |
       +---- Simple / Medium ----> Ollama
       |
       +---- Complex ------------> OpenRouter
       |
       v
Five Evaluation Agents
```

**Vision Routing**

```
Architecture Diagram
       |
       v
Vision Model Router
       |
       +---- Local ----> Ollama + LLaVA
       |
       +---- Cloud ----> OpenRouter Vision Pool
       |
       v
Architecture Description
       |
       v
Text Evaluation Pipeline
```

This separation allows ArchLens to independently configure, monitor, and replace vision models without changing the text-agent routing system.

### 8. Five Specialized Agents

ArchLens uses five independent evaluation agents.

**Structure Agent**

The Structure Agent checks:

- Component organization
- Service boundaries
- Communication patterns
- Architectural clarity
- Overall system organization

**Security Agent**

The Security Agent checks:

- Authentication
- Authorization
- Data protection
- Attack surfaces
- Security controls
- Security weaknesses

**Scalability Agent**

The Scalability Agent checks:

- Horizontal scaling
- Bottlenecks
- Load handling
- Service scalability
- Scaling strategies

**Performance Agent**

The Performance Agent checks:

- Latency
- Throughput
- Database access
- Caching
- Processing bottlenecks
- Performance risks

**Cost Agent**

The Cost Agent checks:

- Infrastructure usage
- Unnecessary services
- Resource consumption
- Infrastructure efficiency
- Potential cost optimization

### 9. Concurrent Agent Execution

The five agents are executed concurrently using Python's ThreadPoolExecutor.

Instead of waiting for each agent sequentially:

- Structure
- Security
- Scalability
- Performance
- Cost

the system runs the independent agent evaluations concurrently.

```
                 Agent Orchestrator
                        |
        +---------------+---------------+
        |       |       |       |       |
        v       v       v       v       v
    Structure Security Scale Performance Cost
        |       |       |       |       |
        +-------+-------+-------+-------+
                        |
                        v
                  Scoring Engine
```

Each agent independently goes through the retrieval, model routing, validation, and scoring pipeline.

Concurrent execution reduces unnecessary waiting when multiple independent evaluations are required.

### 10. RAG and FAISS

ArchLens uses a knowledge base containing architecture best practices.

The knowledge base is indexed using FAISS, with embeddings generated using Hugging Face and SentenceTransformers.

During evaluation:

```
Agent Query
    |
    v
Embedding Generation
    |
    v
FAISS Retrieval
    |
    v
Relevant Best Practices
    |
    v
LLM
    |
    v
Evaluation
```

The retrieved context helps the agents ground their recommendations in predefined architectural practices instead of relying entirely on model-generated reasoning.

### 11. LLM Routing

ArchLens supports different model providers depending on the evaluation requirements.

**Local Models**

Ollama is used for local inference.

Current local models include:

- Mistral for text-based architecture evaluation
- LLaVA for image and diagram analysis

**OpenRouter**

OpenRouter is used for cloud-based model inference, particularly for more complex evaluations and cloud-based vision processing.

The routing system supports:

- Multiple OpenRouter text models
- Multiple OpenRouter vision models
- Retry logic
- Request timeouts
- Fallback models
- Ollama fallback

The actual model used during an evaluation is tracked by the MLOps system.

### 12. Guardrails

LLM responses are validated before they are accepted by the evaluation pipeline.

The expected output contains:

- score
- issues
- recommendations
- summary

The guardrail checks:

- Output type
- Score range
- Required fields
- Issue structure
- Severity values
- Recommendation validity
- Summary validity

If the model produces invalid output, the system retries the request instead of passing malformed data to the scoring system.

### 13. Scoring

Each agent produces a score between 0 and 10.

The scoring engine combines the five dimensions into a final architecture score.

```
Structure
Security
Scalability
Performance
Cost
       |
       v
Weighted Scoring
       |
       v
Final Architecture Score
```

The final result includes the individual dimension scores and an overall architecture assessment.

### 14. MLOps Tracking

ArchLens tracks evaluation information using SQLite.

The system records information such as:

- Evaluation timestamp
- Architecture complexity
- Model used
- Agent latency
- Agent success
- JSON validity
- Dimension scores
- Final score
- Errors
- Hallucination-related flags

This makes it possible to analyze how the evaluation system behaves over time.

### 15. Analytics Dashboard

The Streamlit analytics dashboard provides visibility into system performance.

It includes:

- System health metrics
- Evaluation score trends
- Complexity distribution
- Model usage
- Quality metrics
- Recent evaluations
- Evaluation history

The dashboard uses Plotly for visualization.

## Image and Diagram Evaluation

ArchLens can evaluate architecture diagrams when the architecture is primarily represented visually.

The complete image evaluation pipeline is:

```
Architecture Diagram
        |
        v
Vision Model
        |
        v
Visual Architecture Understanding
        |
        v
Architecture Description
        |
        v
Complexity Classification
        |
        v
Five-Agent Evaluation
        |
        v
Scoring
        |
        v
Final Report
```

For local execution:

```
Architecture Diagram
        |
        v
LLaVA
        |
        v
Ollama
        |
        v
Architecture Description
```

For cloud execution:

```
Architecture Diagram
        |
        v
Dedicated Vision Router
        |
        v
OpenRouter Vision Model Pool
        |
        v
Fallback Models
        |
        v
Architecture Description
```

The vision model is responsible for visual understanding, while the specialized agents are responsible for engineering evaluation.

## Evaluation Report

After all five agents complete their evaluations, ArchLens generates a structured architecture report.

The report contains:

- Overall architecture score
- Overall summary
- Key issues
- Recommendations
- Individual dimension scores
- Dimension summaries
- Dimension-specific issues
- Dimension-specific recommendations

The application provides separate views for the overall report and detailed dimension breakdown.

```
                 Five Agent Results
                        |
                        v
                 Scoring Engine
                        |
                        v
                Overall Evaluation
                        |
            +-----------+-----------+
            |                       |
            v                       v
       Report View            Breakdown View
            |                       |
            v                       v
    Complete Written          Detailed Agent
       Evaluation              Evaluation
```

## Application Interface

ArchLens currently provides four main application sections:

```
Overview
   |
   v
Report
   |
   v
Breakdown
   |
   v
Export
```

### Overview

The Overview page provides a high-level view of the architecture evaluation.

It includes:

- Overall score
- Dimension scores
- Architecture evaluation summary
- Radar visualization

### Report

The Report page provides the complete written architecture evaluation.

It includes:

- Overall score
- Overall summary
- Key issues
- Recommendations
- Detailed dimension breakdown
- Dimension scores
- Dimension summaries
- Dimension-specific issues
- Dimension-specific recommendations

### Breakdown

The Breakdown page provides a focused view of each individual evaluation dimension.

It allows users to inspect:

- Structure
- Security
- Scalability
- Performance
- Cost

Each dimension contains its own evaluation information, issues, recommendations, and score.

### Export

The Export page allows the evaluation results to be exported as a PDF report.

## Problems Faced During Development

**RAG Model Initialization**

The retriever initially encountered errors where the embedding model was not initialized correctly:

```
'NoneType' object has no attribute 'encode'
```

This was fixed by introducing controlled lazy initialization, validation, and safer shared model and index handling.

**Invalid LLM Responses**

LLMs occasionally returned malformed or unexpected JSON.

The solution was to introduce strict schema validation and retry logic before accepting an agent result.

**Model Attribution During Concurrent Execution**

Because the five agents run concurrently, tracking which model actually produced each result required explicit per-agent model tracking.

The orchestrator now records the actual model used by each agent.

**OpenRouter Failures**

Cloud model requests can fail because of:

- Timeouts
- API errors
- Provider rate limits
- Malformed responses
- Temporary provider failures

The router includes:

- Request timeouts
- Retries
- Retry delays
- Multiple configured models
- Fallback mechanisms
- Ollama fallback

The vision pipeline has an independent fallback chain for multimodal model failures.

**SQLite Analytics**

The analytics system initially encountered errors caused by positional tuple access when the database query structure changed.

The database layer was updated to use SQLite Row objects and named columns, making the analytics code more reliable.

## Project Structure

```
Archlens-multi-agent-system-architecture-evaluator/
|
├── agents/
│   └── orchestrator.py
│
├── core/
│   ├── guardrail.py
│   ├── knowledge_base.py
│   ├── llm_client.py
│   ├── mlops.py
│   ├── models.py
│   ├── prompts.py
│   ├── retriever.py
│   ├── router.py
│   └── scoring.py
│
├── data/
│   ├── best_practices/
│   └── faiss_index/
│
├── mcp_server/
│
├── pages/
│   └── analytics.py
│
├── tests/
│
├── .devcontainer/
│
├── .env.example
├── .gitignore
├── README.md
├── app.py
└── requirements.txt
```

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python |
| UI | Streamlit |
| Agents | Custom Python multi-agent orchestration |
| Agent Concurrency | ThreadPoolExecutor |
| Local Text LLM | Ollama + Mistral |
| Local Vision Model | LLaVA + Ollama |
| Cloud Text LLM | OpenRouter |
| Cloud Vision Models | OpenRouter Vision Model Pool |
| Vision Routing | Dedicated Vision Router + Fallback Models |
| RAG | FAISS |
| Embeddings | Hugging Face / SentenceTransformers |
| Guardrails | Custom Schema Validation + Retry |
| Scoring | Custom Weighted Scoring Engine |
| MLOps | SQLite |
| Analytics | Plotly + Streamlit |

## Local Setup

### 1. Clone the Repository

```
git clone https://github.com/anishsharma251205-bit/Archlens-multi-agent-system-architecture-evaluator-.git

cd Archlens-multi-agent-system-architecture-evaluator-
```

### 2. Create a Virtual Environment

```
python -m venv venv
```

Activate it:

**Windows**

```
venv\Scripts\activate
```

**Linux and macOS**

```
source venv/bin/activate
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file based on `.env.example`.

Configure the required OpenRouter settings if cloud inference is being used.

For cloud deployments, configure both the text model pool and the dedicated vision model pool.

Example:

```
# TEXT / AGENT MODELS
OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free
OPENROUTER_FALLBACK_MODELS=google/gemma-4-26b-a4b-it:free;z-ai/glm-5.2:free

# VISION / DIAGRAM MODELS
OPENROUTER_VISION_MODEL=google/gemma-4-26b-a4b-it:free
OPENROUTER_VISION_FALLBACK_MODELS=google/gemma-4-31b-it:free;nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free

# ENVIRONMENT
ARCHLENS_ENV=cloud
```

### 5. Install Ollama

Install Ollama and pull the models used locally.

For example:

```
ollama pull mistral
ollama pull llava
```

The exact model configuration can be controlled through the project's environment and model configuration.

### 6. Run ArchLens

```
streamlit run app.py
```

## Current Implementation

ArchLens currently includes:

- Multi-agent architecture evaluation
- Five specialized evaluation agents
- Concurrent agent execution
- RAG with FAISS
- Hugging Face embeddings
- Local Mistral inference through Ollama
- Local LLaVA-based image and diagram evaluation through Ollama
- Cloud OpenRouter inference
- Dedicated OpenRouter vision-model routing
- Separate text and vision model pools
- Vision model fallback chains
- Text model fallback chains
- Retry and timeout mechanisms
- Structured LLM output validation
- Guardrails
- Weighted architecture scoring
- SQLite-based MLOps tracking
- Model attribution tracking
- Agent latency tracking
- Streamlit analytics dashboard
- Plotly visualizations
- Evaluation history tracking
- Architecture report generation
- Detailed dimension breakdown
- PDF export

## Future Improvements

Potential future improvements include:

- More specialized architecture agents
- Improved diagram understanding
- More vision models
- Better architecture component extraction
- More advanced RAG retrieval
- Historical architecture comparison
- Improved scoring calibration
- More detailed MLOps metrics
- Additional export formats
- Automated architecture improvement suggestions
- Integration with architecture-as-code tools
- Improved vision model selection
- More advanced multimodal architecture analysis

## Author

Anish Sharma

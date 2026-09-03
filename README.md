after the Mermaid diagram:

# How It Works

## 1. Architecture Input

ArchLens accepts two types of architecture input:

- Text-based architecture descriptions
- Architecture diagrams or images

For text input, the architecture description is directly passed into the evaluation pipeline.

For diagram input, ArchLens first uses a dedicated vision pipeline to understand the architecture and convert the visual information into a structured textual description.

This allows both input types to use the same downstream multi-agent evaluation system.

# Vision Pipeline

The vision pipeline is separated from the normal text-agent pipeline.

```mermaid
flowchart TD
    A[Architecture Diagram] --> B[Vision Model Router]

    B --> C[Local LLaVA]
    B --> D[OpenRouter Vision Pool]

    D --> E[Primary Vision Model]
    E -->|Failure / Rate Limit| F[Vision Fallback Model]

    C --> G[Architecture Description]
    E --> G
    F --> G

    G --> H[Text Evaluation Pipeline]
Local Vision Evaluation

For local execution, ArchLens uses LLaVA through Ollama.

LLaVA is responsible for interpreting the architecture diagram and generating a textual representation of the architecture.

The resulting description is then passed into the normal ArchLens evaluation pipeline.

Architecture Diagram
        |
        v
     LLaVA
    (Ollama)
        |
        v
Architecture Description
        |
        v
Text Evaluation Pipeline

This keeps the vision component independent from the five engineering evaluation agents.

Cloud Vision Evaluation

When running in cloud mode, ArchLens uses a dedicated OpenRouter vision model pool.

The vision pool is separate from the text model pool used by the five evaluation agents.

This separation allows ArchLens to select models based on the type of task being performed instead of forcing the same model to handle both text and image inputs.

The current vision configuration supports a primary model and fallback models.

If a vision model is unavailable or rate-limited, ArchLens automatically attempts another model from the configured vision pool.

Separate Text and Vision Routing

ArchLens maintains two independent model-routing paths.

                 ArchLens
                    |
          +---------+---------+
          |                   |
          v                   v
     Text Pipeline       Vision Pipeline
          |                   |
          v                   v
   Text Model Pool      Vision Model Pool
          |                   |
          v                   v
   Five Agents          Image Analysis
          |                   |
          +---------+---------+
                    |
                    v
              Final Evaluation

This design prevents vision-specific model failures from directly affecting the normal text evaluation pipeline.

Complexity Classification

Before the architecture is evaluated, ArchLens classifies the complexity of the input.

The complexity classification helps determine how the architecture should be routed through the model system.

The system considers the architecture description and identifies whether the problem is relatively simple or requires more complex reasoning.

The classification is then passed to the orchestrator.

Architecture Input
        |
        v
Complexity Classification
        |
        v
Agent Orchestrator
Multi-Agent Evaluation

Instead of using a single LLM to perform the entire architecture review, ArchLens divides the evaluation into five specialized agents.

Each agent focuses on one engineering dimension.

                Orchestrator
                     |
       +------+------+------+------+
       |      |      |      |      |
       v      v      v      v      v
   Structure Security Scalability Performance Cost
Structure Agent

The Structure Agent evaluates the overall organization of the architecture.

It looks for issues such as:

Missing components
Unclear service boundaries
Poor component separation
Architectural inconsistencies
Missing dependencies
Weak communication patterns

The agent produces a structured evaluation containing a score, summary, issues, and recommendations.

Security Agent

The Security Agent evaluates security-related aspects of the architecture.

It considers areas such as:

Authentication and authorization
Data protection
Network security
Access control
Secrets management
Service isolation
Security boundaries

The objective is to identify potential weaknesses before deployment.

Scalability Agent

The Scalability Agent evaluates whether the architecture can handle increasing workload.

It considers factors such as:

Horizontal scaling
Bottlenecks
Statelessness
Database scaling
Load distribution
Caching
Queue-based processing
Service scalability
Performance Agent

The Performance Agent focuses on latency and resource efficiency.

It evaluates:

Request latency
Network communication
Database access
Processing bottlenecks
Caching opportunities
Synchronous versus asynchronous operations
Computational overhead
Cost Agent

The Cost Agent evaluates the economic efficiency of the architecture.

It considers:

Infrastructure requirements
Cloud services
Database costs
Compute requirements
Unnecessary components
Scaling-related costs
Potential resource waste
Concurrent Agent Execution

The five agents are executed concurrently using Python's ThreadPoolExecutor.

Instead of waiting for one agent to finish before starting the next, multiple evaluations can run at the same time.

                Orchestrator
                     |
          +----------+----------+
          |          |          |
          v          v          v
      Structure  Security  Scalability
          |          |          |
          +----------+----------+
                     |
          +----------+----------+
          |                     |
          v                     v
     Performance              Cost

This reduces the overall evaluation latency compared with strictly sequential execution.

RAG and FAISS

ArchLens includes a Retrieval-Augmented Generation layer using FAISS.

The purpose of the RAG layer is to provide relevant architectural knowledge to the evaluation agents.

Agent Query
     |
     v
Embedding Model
     |
     v
FAISS Vector Search
     |
     v
Relevant Context
     |
     v
LLM
     |
     v
Agent Evaluation

The system uses embeddings to represent architectural knowledge and FAISS to retrieve relevant information.

This gives the agents additional context instead of relying entirely on the model's internal knowledge.

LLM Model Routing

ArchLens supports both local and cloud-based model execution.

For local execution, text evaluation can use Ollama-based models.

For cloud execution, ArchLens uses OpenRouter.

The system maintains a separate model pool for text evaluation and vision evaluation.

Text Model Pool

The text model pool is used by:

Structure Agent
Security Agent
Scalability Agent
Performance Agent
Cost Agent
Report generation

A primary model is attempted first.

If the request fails, the router can move to a configured fallback model.

Vision Model Pool

The vision model pool is used only for architecture diagram interpretation.

The current configuration supports:

Primary vision model
Vision fallback models

This prevents text and vision workloads from competing for the same model configuration.

Retry and Fallback System

ArchLens is designed to handle model failures.

A request may fail because of:

Rate limits
Temporary model failures
Invalid responses
API errors
Unexpected model output

The router attempts the next available model when possible.

Model Request
      |
      v
Primary Model
      |
   +--+--+
   |     |
Success Failure
   |     |
   v     v
Output  Fallback
          |
          v
       Next Model

This improves reliability during demonstrations and real evaluations.

Guardrail Validation

LLM-generated outputs are validated before being accepted by the scoring system.

ArchLens checks whether the generated response follows the expected structured format.

The validation process helps detect:

Invalid JSON
Missing fields
Incorrect score formats
Malformed issues
Malformed recommendations
Unexpected model responses

If validation fails, ArchLens can retry the model request or use a fallback model.

Evidence-Aware Evaluation

ArchLens also attempts to distinguish between information that is explicitly present, explicitly absent, and not specified.

For example:

PRESENT
The architecture explicitly contains the feature.

ABSENT
The architecture explicitly states that the feature is missing.

UNSPECIFIED
The architecture does not provide enough information to determine whether it exists.

This prevents the evaluator from automatically treating every unspecified feature as a missing feature.

Scoring Engine

After all five agents complete their evaluations, ArchLens combines their results using a weighted scoring engine.

The system generates:

Individual dimension scores
Overall architecture score
Score label
Final architecture assessment
Structure Score
Security Score
Scalability Score
Performance Score
Cost Score
        |
        v
 Weighted Scoring Engine
        |
        v
 Overall Architecture Score

The scoring system provides a single high-level metric while preserving the individual dimension scores.

Final Report Generation

After scoring, ArchLens generates a structured architecture review.

The final report contains information such as:

Overall architecture score
Architecture summary
Major issues
Recommendations
Dimension-level evaluations

The report is designed to be understandable both as a high-level overview and as a detailed engineering review.

MLOps Tracking

ArchLens tracks evaluation information for monitoring and analysis.

The system records information such as:

Timestamp
Architecture complexity
Model used
Model latency
Evaluation success
JSON validity
Dimension scores
Overall score
Errors
Evaluation-related flags

This information is stored using SQLite.

Evaluation
    |
    v
MLOps Tracker
    |
    v
SQLite
    |
    v
Analytics Dashboard
Analytics Dashboard

The application includes an analytics section for examining evaluation results.

The dashboard can be used to understand:

Architecture scores
Dimension performance
Model behavior
Evaluation latency
Evaluation success
Historical evaluation data

This provides a foundation for monitoring how the evaluator performs over time.

Streamlit Interface

ArchLens uses Streamlit for the user interface.

The application provides separate sections for different stages of the evaluation.

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
Overview

The Overview page provides a high-level view of the architecture evaluation.

It displays:

Overall architecture score
Dimension scores
Visual score representation
Architecture evaluation summary
Report

The Report page presents the generated architecture review.

It includes:

Overall score
Summary
Issues
Recommendations
Detailed dimension breakdown

Each engineering dimension can be inspected individually.

Breakdown

The Breakdown page provides a more detailed view of the five evaluation dimensions.

The user can inspect:

Structure
Security
Scalability
Performance
Cost

Each section provides the corresponding agent's score and evaluation details.

Export

ArchLens supports exporting the evaluation results as a PDF report.

The exported report contains the architecture score and detailed evaluation information.

Project Structure
ArchLens/
|
├── agents/
│   └── orchestrator.py
│
├── core/
│   ├── llm_client.py
│   ├── router.py
│   └── scoring.py
│
├── app.py
├── requirements.txt
├── .env
└── README.md
Core Components
app.py

Responsible for:

Streamlit interface
User input
Diagram upload
Evaluation flow
Results display
Navigation
PDF export
agents/orchestrator.py

Responsible for:

Coordinating the five agents
Running agents concurrently
Collecting agent results
Generating the final report
core/router.py

Responsible for:

Complexity classification
Text model routing
Model fallback
JSON parsing
Output validation
Evidence-aware evaluation
core/llm_client.py

Responsible for:

LLM communication
Local Ollama integration
OpenRouter integration
Vision model communication
Vision model fallback
core/scoring.py

Responsible for:

Combining dimension scores
Calculating the final architecture score
Generating score labels
Environment Configuration

ArchLens supports separate configuration for text and vision models.

Example configuration:

# TEXT / AGENT MODELS
OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free
OPENROUTER_FALLBACK_MODELS=google/gemma-4-26b-a4b-it:free;z-ai/glm-5.2:free

# VISION / DIAGRAM MODELS
OPENROUTER_VISION_MODEL=google/gemma-4-26b-a4b-it:free
OPENROUTER_VISION_FALLBACK_MODELS=google/gemma-4-31b-it:free;nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free

# ENVIRONMENT
ARCHLENS_ENV=cloud

For local execution, the vision pipeline can use LLaVA through Ollama.

Installation

Clone the repository and create a Python virtual environment.

git clone https://github.com/anishsharma251205-bit/Archlens-multi-agent-system-architecture-evaluator-.git

cd Archlens-multi-agent-system-architecture-evaluator-

python -m venv venv

Activate the virtual environment on Windows:

venv\Scripts\activate

Install the required dependencies:

pip install -r requirements.txt
Running ArchLens

Start the Streamlit application:

streamlit run app.py

The application will open in the browser.

Local Model Setup

For local text and vision inference, ArchLens can integrate with Ollama.

The local vision pipeline uses LLaVA for architecture diagram understanding.

The local setup is useful when:

Internet access is unavailable
Local inference is preferred
Cloud model limits are reached
Privacy requirements favor local processing
Cloud Model Setup

For cloud execution, ArchLens uses OpenRouter.

The text and vision pipelines use separate model pools.

This allows the system to use models optimized for the respective task.

Problems Faced

During development, several practical problems were encountered.

Model Rate Limits

Free cloud models can become temporarily rate-limited.

ArchLens addresses this using fallback model pools.

If the primary model fails, another configured model can be attempted.

Vision Model Availability

Different vision models may have different availability and rate limits.

The dedicated vision fallback system allows the architecture diagram evaluation pipeline to continue when the primary model is unavailable.

Structured LLM Output

LLMs do not always return perfectly formatted JSON.

ArchLens therefore includes parsing and validation before accepting the output.

Architecture Evidence

A model may assume that a component is missing simply because it was not mentioned.

ArchLens addresses this by distinguishing between:

Present
Absent
Unspecified

This makes the evaluation more conservative and reduces unsupported conclusions.

Model Separation

Text reasoning and image understanding have different requirements.

Instead of forcing one model pool to handle everything, ArchLens separates:

Text model routing
Vision model routing

This makes the system easier to extend and maintain.

Current Implementation

The current version of ArchLens provides:

Multi-agent architecture evaluation
Five specialized engineering agents
Concurrent agent execution
Text-based architecture evaluation
Diagram-based architecture evaluation
Local LLaVA vision support through Ollama
Cloud OpenRouter vision support
Separate text and vision model pools
Model fallback and retry
RAG and FAISS integration
Guardrail validation
Evidence-aware evaluation
Weighted architecture scoring
Structured final reports
MLOps tracking
SQLite storage
Analytics dashboard
Streamlit interface
PDF export
Future Improvements

Possible future improvements include:

More specialized architecture agents
More advanced architecture diagram understanding
Better dependency and service-boundary detection
More extensive architecture knowledge bases
Improved RAG retrieval
Better evaluation calibration
More detailed MLOps monitoring
Model performance comparison
Architecture history and version comparison
Automated architecture recommendations
Support for additional local vision models
Improved report visualization
Deployment as a production service
Technology Stack
Python
|
├── Streamlit
├── Plotly
├── Ollama
│   └── LLaVA
├── OpenRouter
├── FAISS
├── SentenceTransformers
├── SQLite
├── FPDF
└── Concurrent Futures
Design Philosophy

ArchLens is designed around a simple principle:

Do not ask one model to do everything.

Instead, the system separates the problem into specialized components.

Input
  |
  v
Understand
  |
  v
Route
  |
  v
Specialized Agents
  |
  v
Retrieve Context
  |
  v
Validate
  |
  v
Score
  |
  v
Report
  |
  v
Monitor

This modular architecture makes it easier to replace models, add new evaluation dimensions, improve individual components, and experiment with different routing strategies.

Conclusion

ArchLens demonstrates how a multi-agent architecture can be used to automate software architecture evaluation.

By combining specialized agents, model routing, vision understanding, RAG, guardrails, scoring, and MLOps tracking, the system transforms an architecture description or diagram into a structured engineering assessment.

The project is intended as a starting point for building more advanced automated architecture review systems.

Author

Anish Sharma

how hard it is to give it like the prev like i am agi giving you # ArchLens – Multi-Agent System Architecture Evaluator

ArchLens is a multi-agent AI system that evaluates software architectures across five engineering dimensions:

* Structure
* Security
* Scalability
* Performance
* Cost

It supports both **text-based architecture evaluation** and **diagram/image-based evaluation using LLaVA**.

The goal is to turn an architecture description or diagram into a structured engineering review with scores, issues, recommendations, and an overall architecture score.

# Problem

Architecture reviews are usually manual and depend heavily on the experience of the reviewer.

A system may look reasonable at a high level but still have problems such as:

* Missing components or unclear service boundaries
* Security weaknesses
* Scalability bottlenecks
* Performance risks
* Unnecessary infrastructure cost

ArchLens automates this review by splitting the evaluation into multiple specialized agents instead of asking a single LLM to evaluate everything.

# Architecture


mermaid
flowchart TD
    A[Architecture Input] --> B[Complexity Classification]

    B --> C[Agent Orchestrator]

    C --> D[Structure Agent]
    C --> E[Security Agent]
    C --> F[Scalability Agent]
    C --> G[Performance Agent]
    C --> H[Cost Agent]

    A --> V[LLaVA Vision Model]
    V --> C

    D --> I[RAG / FAISS]
    E --> I
    F --> I
    G --> I
    H --> I

    I --> J[LLM / Model Router]

    J --> K[Guardrail Validation]

    K -->|Invalid Output| L[Retry / Fallback]
    L --> J

    K -->|Valid Output| M[Scoring Engine]

    M --> N[Final Report]

    N --> O[MLOps Tracker]
    O --> P[(SQLite)]

    P --> Q[Analytics Dashboard]


# How It Works

## 1. Architecture Input

The user can provide an architecture description for evaluation.

ArchLens can also work with an architecture diagram/image.

For image-based evaluation, the diagram is processed using **LLaVA running locally through Ollama**.


text
Text Input
    ↓
Architecture Evaluation

Diagram/Image
    ↓
LLaVA
    ↓
Architecture Information
    ↓
Architecture Evaluation


## 2. Complexity Classification

The architecture is first classified based on its complexity.

The classification determines how the system routes model requests.


text
Simple / Medium
       ↓
Ollama
       ↓
Local Mistral

Complex
       ↓
OpenRouter
       ↓
Configured Cloud Model


Fallback mechanisms are available when a selected model fails.

## 3. Five Specialized Agents

ArchLens uses five independent evaluation agents.

### Structure Agent

Checks:

* Component organization
* Service boundaries
* Communication patterns
* Architectural clarity

### Security Agent

Checks:

* Authentication and authorization
* Data protection
* Attack surfaces
* Security controls

### Scalability Agent

Checks:

* Horizontal scaling
* Bottlenecks
* Load handling
* Service scalability

### Performance Agent

Checks:

* Latency
* Throughput
* Database access
* Caching
* Processing bottlenecks

### Cost Agent

Checks:

* Infrastructure usage
* Unnecessary services
* Resource consumption
* Potential cost optimization

## 4. Concurrent Agent Execution

The five agents are executed concurrently using Python's ThreadPoolExecutor.

Instead of waiting for each agent sequentially:


text
Structure
Security
Scalability
Performance
Cost


the system runs the agent evaluations concurrently.

Each agent independently goes through the retrieval, model routing, validation, and scoring pipeline.

This reduces unnecessary waiting when multiple independent evaluations are required.

## 5. RAG and FAISS

ArchLens uses a knowledge base containing architecture best practices.

The knowledge base is indexed using **FAISS**, with embeddings generated using Hugging Face/SentenceTransformers.

During evaluation:


text
Agent Query
    ↓
Embedding
    ↓
FAISS Retrieval
    ↓
Relevant Best Practices
    ↓
LLM
    ↓
Evaluation


The retrieved context helps the agents ground their recommendations in predefined architectural practices instead of relying entirely on model-generated reasoning.

## 6. LLM Routing

ArchLens supports different model providers depending on the evaluation requirements.

### Local Models

Ollama is used for local inference.

Current local models include:

* Mistral
* LLaVA for image/diagram analysis

### OpenRouter

OpenRouter is used for cloud-based model inference, particularly for more complex evaluations.

The router also supports:

* Multiple OpenRouter models
* Retry logic
* Timeouts
* Fallback models
* Ollama fallback

The actual model used during an evaluation is tracked by the MLOps system.

## 7. Guardrails

LLM responses are validated before they are accepted by the evaluation pipeline.

The expected output contains:


text
score
issues
recommendations
summary


The guardrail checks:

* Output type
* Score range
* Required fields
* Issue structure
* Severity values
* Recommendation validity
* Summary validity

If the model produces invalid output, the system retries the request instead of passing malformed data to the scoring system.

## 8. Scoring

Each agent produces a score between 0 and 10.

The scoring engine combines the five dimensions into a final architecture score.


text
Structure
Security
Scalability
Performance
Cost
       ↓
Weighted Scoring
       ↓
Final Score


The final result includes the individual dimension scores and overall architecture assessment.

## 9. MLOps Tracking

ArchLens tracks evaluation information using SQLite.

The system records information such as:

* Evaluation timestamp
* Architecture complexity
* Model used
* Agent latency
* Agent success
* JSON validity
* Dimension scores
* Final score
* Errors
* Hallucination-related flags

This makes it possible to analyze how the evaluation system behaves over time.

## 10. Analytics Dashboard

The Streamlit analytics dashboard provides visibility into system performance.

It includes:

* System health metrics
* Evaluation score trends
* Complexity distribution
* Model usage
* Quality metrics
* Recent evaluations
* Evaluation history

The dashboard uses Plotly for visualization.

# Image / Diagram Evaluation

ArchLens also supports architecture diagrams.

The current image evaluation pipeline uses **LLaVA locally through Ollama**.


text
Architecture Diagram
        ↓
      LLaVA
        ↓
Visual Architecture Understanding
        ↓
Architecture Information
        ↓
Five-Agent Evaluation
        ↓
Scoring + Report


This allows ArchLens to evaluate an architecture even when the information is primarily represented visually rather than as text.

The local LLaVA setup is currently intended for development/local execution.

# Problems Faced During Development

## RAG Model Initialization

The retriever initially encountered errors where the embedding model was not initialized correctly:


text
'NoneType' object has no attribute 'encode'


This was fixed by introducing controlled lazy initialization, validation, and safer shared model/index handling.

## Invalid LLM Responses

LLMs occasionally returned malformed or unexpected JSON.

The solution was to introduce strict schema validation and retry logic before accepting an agent result.

## Model Attribution During Concurrent Execution

Because the five agents run concurrently, tracking which model actually produced each result required explicit per-agent model tracking.

The orchestrator now records the actual model used by each agent.

## OpenRouter Failures

Cloud model requests can fail because of timeouts, API errors, or malformed responses.

The router now includes:

* Request timeouts
* Retries
* Retry delays
* Multiple configured models
* Local Ollama fallback

## SQLite Analytics

The analytics system initially encountered errors caused by positional tuple access when the database query structure changed.

The database layer was updated to use SQLite Row objects and named columns, making the analytics code more reliable.

# Project Structure


text
Archlens-multi-agent-system-architecture-evaluator/
│
├── agents/
│   └── orchestrator.py
│
├── core/
│   ├── guardrail.py
│   ├── knowledge_base.py
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


# Tech Stack

| Component         | Technology                              |
| ----------------- | --------------------------------------- |
| Language          | Python                                  |
| UI                | Streamlit                               |
| Agents            | Custom Python multi-agent orchestration |
| Agent Concurrency | ThreadPoolExecutor                      |
| Local LLM         | Ollama + Mistral                        |
| Vision Model      | LLaVA + Ollama                          |
| Cloud LLM         | OpenRouter                              |
| RAG               | FAISS                                   |
| Embeddings        | Hugging Face / SentenceTransformers     |
| Guardrails        | Custom schema validation + retry        |
| Scoring           | Custom weighted scoring engine          |
| MLOps             | SQLite                                  |
| Analytics         | Plotly + Streamlit                      |

# Local Setup

## 1. Clone the repository


bash
git clone https://github.com/anishsharma251205-bit/Archlens-multi-agent-system-architecture-evaluator-.git

cd Archlens-multi-agent-system-architecture-evaluator-


## 2. Create a virtual environment


bash
python -m venv venv


Activate it:

### Windows


bash
venv\Scripts\activate


### Linux / macOS


bash
source venv/bin/activate


## 3. Install dependencies


bash
pip install -r requirements.txt


## 4. Configure environment variables

Create a .env file based on .env.example.

Configure the required OpenRouter settings if cloud inference is being used.

## 5. Install Ollama

Install Ollama and pull the models used locally.

For example:


bash
ollama pull mistral
ollama pull llava


The exact model configuration can be controlled through the project's environment/model configuration.

## 6. Run ArchLens


bash
streamlit run app.py


# Current Implementation

ArchLens currently includes:

* Multi-agent architecture evaluation
* Five specialized evaluation agents
* Concurrent agent execution
* RAG with FAISS
* Hugging Face embeddings
* Local Mistral inference through Ollama
* LLaVA-based image/diagram evaluation through Ollama
* OpenRouter cloud inference
* Model fallback and retry mechanisms
* Structured LLM output validation
* Guardrails
* Weighted architecture scoring
* SQLite-based MLOps tracking
* Streamlit analytics dashboard
* Plotly visualizations
* Evaluation history tracking

# Author

**Anish Sharma**




import os
import pymupdf


def create_sample_pdfs():
    os.makedirs("sample_docs", exist_ok=True)

    # 1. RAG Architecture Overview (3 pages)
    doc1 = pymupdf.open()
    
    # Page 1
    page1 = doc1.new_page()
    p1_text = """RAG ARCHITECTURE OVERVIEW: FOUNDATIONS AND RETRIEVAL MECHANISMS
Chapter 1: Principles of Retrieval-Augmented Generation

Retrieval-Augmented Generation (RAG) combines dense vector retrieval with autoregressive Large Language Models (LLMs) to overcome parametric knowledge limitations and reduce hallucinations.
Standard RAG architectures decouple knowledge storage from model parameters by indexing external documents in high-dimensional vector spaces.

The ingestion pipeline converts unstructured documents such as PDFs into normalized text chunks. Text extraction must preserve document reading order, page offsets, and structural metadata.
Chunking strategy is a primary determinant of retrieval precision. Fixed-size chunking divides text into windows of predefined character or token length, typically between 300 and 800 tokens.
Overlapping chunks (typically 10% to 20% of chunk size) prevent semantic rupture at chunk boundaries, ensuring that entities split across sentences remain retrievable.

Dense retrieval relies on bi-encoder embedding models that project text into a continuous metric space where cosine similarity approximates semantic relevance.
Vectors are stored in specialized vector databases or PostgreSQL using the pgvector extension with IVFFlat or HNSW indexing structures."""
    page1.insert_text((50, 70), p1_text, fontsize=11, fontname="helv")

    # Page 2
    page2 = doc1.new_page()
    p2_text = """RAG ARCHITECTURE OVERVIEW: CONTEXT & GENERATION
Chapter 2: Context Construction and Generation Control

Once top-K passages are retrieved, the context construction module filters irrelevant chunks using a cosine similarity threshold.
A threshold of 0.40 to 0.70 eliminates noisy or low-confidence matches.
Cross-encoder rerankers can optionally score query-passage pairs jointly to optimize ranking order before context injection.

In grounded RAG, the system prompt strictly instructs the LLM to refuse answering if the retrieved context lacks sufficient evidence.
The standard refusal protocol states that if the evidence is missing, the model must explicitly declare that the answer cannot be established from available sources.
Unchecked extrapolation or parametric hallucinations violate grounding guarantees.

Evidence attribution requires verifiable citations. Every factual assertion must be mapped to its originating document, page number, and verbatim excerpt.
Inline citations allow human operators and automated verifiers to audit the factual trail of the generated response."""
    page2.insert_text((50, 70), p2_text, fontsize=11, fontname="helv")

    # Page 3
    page3 = doc1.new_page()
    p3_text = """RAG ARCHITECTURE OVERVIEW: EVALUATION METRICS
Chapter 3: Quantitative Evaluation Frameworks

Rigorous RAG evaluation requires separating retrieval performance from generation performance.
Retrieval metrics evaluate whether the search engine retrieved the ground truth context:
1. Recall@K measures the proportion of relevant chunks or ground truth context retrieved in the top-K list.
2. Hit Rate@K measures whether at least one relevant document or chunk was present in the top-K results.
3. Mean Reciprocal Rank (MRR) evaluates ranking quality as the multiplicative inverse of the rank of the first relevant result.

Generation metrics evaluate the synthesis quality of the language model:
1. Faithfulness measures whether every claim in the generated answer is directly entailed by the retrieved context.
2. Answer Correctness measures semantic similarity and factual agreement with the ground truth answer.
3. Citation Correctness verifies that cited documents, pages, and excerpts exist in the retrieved passages and support the claim."""
    page3.insert_text((50, 70), p3_text, fontsize=11, fontname="helv")

    doc1.save("sample_docs/rag_architecture_overview.pdf")
    doc1.close()

    # 2. Enterprise Cloud Security Policy (3 pages)
    doc2 = pymupdf.open()
    
    # Page 1
    page1 = doc2.new_page()
    p1_text = """ENTERPRISE CLOUD SECURITY POLICY & GOVERNANCE
Section 1: Access Control and Zero Trust Principles

This policy defines mandatory information security standards across all production cloud workloads.
All systems operate under the Zero Trust Architecture model, where no entity inside or outside the network boundary is trusted implicitly.
Every access request must be authenticated, authorized, and encrypted before access is granted.

Multi-Factor Authentication (MFA) is strictly required for all administrative interfaces, cloud console sessions, and API key management portals.
Hardware-backed FIDO2 security keys are mandatory for privileged infrastructure administrators.
Role-Based Access Control (RBAC) enforces the principle of least privilege, ensuring user accounts and service roles possess only minimum permissions necessary for business functions.
Session lifetimes for administrative consoles are capped at 60 minutes of inactivity before automatic session termination."""
    page1.insert_text((50, 70), p1_text, fontsize=11, fontname="helv")

    # Page 2
    page2 = doc2.new_page()
    p2_text = """ENTERPRISE CLOUD SECURITY POLICY & GOVERNANCE
Section 2: Cryptographic Standards and Data Protection

Data at rest must be encrypted using AES-256 (Advanced Encryption Standard with 256-bit keys) or ChaCha20-Poly1305.
Customer-managed encryption keys (CMEK) must be rotated automatically every 90 days.
Under no circumstances may unencrypted plaintext secrets, passwords, or private keys be committed to version control repositories.

Data in transit across public networks and internal VPC endpoints must enforce TLS 1.3 encryption.
Legacy protocols including TLS 1.0, TLS 1.1, and SSLv3 are deprecated and explicitly disabled on all load balancers.
Database storage volumes require transparent data encryption (TDE), and all database snapshots must inherit the parent encryption key.
Database backups must be retained for a mandatory minimum of 365 days in an immutable write-once-read-many (WORM) storage vault."""
    page2.insert_text((50, 70), p2_text, fontsize=11, fontname="helv")

    # Page 3
    page3 = doc2.new_page()
    p3_text = """ENTERPRISE CLOUD SECURITY POLICY & GOVERNANCE
Section 3: Incident Response and Disaster Recovery SLA

Security incidents are categorized into three severity levels: Severity-1 (Critical), Severity-2 (Major), and Severity-3 (Minor).
Severity-1 incidents, defined as unauthorized root access or active data exfiltration, require an initial response time within 15 minutes.
Containment actions for Severity-1 incidents must commence within 30 minutes of detection.
All external stakeholders and regulatory bodies must be notified within 72 hours of incident confirmation in accordance with global compliance regulations.

Disaster recovery capabilities must satisfy a Recovery Point Objective (RPO) of less than 15 minutes and a Recovery Time Objective (RTO) of less than 2 hours.
Disaster recovery simulation drills must be conducted semiannually across all regional availability zones."""
    page3.insert_text((50, 70), p3_text, fontsize=11, fontname="helv")

    doc2.save("sample_docs/enterprise_cloud_security_policy.pdf")
    doc2.close()

    # 3. Autonomous Agent Workflows (3 pages)
    doc3 = pymupdf.open()
    
    # Page 1
    page1 = doc3.new_page()
    p1_text = """AUTONOMOUS AGENT WORKFLOWS: MULTI-AGENT ARCHITECTURE
Chapter 1: Agent Roles and Task Decomposition

Autonomous agent architectures employ coordinated teams of specialized language model agents to execute complex multi-step workflows.
Rather than relying on a single monolithic prompt, agentic systems decompose high-level user goals into sequential and parallel subtasks.

The Coordinator Agent acts as the orchestrator, analyzing incoming user intents, decomposing requirements into a Directed Acyclic Graph (DAG) of tasks, and delegating execution to domain workers.
Domain worker agents include Code Generators, Retrieval Agents, Database Analysts, and Automated Verifiers.
Inter-agent communication follows structured JSON schema messaging over dedicated message buses or publish-subscribe channels.
Each agent maintains a localized context window containing its specific role prompt, working memory, and tool definitions."""
    page1.insert_text((50, 70), p1_text, fontsize=11, fontname="helv")

    # Page 2
    page2 = doc3.new_page()
    p2_text = """AUTONOMOUS AGENT WORKFLOWS: MEMORY & TOOL CALLING
Chapter 2: Memory Hierarchies and Tool Calling Protocols

Agent memory is organized into three distinct tiers:
1. Working Memory: Transient context window holding active conversation turns, intermediate reasoning traces, and immediate tool execution results.
2. Episodic Memory: Vector-indexed record of past task executions, user interactions, and successful problem-solving trajectories.
3. Semantic Memory: Persistent knowledge graph and long-term factual storage regarding system rules, environment capabilities, and learned user preferences.

Tool calling protocols allow agents to interact deterministically with external APIs, databases, shell environments, and web scrapers.
To prevent hallucinated parameters, tool calling interfaces enforce Pydantic or JSON-Schema validation prior to execution.
Sandboxed execution environments isolate tool invocations from production host operating systems."""
    page2.insert_text((50, 70), p2_text, fontsize=11, fontname="helv")

    # Page 3
    page3 = doc3.new_page()
    p3_text = """AUTONOMOUS AGENT WORKFLOWS: VERIFICATION & CONSENSUS
Chapter 3: Verification Loops and Guardrails

To prevent error compounding in long-horizon workflows, autonomous architectures implement automated verification loops.
After worker agents complete execution, an independent Verifier Agent audits the output against predefined acceptance criteria.
If errors or constraint violations are identified, the Verifier generates structured feedback and returns the task to the worker agent for self-correction.

When critical decisions involve financial transactions or data deletion, agents must employ a multi-agent consensus protocol or request human-in-the-loop approval.
Maximum loop depth limits (typically 3 to 5 retry cycles) prevent infinite reflection loops when agents encounter unsolvable constraints.
Execution telemetries, including token usage, latency, and tool invocations, are logged in OpenTelemetry format for auditability."""
    page3.insert_text((50, 70), p3_text, fontsize=11, fontname="helv")

    doc3.save("sample_docs/autonomous_agent_workflows.pdf")
    doc3.close()

    print("Sample PDF documents created successfully!")


if __name__ == "__main__":
    create_sample_pdfs()


## Purpose

为需要最新知识的学习主题提供基于实时证据的题目生成能力，确保题目、答案和解析能够追溯到来源，并在证据不足或过期时避免生成未经支持的内容。

## ADDED Requirements

### Requirement: The system SHALL determine whether a topic requires fresh evidence

The system SHALL classify a requested topic using its wording, requested time range, domain volatility, and configured freshness policy. Topics involving recent events, current products or standards, versions, prices, regulations, or an explicit date/range MUST use web evidence; stable topics MAY use the existing offline path.

#### Scenario: Current topic triggers retrieval
- **WHEN** a user requests questions about a current software version or an event after the model knowledge cutoff
- **THEN** the system retrieves web evidence before creating the outline or first question

#### Scenario: Stable topic uses configured policy
- **WHEN** a user requests a stable foundational topic without a recency signal
- **THEN** the system follows the configured policy and records whether web retrieval was skipped

### Requirement: The system SHALL build a bounded, source-traceable evidence bundle

For a topic requiring fresh evidence, the system MUST retrieve relevant results, retain source URL, title, publisher, publication or update date when available, retrieval time, and the supporting content excerpt, and pass only a bounded evidence bundle to question generation.

#### Scenario: Search returns usable sources
- **WHEN** the search provider returns relevant results with accessible content
- **THEN** the system stores a normalized evidence bundle and associates each evidence item with the generated session

#### Scenario: Search fails or evidence is insufficient
- **WHEN** the provider times out, returns no usable result, or the results do not meet relevance or freshness thresholds
- **THEN** the system does not silently generate a current-fact question and returns a retryable, user-visible generation error

### Requirement: Generated questions SHALL be grounded and cite their evidence

Every question generated from fresh evidence MUST include at least one source citation, a freshness timestamp or policy result, and an explanation that is supported by the cited evidence. The system MUST keep answer-bearing evidence private from the public question payload until the user submits an answer.

#### Scenario: Question passes grounding checks
- **WHEN** the model produces a structured question whose answer and explanation are supported by the evidence bundle
- **THEN** the system persists the question with citation metadata and returns the public stem and options without exposing the private answer

#### Scenario: Question lacks support or citation
- **WHEN** the model output contains an unsupported claim, contradictory answer, missing citation, or citation not present in the evidence bundle
- **THEN** the system rejects the output, retries within the configured limit, and never persists it as playable content

### Requirement: The system SHALL validate source freshness and handle provider/model failures explicitly

The system MUST apply freshness, source relevance, content safety, schema, option, and answer consistency checks before persistence. Search, model, parsing, and validation failures MUST map to stable retryable error categories and MUST preserve session consistency.

#### Scenario: Retry succeeds after transient failure
- **WHEN** a search or model call fails transiently and the retry budget remains
- **THEN** the system retries with bounded backoff and persists only the first valid result

#### Scenario: Retry budget is exhausted
- **WHEN** all configured attempts fail or evidence remains stale
- **THEN** the session enters a recoverable failed-generation state, no score or question index is advanced, and the client can retry generation

### Requirement: The system SHALL expose source metadata and generation status to clients

Question, feedback, report, and generation-error responses MUST expose the applicable source metadata, freshness status, and AI-generated disclaimer without exposing API keys, private answer fields, full prompts, or unsafe raw provider payloads.

#### Scenario: User inspects a cited question
- **WHEN** a source-grounded question is displayed
- **THEN** the client shows a compact source title/domain and retrieval or publication date, with a way to inspect the source URL

#### Scenario: User sees a fallback or error
- **WHEN** evidence retrieval or validation cannot complete
- **THEN** the client shows a clear retry action and explains that a current question was not generated

### Requirement: The system SHALL measure source-grounded question quality

The system MUST record provider latency and status, evidence count and freshness outcome, validation/retry outcome, citation coverage, and generation failure category without logging API keys, full prompts, or unnecessary sensitive user content.

#### Scenario: Successful generation is observed
- **WHEN** a cited question is persisted
- **THEN** metrics contain the provider outcome, latency, evidence and citation coverage, and validation result

#### Scenario: Failure is observed safely
- **WHEN** retrieval or generation fails
- **THEN** logs contain a stable error category and correlation/session identifier but omit secrets and full sensitive payloads

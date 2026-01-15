# End-to-End Speech Translation Flow Workflows
## Universal Speech Translation Platform

> **Complete Pipeline Documentation**: This document provides comprehensive sequence diagrams and workflow documentation for the complete speech translation pipeline from audio input to synthesized output, demonstrating the event-driven microservices architecture with language-agnostic processing and correlation tracking.

## Overview

The Universal Speech Translation Platform processes speech translation requests through a sophisticated event-driven pipeline that maintains complete service independence while ensuring seamless coordination. This document details the complete end-to-end flows including service interactions, event routing, correlation tracking, and error handling across all microservices.

### Contract note (events vs topics vs schemas)

The event names used in the sequence diagrams (e.g., `ASRRequestEvent`, `TranslationRequestEvent`, `TTSRequestEvent`) are **logical event types**, not guaranteed to be the exact Kafka topic names or Avro schemas currently implemented by each service in this workspace.

For contract alignment (topic naming, Avro envelope structure, and schema ownership), refer to [`event-driven-flows.md`](event-driven-flows.md) and the **Reality Check: Current Repo vs This Doc** section.

### Pipeline Architecture Principles

- **Event-Driven Coordination**: All services communicate exclusively through language-agnostic events
- **Correlation Tracking**: Every request maintains a unique correlation ID throughout the entire pipeline
- **Dynamic Language Support**: Runtime language detection and model selection across all services
- **Quality-Based Routing**: Intelligent routing based on language pair quality requirements
- **Independent Service Processing**: Each service operates autonomously with complete fault isolation

## Complete End-to-End Translation Flow

### Primary Translation Pipeline Sequence

```mermaid
sequenceDiagram
    participant Client as Client Application
    participant Gateway as API Gateway
    participant Orchestrator as Pipeline Orchestrator
    participant VAD as Voice Activity Detection
    participant ASR as Speech Recognition Service
    participant Translation as Translation Service
    participant TTS as Text-to-Speech Service
    participant EventBus as Event Bus (Kafka)
    
    Note over Client, EventBus: Complete Speech Translation Pipeline Flow
    
    %% Initial Request Processing
    Client->>Gateway: POST /translate (audio, source_lang?, target_lang)
    Gateway->>Gateway: Generate correlation_id, validate request
    Gateway->>EventBus: AudioInputEvent(correlation_id, audio_data, lang_hint)
    Gateway->>Client: 202 Accepted {correlation_id, session_id}
    
    %% Pipeline Orchestration
    EventBus->>Orchestrator: AudioInputEvent
    Orchestrator->>Orchestrator: Initialize pipeline state, language detection
    Orchestrator->>EventBus: VADRequestEvent(correlation_id, audio_data)
    
    %% Voice Activity Detection
    EventBus->>VAD: VADRequestEvent
    VAD->>VAD: Detect speech segments, filter noise
    VAD->>EventBus: VADCompletedEvent(correlation_id, speech_segments, confidence)
    
    %% Orchestrator Route Decision
    EventBus->>Orchestrator: VADCompletedEvent
    Orchestrator->>Orchestrator: Evaluate speech quality, plan ASR routing
    Orchestrator->>EventBus: ASRRequestEvent(correlation_id, speech_data, lang_hint)
    
    %% Speech Recognition Processing
    EventBus->>ASR: ASRRequestEvent
    ASR->>ASR: Language detection, model selection
    ASR->>ASR: Speech-to-text conversion with quality assessment
    ASR->>EventBus: ASRCompletedEvent(correlation_id, text, detected_lang, confidence)
    
    %% Translation Processing
    EventBus->>Orchestrator: ASRCompletedEvent
    Orchestrator->>Orchestrator: Validate language pair, select translation model
    Orchestrator->>EventBus: TranslationRequestEvent(correlation_id, text, source_lang, target_lang)
    
    EventBus->>Translation: TranslationRequestEvent
    Translation->>Translation: Model selection, context analysis
    Translation->>Translation: Text translation with quality assessment
    Translation->>EventBus: TranslationCompletedEvent(correlation_id, translated_text, quality_score)
    
    %% Text-to-Speech Synthesis
    EventBus->>Orchestrator: TranslationCompletedEvent
    Orchestrator->>Orchestrator: Select TTS model, voice parameters
    Orchestrator->>EventBus: TTSRequestEvent(correlation_id, text, target_lang, voice_config)
    
    EventBus->>TTS: TTSRequestEvent
    TTS->>TTS: Voice model selection, synthesis parameters
    TTS->>TTS: Text-to-speech conversion with quality optimization
    TTS->>EventBus: TTSCompletedEvent(correlation_id, audio_data, synthesis_metadata)
    
    %% Final Response Assembly
    EventBus->>Orchestrator: TTSCompletedEvent
    Orchestrator->>Orchestrator: Assemble complete response, quality metrics
    Orchestrator->>EventBus: PipelineCompletedEvent(correlation_id, final_audio, metadata)
    
    EventBus->>Gateway: PipelineCompletedEvent
    Gateway->>Gateway: Format response, update session state
    Gateway->>Client: WebSocket: TranslationComplete(correlation_id, audio, metadata)
    
    Note over Client, EventBus: End-to-End Latency Target: < 3 seconds
```

### Event Correlation and State Management Flow

```mermaid
graph TD
    subgraph "Correlation Tracking Architecture"
        A[Initial Request] --> B[Generate Correlation ID]
        B --> C[Pipeline State Initialization]
        C --> D[Event Correlation Metadata]
        
        D --> E[VAD Processing State]
        D --> F[ASR Processing State]
        D --> G[Translation Processing State]
        D --> H[TTS Processing State]
        
        E --> I[Pipeline State Aggregation]
        F --> I
        G --> I
        H --> I
        
        I --> J[Final Response Assembly]
        J --> K[State Cleanup]
    end
    
    subgraph "Event Metadata Structure"
        L[correlation_id: UUID]
        M[session_id: UUID]
        N[timestamp: ISO8601]
        O[source_language: string]
        P[target_language: string]
        Q[quality_requirements: object]
        R[processing_metadata: object]
    end
    
    subgraph "State Persistence Strategy"
        S[Redis Pipeline State]
        T[In-Memory Processing Cache]
        U[Event Log Correlation]
        V[Metrics Collection State]
    end
    
    D --> L
    D --> M
    D --> N
    D --> O
    D --> P
    D --> Q
    D --> R
    
    I --> S
    I --> T
    I --> U
    I --> V
```

## Service-Specific Processing Workflows

### Voice Activity Detection Service Flow

```mermaid
flowchart TD
    Start([VAD Request Event]) --> ValidateAudio{Audio Data Valid?}
    ValidateAudio -->|No| Error[Publish VADErrorEvent]
    ValidateAudio -->|Yes| LoadModel[Load Universal VAD Model]
    
    LoadModel --> ProcessAudio[Analyze Audio Segments]
    ProcessAudio --> DetectSpeech[Detect Speech Activity]
    DetectSpeech --> FilterNoise[Apply Noise Filtering]
    
    FilterNoise --> QualityCheck{Speech Quality OK?}
    QualityCheck -->|Low Quality| ApplyEnhancement[Audio Enhancement]
    ApplyEnhancement --> QualityCheck
    
    QualityCheck -->|Good Quality| SegmentAudio[Segment Speech Regions]
    SegmentAudio --> CalculateConfidence[Calculate Confidence Scores]
    
    CalculateConfidence --> CreateResponse[Create VADCompletedEvent]
    CreateResponse --> PublishEvent[Publish to Event Bus]
    PublishEvent --> End([VAD Processing Complete])
    
    Error --> End
    
    style Start fill:#e1f5fe
    style End fill:#e8f5e8
    style Error fill:#ffebee
    style QualityCheck fill:#fff3e0
```

### Speech Recognition Service Flow

```mermaid
flowchart TD
    Start([ASR Request Event]) --> ParseEvent[Extract Audio & Language Hint]
    ParseEvent --> LanguageDetection{Language Provided?}
    
    LanguageDetection -->|No| AutoDetect[Automatic Language Detection]
    AutoDetect --> ValidateLanguage[Validate Detected Language]
    LanguageDetection -->|Yes| ValidateLanguage
    
    ValidateLanguage --> SelectModel[Select Optimal ASR Model]
    SelectModel --> LoadModel[Load/Initialize Model]
    LoadModel --> ConfigureModel[Configure for Language]
    
    ConfigureModel --> ProcessAudio[Speech-to-Text Processing]
    ProcessAudio --> PostProcess[Text Post-Processing]
    PostProcess --> QualityAssessment[Quality Assessment]
    
    QualityAssessment --> QualityCheck{Quality Threshold Met?}
    QualityCheck -->|No| TryFallback{Fallback Available?}
    TryFallback -->|Yes| FallbackModel[Load Fallback Model]
    FallbackModel --> ProcessAudio
    TryFallback -->|No| LowQualityResponse[Create Low-Confidence Response]
    
    QualityCheck -->|Yes| CreateResponse[Create ASRCompletedEvent]
    LowQualityResponse --> PublishEvent[Publish to Event Bus]
    CreateResponse --> PublishEvent
    PublishEvent --> End([ASR Processing Complete])
    
    style Start fill:#e1f5fe
    style End fill:#e8f5e8
    style TryFallback fill:#fff3e0
    style QualityCheck fill:#fff3e0
```

### Translation Service Flow

```mermaid
flowchart TD
    Start([Translation Request Event]) --> ParseRequest[Extract Text & Language Pair]
    ParseRequest --> ValidatePair{Language Pair Supported?}
    
    ValidatePair -->|No| ErrorResponse[Create UnsupportedPairError]
    ValidatePair -->|Yes| SelectEngine[Select Translation Engine]
    
    SelectEngine --> ModelSelection[Select Optimal Model]
    ModelSelection --> LoadModel[Load/Initialize Model]
    LoadModel --> ContextAnalysis[Analyze Text Context]
    
    ContextAnalysis --> CulturalAdaptation[Apply Cultural Context]
    CulturalAdaptation --> Translation[Perform Translation]
    Translation --> PostProcessing[Post-Process Translation]
    
    PostProcessing --> QualityEvaluation[Evaluate Translation Quality]
    QualityEvaluation --> QualityGate{Quality Acceptable?}
    
    QualityGate -->|No| AlternativeEngine{Alternative Engine?}
    AlternativeEngine -->|Yes| SelectEngine
    AlternativeEngine -->|No| LowQualityFlag[Flag Low Quality]
    
    QualityGate -->|Yes| CreateResponse[Create TranslationCompletedEvent]
    LowQualityFlag --> CreateResponse
    CreateResponse --> PublishEvent[Publish to Event Bus]
    
    ErrorResponse --> PublishEvent
    PublishEvent --> End([Translation Processing Complete])
    
    style Start fill:#e1f5fe
    style End fill:#e8f5e8
    style ErrorResponse fill:#ffebee
    style QualityGate fill:#fff3e0
    style AlternativeEngine fill:#fff3e0
```

### Text-to-Speech Service Flow

```mermaid
flowchart TD
    Start([TTS Request Event]) --> ParseRequest[Extract Text & Language]
    ParseRequest --> ValidateLanguage{Language Supported?}
    
    ValidateLanguage -->|No| ErrorResponse[Create UnsupportedLanguageError]
    ValidateLanguage -->|Yes| VoiceSelection[Select Voice Model]
    
    VoiceSelection --> ModelConfiguration[Configure Synthesis Parameters]
    ModelConfiguration --> LoadModel[Load/Initialize TTS Model]
    LoadModel --> TextPreprocessing[Preprocess Text]
    
    TextPreprocessing --> PhonemicAnalysis[Phonemic Analysis]
    PhonemicAnalysis --> ProsodyGeneration[Generate Prosody]
    ProsodyGeneration --> AudioSynthesis[Synthesize Audio]
    
    AudioSynthesis --> QualityCheck[Audio Quality Assessment]
    QualityCheck --> QualityGate{Quality Acceptable?}
    
    QualityGate -->|No| TryAlternative{Alternative Voice?}
    TryAlternative -->|Yes| VoiceSelection
    TryAlternative -->|No| AcceptLowerQuality[Accept with Quality Warning]
    
    QualityGate -->|Yes| AudioPostProcess[Post-Process Audio]
    AcceptLowerQuality --> AudioPostProcess
    AudioPostProcess --> CreateResponse[Create TTSCompletedEvent]
    
    ErrorResponse --> PublishEvent[Publish to Event Bus]
    CreateResponse --> PublishEvent
    PublishEvent --> End([TTS Processing Complete])
    
    style Start fill:#e1f5fe
    style End fill:#e8f5e8
    style ErrorResponse fill:#ffebee
    style QualityGate fill:#fff3e0
    style TryAlternative fill:#fff3e0
```

## Advanced Pipeline Scenarios

### Dynamic Language Detection Flow

```mermaid
sequenceDiagram
    participant Client as Client
    participant Gateway as API Gateway  
    participant Orchestrator as Pipeline Orchestrator
    participant ASR as Speech Recognition
    participant LangDetector as Language Detection Service
    participant EventBus as Event Bus
    
    Note over Client, EventBus: Dynamic Language Detection Scenario
    
    Client->>Gateway: Audio without language hint
    Gateway->>EventBus: AudioInputEvent(no language hint)
    
    EventBus->>Orchestrator: AudioInputEvent
    Orchestrator->>EventBus: LanguageDetectionRequest(audio_sample)
    
    EventBus->>LangDetector: LanguageDetectionRequest  
    LangDetector->>LangDetector: Analyze audio characteristics
    LangDetector->>LangDetector: Apply language detection models
    LangDetector->>EventBus: LanguageDetectedEvent(language, confidence)
    
    EventBus->>Orchestrator: LanguageDetectedEvent
    Orchestrator->>Orchestrator: Validate language support, select models
    Orchestrator->>EventBus: ASRRequestEvent(with detected language)
    
    Note over Orchestrator: Continue with normal pipeline flow
```

### Multi-Model Quality Comparison Flow

```mermaid
sequenceDiagram
    participant Orchestrator as Pipeline Orchestrator
    participant ASR1 as ASR Service (Model A)
    participant ASR2 as ASR Service (Model B)
    participant QualityService as Quality Assessment
    participant EventBus as Event Bus
    
    Note over Orchestrator, EventBus: Quality-Based Model Selection
    
    Orchestrator->>EventBus: ASRRequestEvent(parallel processing)
    
    EventBus->>ASR1: ASRRequestEvent (Model A)
    EventBus->>ASR2: ASRRequestEvent (Model B)
    
    par Process with Model A
        ASR1->>ASR1: Process with Model A
        ASR1->>EventBus: ASRResultEvent(model_a_result)
    and Process with Model B  
        ASR2->>ASR2: Process with Model B
        ASR2->>EventBus: ASRResultEvent(model_b_result)
    end
    
    EventBus->>QualityService: CompareResultsRequest(both results)
    QualityService->>QualityService: Evaluate quality metrics
    QualityService->>EventBus: BestResultSelectedEvent(winning_result)
    
    EventBus->>Orchestrator: BestResultSelectedEvent
    Note over Orchestrator: Continue with highest quality result
```

### Error Handling and Recovery Flow

```mermaid
flowchart TD
    ProcessingError[Service Processing Error] --> ErrorClassification{Error Type?}
    
    ErrorClassification -->|Transient| RetryLogic[Apply Retry Logic]
    ErrorClassification -->|Configuration| ConfigError[Configuration Error Handler]
    ErrorClassification -->|Resource| ResourceError[Resource Error Handler]
    ErrorClassification -->|Quality| QualityError[Quality Error Handler]
    ErrorClassification -->|Fatal| FatalError[Fatal Error Handler]
    
    RetryLogic --> RetryAttempt[Retry with Backoff]
    RetryAttempt --> RetrySuccess{Retry Successful?}
    RetrySuccess -->|Yes| ContinuePipeline[Continue Pipeline]
    RetrySuccess -->|No| CheckRetryLimit{Max Retries?}
    CheckRetryLimit -->|No| RetryAttempt
    CheckRetryLimit -->|Yes| FallbackStrategy[Activate Fallback]
    
    ConfigError --> LoadBackupConfig[Load Backup Configuration]
    LoadBackupConfig --> ConfigFixed{Config Valid?}
    ConfigFixed -->|Yes| ContinuePipeline
    ConfigFixed -->|No| FallbackStrategy
    
    ResourceError --> CheckAlternativeResource[Check Alternative Resources]
    CheckAlternativeResource --> ResourceAvailable{Resource Available?}
    ResourceAvailable -->|Yes| SwitchResource[Switch to Alternative]
    SwitchResource --> ContinuePipeline
    ResourceAvailable -->|No| FallbackStrategy
    
    QualityError --> LowerQualityAcceptable{Accept Lower Quality?}
    LowerQualityAcceptable -->|Yes| ProceedWithWarning[Proceed with Quality Warning]
    ProceedWithWarning --> ContinuePipeline
    LowerQualityAcceptable -->|No| FallbackStrategy
    
    FatalError --> FallbackStrategy
    FallbackStrategy --> FallbackAvailable{Fallback Available?}
    FallbackAvailable -->|Yes| ActivateFallback[Activate Fallback Pipeline]
    ActivateFallback --> ContinuePipeline
    FallbackAvailable -->|No| GracefulFailure[Graceful Failure Response]
    
    ContinuePipeline --> Success([Pipeline Continues])
    GracefulFailure --> ErrorResponse([Error Response to Client])
    
    style ProcessingError fill:#ffebee
    style Success fill:#e8f5e8
    style ErrorResponse fill:#ffcdd2
    style FallbackStrategy fill:#fff3e0
```

## Performance Metrics and Monitoring

### Key Performance Indicators

```mermaid
graph TB
    subgraph "Latency Metrics"
        A[Total Pipeline Latency]
        B[Per-Service Processing Time]
        C[Event Routing Latency]
        D[Model Loading Time]
    end
    
    subgraph "Quality Metrics"
        E[Translation Quality Score]
        F[Speech Recognition Accuracy]
        G[Audio Synthesis Quality]
        H[Overall Pipeline Quality]
    end
    
    subgraph "Throughput Metrics"
        I[Concurrent Sessions]
        J[Events per Second]
        K[Requests per Minute]
        L[Model Utilization Rate]
    end
    
    subgraph "Reliability Metrics"
        M[Success Rate]
        N[Error Rate by Type]
        O[Retry Success Rate]
        P[Fallback Activation Rate]
    end
    
    A --> Target1[< 3 seconds end-to-end]
    B --> Target2[Service SLA compliance]
    C --> Target3[< 50ms event routing]
    D --> Target4[< 30s model switching]
    
    E --> Target5[> 85% quality score]
    F --> Target6[> 95% word accuracy]
    G --> Target7[> 4.0 MOS score]
    H --> Target8[> 80% overall quality]
```

### Real-Time Monitoring Dashboard Metrics

1. **Pipeline Health**
   - End-to-end success rate
   - Service availability status
   - Event processing backlog
   - Active pipeline count

2. **Language-Specific Performance**
   - Performance by language pair
   - Model performance comparison
   - Quality metrics by language family
   - Cultural adaptation effectiveness

3. **Resource Utilization**
   - CPU usage per service
   - Memory consumption patterns
   - GPU utilization for ML models
   - Storage usage for model cache

4. **Quality Tracking**
   - Real-time quality scores
   - Quality degradation alerts
   - Model performance trends
   - User satisfaction metrics

## Correlation ID Tracking Implementation

### Event Correlation Structure

```yaml
correlation_metadata:
  correlation_id: "550e8400-e29b-41d4-a716-446655440000"
  session_id: "session_2025_09_15_12345"
  parent_event_id: "vad_completed_001"
  root_event_id: "audio_input_root"
  timestamp: "2025-09-15T12:17:00Z"
  
pipeline_state:
  current_stage: "translation"
  completed_stages: ["vad", "asr"]
  remaining_stages: ["tts", "response"]
  
language_metadata:
  source_language: "da"
  target_language: "en"
  detected_language: "da"
  detection_confidence: 0.95
  
quality_metrics:
  overall_quality_requirement: "high"
  stage_quality_scores:
    vad: 0.92
    asr: 0.88
    translation: null  # In progress
    tts: null  # Pending
```

### Correlation Tracking Across Services

Each service maintains correlation context and enriches events with processing metadata:

```mermaid
graph LR
    subgraph "Event Enrichment Pattern"
        Input[Input Event] --> Process[Service Processing]
        Process --> Enrich[Enrich with Metadata]
        Enrich --> Output[Output Event]
    end
    
    subgraph "Correlation Context"
        CC[Correlation Context]
        CC --> Timing[Processing Timestamps]
        CC --> Quality[Quality Metrics]
        CC --> Performance[Performance Data]
        CC --> Errors[Error Information]
    end
    
    Input --> CC
    Process --> CC
    CC --> Enrich
```

This comprehensive end-to-end flow documentation provides complete visibility into the Universal Speech Translation Platform's event-driven architecture, enabling systematic performance analysis, troubleshooting, and academic research validation.

---

**Flow Documentation Standards**: All sequence diagrams use consistent notation and correlation tracking  
**Academic Context**: Detailed flows support thesis research on distributed AI systems  
**Maintenance**: Flow documentation updated automatically with system changes  
**Last Updated**: September 2025
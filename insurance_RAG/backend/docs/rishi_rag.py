"""Enhanced RAG system with intelligent agent loop using LangGraph.

This module implements an advanced RAG system that automatically determines
optimal retrieval strategies, performs intelligent hop selection, and provides
comprehensive context gathering with step-by-step transparency.

Key Features:
- Automatic question complexity analysis
- Intelligent hop selection based on question type
- Parallel multi-strategy retrieval
- Advanced context quality assessment
- Multi-factor decision making
- Enhanced synthesis with confidence scoring
- Comprehensive answer verification
"""

from __future__ import annotations

import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Any, Tuple, TypedDict
import os
from uuid import uuid4
import time

from dotenv import load_dotenv

from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_postgres import PGVector
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from rishi_prompts import (
    QUESTION_ANALYSIS_PROMPT,
    MULTI_QUERY_PLANNING_PROMPT,
    CONTEXT_ASSESSMENT_PROMPT,
    DECISION_MAKING_PROMPT,
    ENHANCED_SYNTHESIS_PROMPT,
    ADVANCED_VERIFICATION_PROMPT,
    USER_PROMPT
)

from prompts import (
    SYSTEM_PROMPT1
)

# -----------------------------------------------------------------------------
# Enhanced State Schema
# -----------------------------------------------------------------------------

class EnhancedAgentState(TypedDict, total=False):
    # Input
    question: str
    
    # Question Analysis
    question_complexity: float  # 1-10 scale
    question_type: str  # factual, analytical, comparative, etc.
    estimated_hops: int
    required_evidence_types: List[str]
    key_aspects: List[str]
    
    # Planning
    sub_questions: List[Dict[str, Any]]  # Multiple sub-questions with priorities
    current_query_batch: List[str]
    
    # Retrieval
    retrieval_strategies: List[str]
    parallel_results: Dict[str, List[Document]]
    fused_results: List[Document]
    
    # Assessment
    context_quality_score: float
    coverage_score: float
    evidence_strength: float
    detected_contradictions: List[str]
    information_gaps: List[str]
    sufficiency_assessment: str
    key_findings: List[str]
    
    # Decision
    decision_factors: Dict[str, float]
    continue_probability: float
    stop_reasons: List[str]
    recent_quality_improvements: List[float]
    
    # Synthesis
    answer_confidence: float
    
    # Control
    iteration: int
    max_dynamic_iters: int
    stop: bool
    
    # Legacy (for compatibility)
    evidence_docs: List[Document]
    last_batch: List[Document]
    evidence_hints: List[str]
    gaps: List[str]
    final_answer: str
    grounded_ok: bool
    sub_question: str  # For compatibility


# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def _format_docs(docs: List[Document]) -> str:
    """Format a list of documents into a numbered string with source and page."""
    lines = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source") or d.metadata.get("file_path") or "unknown"
        page = d.metadata.get("page", "?")
        header = f"[S{i}] ({src} p.{page})"
        body = d.page_content or ""
        lines.append(f"{header}\n{body}\n")
    return "\n".join(lines)


def _dedupe_docs(docs: List[Document]) -> List[Document]:
    """Remove duplicate documents based on (source, page) metadata."""
    seen = set()
    out = []
    for d in docs:
        key = (d.metadata.get("source"), d.metadata.get("page"))
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def _safe_json_parse(text: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
    """Safely parse JSON text, returning default if parsing fails."""
    if default is None:
        default = {}
    try:
        # Try to extract JSON from text if it's wrapped in other content
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            json_text = text[start:end]
            return json.loads(json_text)
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return default


# -----------------------------------------------------------------------------
# Enhanced RAG Pipeline
# -----------------------------------------------------------------------------

class EnhancedRAGPipeline:
    """Enhanced RAG pipeline with intelligent agent loop."""

    def __init__(self, max_iters: int = 8, min_iters: int = 2):
        # Load environment variables
        load_dotenv()

        # Environment
        self.db_url = os.environ["PGVECTOR_DATABASE_URL"]
        self.endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
        self.api_key = os.environ["AZURE_OPENAI_API_KEY"]
        self.api_version = os.environ["AZURE_OPENAI_API_VERSION"]
        self.chat_deployment = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]
        self.emb_deployment = os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"]
        self.collections = os.environ["COLLECTION_NAME"]

        # Embeddings and vector store
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            deployment=self.emb_deployment,
        )

        self.vectorstore = PGVector(
            embeddings=self.embeddings,
            connection=self.db_url,
            collection_name=self.collections,
            use_jsonb=True,
        )

        # Multiple retrievers for different strategies
        self.semantic_retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 6, "fetch_k": 24, "lambda_mult": 0.5},
        )
        
        self.similarity_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 8},
        )

        # LLMs for different purposes
        self.analysis_llm = AzureChatOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            deployment_name=self.chat_deployment,
            temperature=0.0,
            max_tokens=4096,
        )
        
        self.planning_llm = AzureChatOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            deployment_name=self.chat_deployment,
            temperature=0.2,
            max_tokens=4096,
        )
        
        self.synthesis_llm = AzureChatOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            deployment_name=self.chat_deployment,
            temperature=0.0,
            max_tokens=4096,
        )

        # Default parameters
        self.default_max_iters = max_iters
        self.min_iters = max(0, min_iters)

        # Build the enhanced graph
        graph = StateGraph(EnhancedAgentState)
        
        # Add nodes
        graph.add_node("analyze_question", self._analyze_question)
        graph.add_node("enhanced_plan", self._enhanced_plan)
        graph.add_node("parallel_retrieve", self._parallel_retrieve)
        graph.add_node("advanced_assess", self._advanced_assess)
        graph.add_node("intelligent_decide", self._intelligent_decide)
        graph.add_node("enhanced_synthesis", self._enhanced_synthesis)
        graph.add_node("advanced_verify", self._advanced_verify)

        # Set up graph flow
        graph.set_entry_point("analyze_question")
        graph.add_edge("analyze_question", "enhanced_plan")
        graph.add_edge("enhanced_plan", "parallel_retrieve")
        graph.add_edge("parallel_retrieve", "advanced_assess")
        graph.add_edge("advanced_assess", "intelligent_decide")

        # Conditional routing from decide node
        graph.add_conditional_edges(
            "intelligent_decide",
            lambda state: "enhanced_synthesis" if state.get("stop", False) else "enhanced_plan",
        )

        graph.add_edge("enhanced_synthesis", "advanced_verify")
        graph.add_edge("advanced_verify", END)

        # State persistence
        self.checkpointer = MemorySaver()
        self.app = graph.compile(checkpointer=self.checkpointer)

        # Thread pool for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=4)

    # --------------------------- Node Implementations ----------------------------

    def _analyze_question(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Analyze question complexity and characteristics."""
        question = state["question"]
        
        prompt = ChatPromptTemplate.from_template(QUESTION_ANALYSIS_PROMPT)
        chain = prompt | self.analysis_llm | StrOutputParser()
        
        response = chain.invoke({"question": question})
        analysis = _safe_json_parse(response, {
            "complexity_score": 5.0,
            "question_type": "analytical",
            "estimated_hops": 4,
            "required_evidence_types": ["documents"],
            "key_aspects": ["general"],
            "reasoning": "Default analysis"
        })
        
        # Set dynamic max iterations based on complexity
        complexity = analysis.get("complexity_score", 5.0)
        estimated_hops = analysis.get("estimated_hops", 4)
        max_dynamic = min(self.default_max_iters, max(2, int(complexity * 0.8 + estimated_hops * 0.5)))
        
        return {
            "question_complexity": complexity,
            "question_type": analysis.get("question_type", "analytical"),
            "estimated_hops": estimated_hops,
            "required_evidence_types": analysis.get("required_evidence_types", ["documents"]),
            "key_aspects": analysis.get("key_aspects", ["general"]),
            "max_dynamic_iters": max_dynamic,
            "iteration": 0,
            "evidence_docs": [],
            "evidence_hints": [],
            "gaps": [],
            "recent_quality_improvements": [],
            "context_quality_score": 0.0,
            "coverage_score": 0.0,
            "evidence_strength": 0.0,
            "information_gaps": [],
            "detected_contradictions": [],
            "key_findings": []
        }

    def _enhanced_plan(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Generate multiple focused sub-questions for comprehensive retrieval."""
        question = state["question"]
        analysis = {
            "complexity_score": state.get("question_complexity", 5.0),
            "question_type": state.get("question_type", "analytical"),
            "estimated_hops": state.get("estimated_hops", 4),
            "required_evidence_types": state.get("required_evidence_types", [])
        }
        
        context_hints = "\n".join(f"- {h}" for h in state.get("evidence_hints", [])[-10:]) or "None"
        gaps = "\n".join(f"- {g}" for g in state.get("information_gaps", [])[-5:]) or "None"
        
        prompt = ChatPromptTemplate.from_template(MULTI_QUERY_PLANNING_PROMPT)
        chain = prompt | self.planning_llm | StrOutputParser()
        
        response = chain.invoke({
            "question": question,
            "analysis": json.dumps(analysis),
            "context_hints": context_hints,
            "gaps": gaps
        })
        
        planning_result = _safe_json_parse(response, {
            "sub_questions": [{"query": question, "priority": 1.0, "aspect": "general", "strategy": "semantic"}],
            "reasoning": "Default planning"
        })
        
        sub_questions = planning_result.get("sub_questions", [])
        print(sub_questions)
        # Sort by priority and extract queries for current batch
        sub_questions.sort(key=lambda x: x.get("priority", 0.5), reverse=True)
        current_batch = [sq["query"] for sq in sub_questions[:3]]  # Top 3 queries
        
        # For compatibility, set sub_question to the highest priority query
        sub_question = current_batch[0] if current_batch else question
        
        return {
            "sub_questions": sub_questions,
            "current_query_batch": current_batch,
            "sub_question": sub_question  # For compatibility
        }

    def _parallel_retrieve(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Execute parallel retrieval using multiple strategies."""
        queries = state.get("current_query_batch", [state.get("sub_question", state["question"])])
        
        def retrieve_with_strategy(query: str, strategy: str) -> List[Document]:
            """Retrieve documents using specified strategy."""
            try:
                if strategy == "semantic":
                    return self.semantic_retriever.invoke(query)
                elif strategy == "similarity":
                    return self.similarity_retriever.invoke(query)
                else:  # hybrid - combine both
                    semantic_docs = self.semantic_retriever.invoke(query)
                    similarity_docs = self.similarity_retriever.invoke(query)
                    return _dedupe_docs(semantic_docs + similarity_docs)
            except Exception as e:
                print(f"Retrieval error for query '{query}' with strategy '{strategy}': {e}")
                return []
        
        # Execute parallel retrieval
        parallel_results = {}
        all_docs = []
        
        for query in queries:
            # Determine strategy based on sub_questions info or default to semantic
            strategy = "semantic"  # Default strategy
            if state.get("sub_questions"):
                for sq in state.get("sub_questions", []):
                    if sq.get("query") == query:
                        strategy = sq.get("strategy", "semantic")
                        break
            
            print(f"Running retrieval for Query: '{query}' | Strategy: '{strategy}'")

            docs = retrieve_with_strategy(query, strategy)

            print(f"Results for Query: '{query}' | Strategy: '{strategy}'")
            print(docs)

            parallel_results[f"{query}_{strategy}"] = docs

            all_docs.extend(docs)
        
        # Fuse and deduplicate results
        fused_docs = _dedupe_docs(all_docs)
        
        # Update evidence docs
        existing_evidence = state.get("evidence_docs", [])
        updated_evidence = _dedupe_docs(existing_evidence + fused_docs)
        
        # Generate hints from new documents
        new_hints = []
        for d in fused_docs:
            src = d.metadata.get("source") or d.metadata.get("file_path") or "unknown"
            page = d.metadata.get("page", "?")
            title = (d.page_content or "").splitlines()[0][:120] if d.page_content else "No content"
            new_hints.append(f"{src} p.{page}: {title}")
        
        existing_hints = state.get("evidence_hints", [])
        updated_hints = (existing_hints + new_hints)[-50:]  # Keep last 50 hints
        
        return {
            "parallel_results": parallel_results,
            "fused_results": fused_docs,
            "last_batch": fused_docs,  # For compatibility
            "evidence_docs": updated_evidence,
            "evidence_hints": updated_hints
        }

    def _advanced_assess(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Perform comprehensive assessment of context quality and completeness."""
        question = state["question"]
        evidence_docs = state.get("evidence_docs", [])
        evidence_count = len(evidence_docs)
        
        if not evidence_docs:
            return {
                "context_quality_score": 0.0,
                "coverage_score": 0.0,
                "evidence_strength": 0.0,
                "information_gaps": ["No relevant documents found"],
                "detected_contradictions": [],
                "sufficiency_assessment": "insufficient",
                "key_findings": [],
                "gaps": ["No relevant documents found"]  # For compatibility
            }
        
        context = _format_docs(evidence_docs)
        
        prompt = ChatPromptTemplate.from_template(CONTEXT_ASSESSMENT_PROMPT)
        chain = prompt | self.analysis_llm | StrOutputParser()
        
        response = chain.invoke({
            "question": question,
            "context": context,
            "evidence_count": evidence_count
        })
        
        assessment = _safe_json_parse(response, {
            "quality_score": 0.5,
            "coverage_score": 0.5,
            "evidence_strength": 0.5,
            "information_gaps": ["Assessment failed"],
            "contradictions": [],
            "sufficiency_assessment": "partial",
            "key_findings": [],
            "reasoning": "Default assessment"
        })
        
        # Track quality improvements
        previous_quality = state.get("context_quality_score", 0.0)
        current_quality = assessment.get("quality_score", 0.5)
        quality_improvement = current_quality - previous_quality
        
        recent_improvements = state.get("recent_quality_improvements", [])
        recent_improvements.append(quality_improvement)
        recent_improvements = recent_improvements[-3:]  # Keep last 3 improvements
        
        return {
            "context_quality_score": current_quality,
            "coverage_score": assessment.get("coverage_score", 0.5),
            "evidence_strength": assessment.get("evidence_strength", 0.5),
            "information_gaps": assessment.get("information_gaps", []),
            "detected_contradictions": assessment.get("contradictions", []),
            "sufficiency_assessment": assessment.get("sufficiency_assessment", "partial"),
            "key_findings": assessment.get("key_findings", []),
            "recent_quality_improvements": recent_improvements,
            "gaps": assessment.get("information_gaps", [])  # For compatibility
        }

    def _intelligent_decide(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Make intelligent decision about continuing or stopping retrieval."""
        iteration = state.get("iteration", 0)
        max_iters = state.get("max_dynamic_iters", self.default_max_iters)
        complexity = state.get("question_complexity", 5.0)
        
        # Gather assessment data
        assessment = {
            "quality_score": state.get("context_quality_score", 0.0),
            "coverage_score": state.get("coverage_score", 0.0),
            "evidence_strength": state.get("evidence_strength", 0.0),
            "sufficiency_assessment": state.get("sufficiency_assessment", "insufficient"),
            "information_gaps": state.get("information_gaps", []),
            "recent_improvements": state.get("recent_quality_improvements", [])
        }
        
        # Check recent retrieval success
        last_batch_size = len(state.get("last_batch", []))
        recent_success = "successful" if last_batch_size > 0 else "unsuccessful"
        
        prompt = ChatPromptTemplate.from_template(DECISION_MAKING_PROMPT)
        chain = prompt | self.analysis_llm | StrOutputParser()
        
        response = chain.invoke({
            "question": state["question"],
            "iteration": iteration + 1,
            "max_iterations": max_iters,
            "assessment": json.dumps(assessment),
            "recent_success": recent_success,
            "complexity": complexity
        })
        
        decision_result = _safe_json_parse(response, {
            "decision": "continue",
            "confidence": 0.5,
            "reasoning": "Default decision",
            "stop_reasons": [],
            "continue_strategy": "general search",
            "estimated_remaining_hops": 2
        })
        
        should_stop = decision_result.get("decision", "continue").lower() == "stop"
        
        # Additional safety checks
        if iteration + 1 >= max_iters:
            should_stop = True
            decision_result["stop_reasons"].append("Reached maximum iterations")
        
        # Minimum iterations check
        if iteration + 1 < self.min_iters:
            should_stop = False
        
        return {
            "stop": should_stop,
            "iteration": iteration + 1,
            "decision_factors": {
                "quality_score": assessment["quality_score"],
                "coverage_score": assessment["coverage_score"],
                "iteration_ratio": (iteration + 1) / max_iters,
                "complexity_factor": complexity / 10.0
            },
            "continue_probability": decision_result.get("confidence", 0.5),
            "stop_reasons": decision_result.get("stop_reasons", [])
        }

    def _enhanced_synthesis(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Generate comprehensive answer using enhanced synthesis."""
        question = state["question"]
        evidence_docs = state.get("evidence_docs", [])
        
        if not evidence_docs:
            return {
                "final_answer": "I couldn't find any relevant evidence in the knowledge base for this query.",
                "answer_confidence": 0.0
            }
        
        context = _format_docs(evidence_docs)
        quality_score = state.get("context_quality_score", 0.5)
        coverage_score = state.get("coverage_score", 0.5)
        evidence_strength = state.get("evidence_strength", 0.5)
        
        prompt = ChatPromptTemplate.from_template(ENHANCED_SYNTHESIS_PROMPT)
        chain = prompt | self.synthesis_llm | StrOutputParser()
        
        answer = chain.invoke({
            "question": question,
            "context": context,
            "quality_score": quality_score,
            "coverage_score": coverage_score,
            "evidence_strength": evidence_strength
        })
        
        # Calculate answer confidence based on context quality
        confidence = (quality_score * 0.4 + coverage_score * 0.4 + evidence_strength * 0.2)
        
        return {
            "final_answer": answer.strip(),
            "answer_confidence": confidence
        }

    def _advanced_verify(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Perform comprehensive answer verification."""
        question = state["question"]
        answer = state.get("final_answer", "")
        evidence_docs = state.get("evidence_docs", [])
        
        if not evidence_docs or not answer:
            return {"grounded_ok": False}
        
        context = _format_docs(evidence_docs)
        
        prompt = ChatPromptTemplate.from_template(ADVANCED_VERIFICATION_PROMPT)
        chain = prompt | self.analysis_llm | StrOutputParser()
        
        response = chain.invoke({
            "question": question,
            "answer": answer,
            "context": context,
            #"system_prompt":SYSTEM_PROMPT1,
        })
        print("************************************************************************************************")
        print("response :::: ",response)
        print("************************************************************************************************")

        verification = _safe_json_parse(response, {
            "overall_grounding": "fail",
            "factual_grounding": 0.5,
            "logical_consistency": 0.5,
            "completeness": 0.5,
            "source_attribution": 0.5,
            "confidence_calibration": 0.5,
            "issues_found": ["Verification failed"],
            "recommendations": [],
            "final_assessment": "needs_improvement"
        })
        
        grounded_ok = verification.get("overall_grounding", "fail").lower() == "pass"
        
        return {"grounded_ok": grounded_ok}

    # ------------------------- Public API ---------------------------

    def ask(
        self,
        question: str,
        max_iters: Optional[int] = None,
        thread_id: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Execute the enhanced pipeline and return answer with debug info."""
        mi = max_iters if max_iters is not None else self.default_max_iters
        init: EnhancedAgentState = {
            "question": question,
        }
        
        tid = thread_id or f"enhanced-rag-{uuid4().hex}"
        final_state = self.app.invoke(init, config={"configurable": {"thread_id": tid}})
        
        answer = final_state.get("final_answer", "")
        print("************************************************************************************************")
        print("FINAL_ANSWER :::: ",answer)
        print("************************************************************************************************")

        debug = {
            "iterations": final_state.get("iteration", 0),
            "evidence_count": len(final_state.get("evidence_docs", []) or []),
            "grounded_ok": final_state.get("grounded_ok", None),
            "question_complexity": final_state.get("question_complexity", 0.0),
            "context_quality_score": final_state.get("context_quality_score", 0.0),
            "coverage_score": final_state.get("coverage_score", 0.0),
            "answer_confidence": final_state.get("answer_confidence", 0.0),
            "stop_reasons": final_state.get("stop_reasons", []),
            "last_gaps": final_state.get("information_gaps", [])[-3:],
            "last_sub_question": final_state.get("sub_question", "")
        }
        
        return answer, debug

    def stream(
        self,
        question: str,
        max_iters: Optional[int] = None,
        thread_id: Optional[str] = None
    ):
        """Stream per-node events during execution for real-time UIs."""
        mi = max_iters if max_iters is not None else self.default_max_iters
        init: EnhancedAgentState = {"question": question}
        
        tid = thread_id or f"enhanced-rag-{uuid4().hex}"
        
        for ev in self.app.stream(
            init,
            config={"configurable": {"thread_id": tid}},
            stream_mode="updates",
        ):
            if not isinstance(ev, dict) or not ev:
                continue
            
            node, payload = next(iter(ev.items()))
            if not isinstance(payload, dict):
                yield {"node": node, "raw": payload}
                continue
            
            yield {
                "node": node,
                "input": payload.get("input"),
                "output": payload.get("output"),
            }
        
        # Get final state
        final_state = self.app.invoke(init, config={"configurable": {"thread_id": tid}})
        yield {"node": "__final__", "state": final_state}


# Alias for backward compatibility
RAGAgentPipeline = EnhancedRAGPipeline


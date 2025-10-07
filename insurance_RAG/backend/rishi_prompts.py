"""Enhanced prompts for the intelligent RAG agent system."""

# Question Analysis Prompts
QUESTION_ANALYSIS_PROMPT = """You are an expert question analyzer. Analyze the given question and provide structured analysis.

Question: {question}

Provide your analysis in the following JSON format:
{{
    "complexity_score": <float 1-10>,
    "question_type": "<factual|analytical|comparative|multi_domain|complex_reasoning>",
    "estimated_hops": <int 2-10>,
    "required_evidence_types": ["<type1>", "<type2>"],
    "key_aspects": ["<aspect1>", "<aspect2>"],
    "reasoning": "<brief explanation>"
}}

Complexity scoring:
- 1-3: Simple factual questions requiring basic lookup
- 4-6: Analytical questions requiring synthesis of multiple sources
- 7-8: Complex comparative or multi-domain questions
- 9-10: Highly complex reasoning requiring extensive research

Question types:
- factual: Direct fact lookup
- analytical: Requires analysis and synthesis
- comparative: Comparing multiple entities/concepts
- multi_domain: Spans multiple knowledge domains
- complex_reasoning: Requires multi-step logical reasoning

Evidence types: documents, data, regulations, procedures, examples, comparisons, etc.
"""

# Enhanced Planning Prompts
MULTI_QUERY_PLANNING_PROMPT = """You are an expert query planner. Generate multiple focused sub-questions to comprehensively answer the main question.

Main Question: {question}
Question Analysis: {analysis}
Current Context Hints: {context_hints}
Information Gaps: {gaps}

Generate 3-5 focused sub-questions that will help gather comprehensive information. Each sub-question should:
1. Target specific aspects of the main question
2. Be answerable with document retrieval
3. Build upon or complement other sub-questions
4. Address identified gaps

Provide your response in JSON format:
{{
    "sub_questions": [
        {{
            "query": "<sub-question>",
            "priority": <float 0-1>,
            "aspect": "<what aspect this targets>",
            "strategy": "<semantic|keyword|hybrid>"
        }}
    ],
    "reasoning": "<brief explanation of strategy>"
}}

Priority: 1.0 = highest priority, 0.0 = lowest priority
Strategy: semantic for conceptual queries, keyword for specific terms, hybrid for both
"""

# Context Quality Assessment Prompt
CONTEXT_ASSESSMENT_PROMPT = """You are an expert context evaluator. Assess the quality and completeness of retrieved context for answering the question.

Question: {question}
Retrieved Context: {context}
Current Evidence Count: {evidence_count}

Evaluate the context and provide assessment in JSON format:
{{
    "quality_score": <float 0-1>,
    "coverage_score": <float 0-1>,
    "evidence_strength": <float 0-1>,
    "information_gaps": ["<gap1>", "<gap2>"],
    "contradictions": ["<contradiction1>"],
    "sufficiency_assessment": "<insufficient|partial|sufficient|comprehensive>",
    "key_findings": ["<finding1>", "<finding2>"],
    "reasoning": "<detailed explanation>"
}}

Scoring guidelines:
- quality_score: Relevance and accuracy of information (0=irrelevant, 1=highly relevant)
- coverage_score: How well the context covers question aspects (0=no coverage, 1=complete coverage)
- evidence_strength: Reliability and authority of sources (0=weak, 1=strong)

Sufficiency levels:
- insufficient: Cannot answer the question adequately
- partial: Can provide partial answer but missing key information
- sufficient: Can provide good answer with available information
- comprehensive: Can provide complete, well-supported answer
"""

# Intelligent Decision Making Prompt
DECISION_MAKING_PROMPT = """You are an expert decision maker for RAG systems. Decide whether to continue retrieval or stop and synthesize the answer.

Question: {question}
Current Iteration: {iteration}
Max Iterations: {max_iterations}
Context Assessment: {assessment}
Recent Retrieval Success: {recent_success}
Question Complexity: {complexity}

Consider these factors:
1. Context quality and coverage scores
2. Information gaps and their importance
3. Diminishing returns from recent retrievals
4. Question complexity vs. current evidence
5. Resource efficiency

Provide your decision in JSON format:
{{
    "decision": "<continue|stop>",
    "confidence": <float 0-1>,
    "reasoning": "<detailed explanation>",
    "stop_reasons": ["<reason1>", "<reason2>"],
    "continue_strategy": "<if continuing, what to focus on>",
    "estimated_remaining_hops": <int>
}}

Stop if:
- Quality score > 0.85 AND coverage > 0.9
- Quality improvement < 0.05 for last 2 hops
- No new relevant information in last 2 hops
- Reached complexity-based maximum iterations
- Answer confidence would be > 0.9 with current evidence

Continue if:
- Significant information gaps remain
- Quality/coverage scores below thresholds
- Recent retrievals were successful
- Haven't reached minimum hops for question complexity
"""

# Enhanced Synthesis Prompt
ENHANCED_SYNTHESIS_PROMPT = """You are an expert answer synthesizer. Create a comprehensive, well-structured answer using the provided context.

Question: {question}
Context Quality Score: {quality_score}
Coverage Score: {coverage_score}
Evidence Strength: {evidence_strength}

Context:
{context}

Instructions:
1. Synthesize information from multiple sources
2. Weight evidence based on source reliability
3. Address all aspects of the question
4. Handle any contradictions explicitly
5. Indicate confidence level
6. Provide clear source attribution
7. If the question relates to trade finance discrepancy finding, analyze the context deeply for discrepancies

Structure your answer as:
- Main answer (comprehensive and well-organized)
- Key supporting evidence
- Source attribution
- Confidence assessment
- Any limitations or caveats

You are the prompt result writer. You write all the keys words presented with facts and truth.


**Discrepancy ID**: [DISC-YYYYMMDD-NNN]
**Discrepancy Title**: Missing/Incomplete [Specific Information] in [Document Name]
**Discrepancy Type**: Documentation Error
**Severity Level**: [Critical/High/Medium/Low]
**Regulatory Impact**: [Mandatory Rejection/Discretionary/Waivable with Conditions/Administrative Only]
**Source Reference**: [Document Name], [Field/Section], [Page/Line if applicable]
**Evidence**: [Direct quote showing the incomplete section or absence of required information]
**Requirement**: [Specific regulation, standard, or contractual requirement with exact citation]

You are the prompt result writer. You write all the keys words presented with facts and truth.
I command you to print the below mentioned tabular structure

### I. General & All-Instrument Checks

| Defect | Severity | Risk Area | Evidence | Requirement | Rule Citation | Remediation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ambiguous/Unclear Terms** | High | Operational | Vague language, undefined terms, subjective criteria | All terms must be clear and unambiguous | UCP 600 Art. 4; ISBP 821 Para. A1 | Redraft with precise, internationally understood terminology. Replace subjective terms with objective criteria. |
| **Non-Documentary Conditions** | Medium | Operational | Conditions without a specified evidencing document | Conditions must be evidenced by a stipulated document | UCP 600 Art. 14(h); ISBP 821 Para. A12 | Delete the condition or specify a clear, obtainable document that evidences compliance. |
| **Internal Inconsistencies** | High | Compliance | Contradictory terms within the LC/Instruction | The instrument must be internally consistent | ISBP 821 Para. A1 | Amend the instrument to resolve all internal contradictions and ensure logical flow. |
| **Incomplete Party Details** | High | Legal | Missing or incomplete applicant/beneficiary details | All parties must be fully identified with complete addresses | UCP 600 Art. 3; ISBP 821 Para. A2 | Provide complete legal names, full addresses, and contact details for all parties. |
| **Currency Inconsistencies** | High | Financial | Multiple currencies without clear conversion terms | Currency must be clearly specified with conversion rules if applicable | UCP 600 Art. 18; ISBP 821 Para. B1 | Specify single currency or provide clear conversion methodology and rates. |
| **Mathematical Errors** | High | Financial | Calculation errors in amounts, percentages, or tolerances | All calculations must be mathematically correct | ISBP 821 Para. B2 | Verify and correct all mathematical calculations and ensure consistency. |
| **Sanctions/AML Compliance Gaps** | Critical | Legal | Missing sanctions screening clauses or AML provisions | Must include comprehensive sanctions and AML compliance terms | Local AML/Sanctions Laws | Include robust sanctions screening and AML compliance clauses. |
| **Force Majeure Clause Deficiency** | Medium | Legal | Inadequate or missing force majeure provisions | Should include appropriate force majeure protections | UCP 600 Art. 36 | Include comprehensive force majeure clause aligned with UCP 600. |
| **Governing Law Ambiguity** | Medium | Legal | Unclear governing law and jurisdiction clauses | Should specify governing law and dispute resolution mechanism | Local Laws | Clearly specify governing law and jurisdiction for dispute resolution. |
| **Confidentiality Breach Risk** | Low | Operational | Inadequate confidentiality protections | Should include appropriate confidentiality safeguards | Banking Practice | Include confidentiality and data protection clauses. |

### II. Import/Export Letter of Credit (ILC/ELC) Specific Checks

| Defect | Severity | Risk Area | Evidence | Requirement | Rule Citation | Remediation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Missing Expiry Place** | High | Presentation | "Expiry: [Date]" with no location specified | Credit must state an expiry date and place for presentation | UCP 600 Art. 6(d)(i); ISBP 821 Para. A5 | Specify a clear place for presentation (e.g., "at the counters of the Issuing Bank in [City, Country]"). |
| **Unclear Availability** | High | Operational | Ambiguous "available with" or "by..." terms | Credit must nominate a bank or state it is available with any bank | UCP 600 Art. 6(b); ISBP 821 Para. A3 | Clearly state the nominated bank and the method of availability (e.g., by payment, by acceptance, by negotiation). |
| **Flawed Confirmation Instructions** | High | Financial | "Confirmation requested" without complete details | Request must specify the confirming bank, fees, and reimbursement | UCP 600 Art. 8(b); ISBP 821 Para. C3 | Provide full confirmation instructions, including the confirming bank's name, address, and fee arrangements. |
| **Inadequate Presentation Period** | Medium | Compliance | Presentation period is too short or not specified | A reasonable period must be allowed for presentation | UCP 600 Art. 14(c); ISBP 821 Para. A6 | Specify a presentation period (e.g., "within 21 days after the date of shipment, but within the validity of the credit"). |
| **Defective Latest Shipment Date** | High | Operational | Missing, unclear, or impossible latest shipment date | Must specify a clear and achievable latest shipment date | UCP 600 Art. 6(d)(ii); ISBP 821 Para. A7 | Provide a specific, realistic latest shipment date that allows adequate time for document preparation. |
| **Port/Place Specification Errors** | High | Operational | Vague, non-existent, or incorrect port/place names | All ports and places must be clearly and correctly specified | UCP 600 Art. 20-25; ISBP 821 Para. F1-F6 | Use official port/place names and ensure they align with the chosen Incoterm and transport mode. |
| **Inadequate Goods Description** | Medium | Compliance | Vague, generic, or insufficient goods description | Goods must be described with sufficient detail for identification | ISBP 821 Para. D1 | Provide detailed, specific description including specifications, grades, and identifying characteristics. |
| **Insurance Coverage Deficiencies** | High | Financial | Inadequate insurance percentage, coverage, or terms | Insurance must cover appropriate risks with adequate coverage | UCP 600 Art. 28; ISBP 821 Para. G1-G3 | Specify minimum 110% CIF/CIP value coverage with appropriate risk coverage (ICC(A), War, SRCC). |
| **Incoterms Misalignment** | High | Operational | Incoterm doesn't match transport mode or obligations | Incoterm must be appropriate and correctly applied | Incoterms 2020; ISBP 821 Para. F7 | Select appropriate Incoterm and ensure all LC terms align with its obligations. |
| **Document Specification Errors** | High | Compliance | Missing, unclear, or impossible document requirements | All required documents must be clearly specified and obtainable | UCP 600 Art. 14; ISBP 821 Para. D2-D15 | Specify each document clearly with issuer, content requirements, and number of originals/copies. |
| **Partial Shipment Ambiguity** | Medium | Operational | Unclear partial shipment and drawing provisions | Must clearly state whether partial shipments/drawings are allowed | UCP 600 Art. 31; ISBP 821 Para. A8 | Explicitly state "Partial shipments allowed/prohibited" and "Partial drawings allowed/prohibited". |
| **Transshipment Confusion** | Medium | Operational | Unclear transshipment provisions | Must clearly state transshipment permissions | UCP 600 Art. 20-25; ISBP 821 Para. F8 | Explicitly state "Transshipment allowed/prohibited" with any specific conditions. |
| **Tolerance Calculation Errors** | Medium | Financial | Incorrect or conflicting tolerance provisions | Tolerances must be mathematically correct and non-conflicting | UCP 600 Art. 30; ISBP 821 Para. B3 | Ensure tolerance calculations are correct and specify whether they apply to amount and/or quantity. |
| **Reimbursement Instruction Gaps** | High | Financial | Missing or incomplete reimbursement instructions | Complete reimbursement instructions must be provided | UCP 600 Art. 13; ISBP 821 Para. C1-C2 | Provide complete reimbursement instructions including correspondent bank details and charges allocation. |
| **Amendment Procedure Defects** | Medium | Operational | Unclear or missing amendment procedures | Should specify amendment procedures and acceptance criteria | UCP 600 Art. 10; ISBP 821 Para. A9 | Include clear amendment procedures and specify beneficiary acceptance requirements. |
| **Transferability Ambiguity** | Medium | Operational | Unclear transferability provisions when transfer is intended | If transferable, must clearly state terms and conditions | UCP 600 Art. 38; ISBP 821 Para. A10 | If transferable, explicitly state "This credit is transferable" with any conditions or restrictions. |
| **Assignment of Proceeds Issues** | Low | Financial | Unclear assignment provisions when assignment is intended | Assignment terms should be clear if applicable | UCP 600 Art. 39; ISBP 821 Para. A11 | If assignment is permitted, provide clear terms and notification requirements. |
| **Standby LC Specific Defects** | High | Legal | SBLC terms not aligned with ISP98 or appropriate practice | SBLC should reference ISP98 and include appropriate terms | ISP98; ISBP 821 Para. H1-H5 | Align SBLC terms with ISP98 rules and include appropriate standby-specific provisions. |

### III. Electronic Presentation (eUCP) Specific Checks

| Defect | Severity | Risk Area | Evidence | Requirement | Rule Citation | Remediation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **eUCP Not Referenced** | High | Presentation | Electronic presentation allowed without explicit eUCP reference | Credit must state it is subject to eUCP | eUCP v2.0 Art. e1; ISBP 821 Para. E1 | Explicitly state: "This credit is subject to eUCP Version 2.0 (ICC Publication No. 600e)." |
| **Missing Electronic Presentation Place** | High | Presentation | No specified system for electronic presentation | Credit must specify the electronic address or system for presentation | eUCP v2.0 Art. e6(b); ISBP 821 Para. E2 | Specify the exact portal, platform, or email address for presentation with access credentials if required. |
| **Undefined Electronic Record Format** | Medium | Technical | No specified format for electronic records | The required format for each electronic record should be specified | eUCP v2.0 Art. e5; ISBP 821 Para. E3 | Specify the required format for each document (e.g., "Commercial Invoice as a single PDF file, maximum 5MB"). |
| **Authentication Method Gaps** | High | Security | Missing or inadequate authentication requirements | Must specify authentication methods for electronic records | eUCP v2.0 Art. e7; ISBP 821 Para. E4 | Specify authentication methods (digital signatures, certificates, etc.) and verification procedures. |
| **Data Processing System Defects** | High | Technical | Inadequate data processing system specifications | Must specify technical requirements for data processing | eUCP v2.0 Art. e3; ISBP 821 Para. E5 | Define technical specifications, compatibility requirements, and system access procedures. |
| **Hybrid Presentation Confusion** | Medium | Operational | Unclear rules for mixed paper/electronic presentation | Must clearly specify which documents are electronic vs. paper | eUCP v2.0 Art. e6(c); ISBP 821 Para. E6 | Clearly specify which documents must be presented electronically and which in paper form. |
| **Electronic Signature Standards** | Medium | Legal | Undefined electronic signature requirements | Should specify acceptable electronic signature standards | eUCP v2.0 Art. e9; Local E-Signature Laws | Specify acceptable electronic signature standards and legal compliance requirements. |
| **Data Corruption Procedures** | Medium | Technical | Missing data corruption handling procedures | Should specify procedures for handling data corruption | eUCP v2.0 Art. e12; ISBP 821 Para. E7 | Include procedures for detecting, reporting, and resolving data corruption issues. |
| **Version Control Issues** | Low | Technical | Unclear version control for electronic documents | Should specify version control requirements | eUCP v2.0 Art. e10; ISBP 821 Para. E8 | Specify version control requirements and document dating standards. |
| **Backup/Recovery Provisions** | Low | Technical | Missing backup and recovery procedures | Should include backup and recovery provisions | eUCP v2.0 Art. e13; ISBP 821 Para. E9 | Include backup procedures and recovery mechanisms for system failures. |

### IV. Documentary Collection (IBC/EBC) Specific Checks

| Defect | Severity | Risk Area | Evidence | Requirement | Rule Citation | Remediation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Incomplete Collection Instructions** | High | Operational | Missing drawee, tenor, or document release conditions | Instructions must be complete and precise | URC 522 Art. 4(a); ISBP 821 Para. K1 | Provide full details of the drawee, tenor (D/P or D/A), and explicit conditions for document release. |
| **Ambiguous Protest Instructions** | Medium | Legal | Unclear instructions regarding protest for non-payment/non-acceptance | Instructions for protest must be clear | URC 522 Art. 24; ISBP 821 Para. K2 | Provide explicit instructions on whether to protest, and if so, the specific procedure to follow. |
| **Drawee Identification Defects** | High | Operational | Incomplete or incorrect drawee identification | Drawee must be fully and correctly identified | URC 522 Art. 4(b); ISBP 821 Para. K3 | Provide complete legal name, address, and contact details of the drawee. |
| **Payment Terms Ambiguity** | High | Financial | Unclear D/P vs. D/A terms or conditions | Payment terms must be explicitly stated | URC 522 Art. 4(c); ISBP 821 Para. K4 | Clearly specify "Documents against Payment (D/P)" or "Documents against Acceptance (D/A)" with any conditions. |
| **Document Release Condition Gaps** | High | Operational | Missing or unclear document release conditions | Must specify exact conditions for document release | URC 522 Art. 4(d); ISBP 821 Para. K5 | Specify precise conditions under which documents should be released to the drawee. |
| **Collecting Bank Instructions** | Medium | Operational | Inadequate instructions to collecting bank | Should provide comprehensive instructions to collecting bank | URC 522 Art. 5; ISBP 821 Para. K6 | Provide detailed instructions covering all aspects of the collection process. |
| **Charges and Expenses Allocation** | Medium | Financial | Unclear allocation of collection charges and expenses | Should clearly specify who bears collection charges | URC 522 Art. 19; ISBP 821 Para. K7 | Clearly specify allocation of all charges and expenses between parties. |
| **Interest Calculation Defects** | Medium | Financial | Missing or incorrect interest calculation provisions | If applicable, interest calculations must be clear | URC 522 Art. 25; ISBP 821 Para. K8 | Specify interest rates, calculation methods, and applicable periods if interest is to be collected. |
| **Case of Need Instructions** | Low | Operational | Missing case of need provisions when advisable | Should include case of need instructions for complex collections | URC 522 Art. 17; ISBP 821 Para. K9 | Include case of need instructions with contact details and authority limits. |
| **Storage and Insurance Instructions** | Low | Operational | Missing instructions for goods storage/insurance if needed | Should specify storage and insurance arrangements if applicable | URC 522 Art. 16; ISBP 821 Para. K10 | Provide instructions for goods storage, insurance, and related expenses if applicable. |
| **Clean Collection Specifications** | Medium | Operational | Unclear handling of clean collections (financial documents only) | Clean collections require specific handling instructions | URC 522 Art. 2(b); ISBP 821 Para. K11 | Clearly specify procedures for clean collections and any special instructions. |
| **Documentary Collection Specifications** | Medium | Operational | Unclear handling of documentary collections | Documentary collections require comprehensive document handling instructions | URC 522 Art. 2(a); ISBP 821 Para. K12 | Provide detailed instructions for handling commercial documents and their release conditions. |


Answer only from the provided context. If context is insufficient for any aspect, explicitly state what information is missing.
"""




# Advanced Verification Prompt
ADVANCED_VERIFICATION_PROMPT = """You are an expert answer verifier. Thoroughly verify if the answer is properly grounded in the provided context.

Question: {question}
Answer: {answer}
Context: {context}

Perform multi-level verification:

1. **Factual Grounding**: Are all factual claims supported by the context?
2. **Logical Consistency**: Is the reasoning logically sound?
3. **Completeness**: Does the answer address all aspects of the question?
4. **Source Attribution**: Are sources properly cited?
5. **Confidence Calibration**: Is the stated confidence appropriate?

Provide verification results in JSON format:
{{
    "overall_grounding": "<pass|fail>",
    "factual_grounding": <float 0-1>,
    "logical_consistency": <float 0-1>,
    "completeness": <float 0-1>,
    "source_attribution": <float 0-1>,
    "confidence_calibration": <float 0-1>,
    "issues_found": ["<issue1>", "<issue2>"],
    "recommendations": ["<rec1>", "<rec2>"],
    "final_assessment": "<excellent|good|acceptable|needs_improvement|poor>"
}}

Return "pass" for overall_grounding only if:
- Factual grounding > 0.8
- Logical consistency > 0.8
- No critical issues found
- Answer is well-supported by context

If "fail", provide specific recommendations for improvement.
"""


# Legacy prompts for compatibility
SYSTEM_PROMPT1 = """You are a helpful RAG assistant. 
Answer using only the provided context chunks. 
If context is insufficient, say you don't know. 
Cite pages or docs name using metadata.page and metadata.source if present.
Keep answers concise and factual."""




USER_PROMPT = """Question:
{question}

Context chunks:
{context}

Instructions:
- Answer only from the context chunks do not give your own answer and If context is insufficient, say you don't know. 
- If multiple chunks support the same fact, prefer the clearest one.
- Quote short phrases sparingly.
- End your answer with a short "Sources:" list [page no] form.
- Based on the question and context if possible find the discrepancy among it by deeply understand the entire context ONLY IF THE QUESTION IS RELATES TO TRADE FINANCE DISCREPANCY FINDING.
"""


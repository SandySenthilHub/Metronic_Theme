from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import json
import base64
import logging
import re  # Added for regex cleaning
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage
from rag_utils import EnhancedRAGPipeline
import aiofiles
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
import magic
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Insurance AI Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()

# Azure OpenAI configurations
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

# Azure Document Intelligence configurations
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
AZURE_DOCUMENT_INTELLIGENCE_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

# PGVector configurations
PGVECTOR_DATABASE_URL = os.getenv("PGVECTOR_DATABASE_URL")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# Validate environment variables
required_env_vars = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_API_VERSION",
    "AZURE_OPENAI_CHAT_DEPLOYMENT",
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
    "AZURE_DOCUMENT_INTELLIGENCE_KEY",
    "PGVECTOR_DATABASE_URL",
    "COLLECTION_NAME"
]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing environment variable: {var}")

# Initialize Azure GPT-4o for analysis
try:
    llm = AzureChatOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        deployment_name=AZURE_OPENAI_CHAT_DEPLOYMENT,
        temperature=0.0,
        max_tokens=4096,
    )
    logger.info("AzureChatOpenAI initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AzureChatOpenAI: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Failed to initialize AI model: {str(e)}")

# Initialize Azure Document Intelligence client
try:
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_DOCUMENT_INTELLIGENCE_KEY),
        api_version="2024-02-29-preview"
    )
    logger.info("DocumentIntelligenceClient initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize DocumentIntelligenceClient: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Failed to initialize Document Intelligence: {str(e)}")

# Initialize RAG pipeline
try:
    rag_pipeline = EnhancedRAGPipeline(max_iters=3, min_iters=1)
    logger.info("RAG pipeline initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RAG pipeline: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Failed to initialize RAG pipeline: {str(e)}")

# Parser for JSON output
parser = JsonOutputParser()

# Pydantic model for /policy_qa/ input validation
class PolicyQARequest(BaseModel):
    question: str
    thread_id: str

# Maximum file size (10MB) and maximum damaged photos (5)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
MAX_DAMAGED_PHOTOS = 5

# Supported file types for Document Intelligence
SUPPORTED_FILE_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/bmp",
    "image/tiff",
    "image/heif"
]

def generate_claim_table_rows(analysis_json: Any, extracted_data: dict) -> list:
    """
    Converts extracted data and analysis JSON into a list of dicts representing table rows.
    """
    rows = []
    if not isinstance(analysis_json, dict):
        logger.error(f"analysis_json is not a dict: {type(analysis_json)} - {analysis_json}")
        analysis_json = {
            "policy_suggestion": "Unknown",
            "estimated_claim": "Unknown",
            "claim_details": {"Description": "Analysis failed", "Date of Loss": "Unknown"},
            "policy_details": {"Policy Number": "Unknown", "Holder": "Unknown"}
        }

    policy_details = analysis_json.get("policy_details", {})
    policy_number = policy_details.get("Policy Number", "Unknown") if isinstance(policy_details, dict) else "Unknown"
    claim_details = analysis_json.get("claim_details", {})
    date_of_loss = claim_details.get("Date of Loss", "Unknown") if isinstance(claim_details, dict) else "Unknown"
    description = claim_details if isinstance(claim_details, str) else claim_details.get("Description", "See summary") if isinstance(claim_details, dict) else "See summary"
    estimated_loss = analysis_json.get("estimated_claim", "Unknown")

    total_loss = "Yes" if isinstance(description, str) and "total loss" in description.lower() else "No"
    ncb = "Unknown"
    status = "Open"
    claim_type = "Motor"

    rows.append({
        "Claim ID/Policy #": policy_number,
        "Date of Loss": date_of_loss,
        "Type of Claim": claim_type,
        "Description": description,
        "Estimated Loss Amount": estimated_loss,
        "Total Loss": total_loss,
        "No Claim Bonus": ncb,
        "Status": status
    })

    damaged_photos = extracted_data.get("damaged_photos", {}).get("summaries", [])
    for i, photo_summary in enumerate(damaged_photos, 1):
        rows.append({
            "Claim ID/Policy #": f"{policy_number}-D{i}",
            "Date of Loss": date_of_loss,
            "Type of Claim": "Motor - Damage Photo",
            "Description": photo_summary[:100] + "..." if len(photo_summary) > 100 else photo_summary,
            "Estimated Loss Amount": estimated_loss,
            "Total Loss": "No",
            "No Claim Bonus": ncb,
            "Status": status
        })

    return rows[:10]

@app.post("/process_claim/")
async def process_claim(
    emirates_id: UploadFile = File(...),
    driving_license: UploadFile = File(...),
    vehicle_registry: UploadFile = File(...),
    claim_form: UploadFile = File(...),
    damaged_photos: List[UploadFile] = File(...),
    police_report: Optional[UploadFile] = File(None),
    police_document: Optional[UploadFile] = File(None)
):
    """Process uploaded documents for claim analysis using Azure Document Intelligence and vision."""
    try:
        # Validate number of damaged photos
        if len(damaged_photos) > MAX_DAMAGED_PHOTOS:
            raise HTTPException(status_code=422, detail=f"Maximum {MAX_DAMAGED_PHOTOS} damaged photos allowed")

        # Validate file sizes
        files_to_validate = [emirates_id, driving_license, vehicle_registry, claim_form] + damaged_photos
        if police_report:
            files_to_validate.append(police_report)
        for file in files_to_validate:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(status_code=422, detail=f"File {file.filename} exceeds 10MB limit")
            await file.seek(0)
            logger.info(f"Received file: {file.filename}, size: {len(content)} bytes")

        extracted_data = {}

        # Define single-file documents
        documents = [
            ("emirates_id", emirates_id),
            ("driving_license", driving_license),
            ("vehicle_registry", vehicle_registry),
            ("claim_form", claim_form)
        ]
        if police_report:
            documents.append(("police_report", police_report))
        if police_document:
            documents.append(("police_document", police_document))

        # Process single-file documents
        for doc_type, file in documents:
            logger.info(f"Processing {doc_type}: {file.filename}")
            async with aiofiles.tempfile.NamedTemporaryFile(suffix=f".{file.filename.split('.')[-1]}", delete=False) as temp_file:
                content = await file.read()
                await temp_file.write(content)
                temp_path = temp_file.name

            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(temp_path)
            if mime_type not in SUPPORTED_FILE_TYPES:
                logger.error(f"Unsupported file type for {doc_type}: {mime_type}")
                extracted_data[doc_type] = {
                    "extracted_details": {"error": f"Unsupported file type: {mime_type}"},
                    "summary": "Failed to process document"
                }
                os.unlink(temp_path)
                continue

            try:
                with open(temp_path, "rb") as f:
                    document_content = f.read()
                    # Try prebuilt-document, fall back to prebuilt-read
                    model_id = "prebuilt-document"
                    try:
                        poller = document_intelligence_client.begin_analyze_document(
                            model_id=model_id,
                            body=document_content
                        )
                        result: AnalyzeResult = poller.result()
                    except ResourceNotFoundError:
                        logger.warning(f"Model {model_id} not found for {doc_type}, falling back to prebuilt-read")
                        model_id = "prebuilt-read"
                        poller = document_intelligence_client.begin_analyze_document(
                            model_id=model_id,
                            body=document_content
                        )
                        result: AnalyzeResult = poller.result()

                extracted_details = {}
                if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
                    for kv_pair in result.key_value_pairs:
                        if kv_pair.key and kv_pair.value:
                            extracted_details[kv_pair.key.content] = kv_pair.value.content
                else:
                    extracted_details["raw_text"] = result.content

                summary = result.content[:200] + "..." if len(result.content) > 200 else result.content
                extracted_data[doc_type] = {
                    "extracted_details": extracted_details,
                    "summary": summary
                }
                print(f"Extracted data for {doc_type}: {extracted_data[doc_type]}")
                logger.info(f"Document Intelligence processed {doc_type} successfully with model {model_id}")
            except (ResourceNotFoundError, HttpResponseError) as e:
                logger.error(f"Document Intelligence failed for {doc_type}: {str(e)}")
                extracted_data[doc_type] = {
                    "extracted_details": {"error": f"Processing failed: {str(e)}"},
                    "summary": "Failed to process document"
                }
                logger.warning(f"Fallback applied for {doc_type}")
            except Exception as e:
                logger.error(f"Unexpected error for {doc_type}: {str(e)}")
                extracted_data[doc_type] = {
                    "extracted_details": {"error": f"Unexpected error: {str(e)}"},
                    "summary": "Failed to process document"
                }
                logger.warning(f"Fallback applied for {doc_type}")
            finally:
                os.unlink(temp_path)

        # Process damaged photos using vision LLM
        photo_summaries = []
        for photo in damaged_photos:
            logger.info(f"Processing damaged photo: {photo.filename}")
            async with aiofiles.tempfile.NamedTemporaryFile(suffix=f".{photo.filename.split('.')[-1]}", delete=False) as temp_file:
                content = await photo.read()
                await temp_file.write(content)
                temp_path = temp_file.name

            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(temp_path)
            if mime_type not in ["image/jpeg", "image/png"]:
                logger.error(f"Unsupported file type for damaged photo {photo.filename}: {mime_type}")
                photo_summaries.append(f"Unsupported file type: {mime_type}")
                os.unlink(temp_path)
                continue

            try:
                with open(temp_path, "rb") as f:
                    base64_image = base64.b64encode(f.read()).decode('utf-8')

                vision_prompt = (
                    "You are an insurance damage assessor. Describe the vehicle damage visible in this image in detail, "
                    "including affected parts, severity (minor/moderate/severe), and estimated repair needs. "
                    "If no damage is visible, say 'No visible damage'."
                )

                response = llm.invoke([
                    HumanMessage(content=[
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                    ])
                ])
                summary = response.content.strip()
                photo_summaries.append(summary)
                logger.info(f"Vision analysis for damaged photo: {photo.filename} - Summary: {summary[:100]}...")
            except Exception as e:
                logger.error(f"Vision analysis failed for damaged photo {photo.filename}: {str(e)}")
                photo_summaries.append(f"Image analysis failed: {str(e)}")
            finally:
                os.unlink(temp_path)

        extracted_data["damaged_photos"] = {"summaries": photo_summaries}
        print(f"Final extracted data: {extracted_data}")

        # Analyze extracted data
        analysis_prompt = ChatPromptTemplate.from_template("""
        You are an insurance claims analyst. Analyze the extracted document details: {extracted_data}

        Instructions:
        - Suggest a policy type (e.g., Comprehensive Motor, Third-Party Liability) based on data or use "Unknown" if unclear.
        - Estimate claim amount (e.g., "$5000") or "Unknown" if data is insufficient.
        - Provide claim details (e.g., date, description) or "Insufficient data" if missing.
        - Provide policy details (e.g., policy number, holder) or "Insufficient data" if missing.
        - If data is incomplete, suggest manual review and use placeholders.
        - Output must be valid JSON, enclosed in ```json``` delimiters.
        - Do not use indentation or newlines inside the JSON object that could cause parsing errors.

        ```json{{"policy_suggestion": "<policy type>","estimated_claim": "<amount or Unknown>","claim_details": {{"Date of Loss": "<date or Unknown>","Description": "<details or Insufficient data>"}},"policy_details": {{"Policy Number": "<number or Unknown>","Holder": "<name or Unknown>"}}}}```
        """)

        logger.info("Analyzing extracted data")
        try:
            analysis_response = llm.invoke(analysis_prompt.format(extracted_data=json.dumps(extracted_data, ensure_ascii=False)))
            print(f"Raw LLM analysis response: {analysis_response.content}")
            try:
                # Clean the response: Strip whitespace, remove delimiters, and extract JSON using regex if needed
                response_content = analysis_response.content.strip()
                response_content = re.sub(r'^\s*```json\s*|\s*```\s*$', '', response_content).strip()
                # Remove any leading newlines or tabs
                response_content = re.sub(r'^\s+', '', response_content)
                # Replace indented newlines with compact form
                response_content = response_content.replace('\n', '').replace('  ', '')
                print(f"Cleaned response for parsing: {response_content}")
                analysis = parser.parse(response_content)
                if not isinstance(analysis, dict):
                    logger.error(f"Parsed analysis is not a dict: {type(analysis)} - {analysis}")
                    analysis = {
                        "policy_suggestion": "Unknown",
                        "estimated_claim": "Unknown",
                        "claim_details": {"Description": "Analysis failed", "Date of Loss": "Unknown"},
                        "policy_details": {"Policy Number": "Unknown", "Holder": "Unknown"}
                    }
            except Exception as parse_error:
                logger.error(f"JSON parsing failed: {str(parse_error)} - Raw: {analysis_response.content}")
                analysis = {
                    "policy_suggestion": "Unknown",
                    "estimated_claim": "Unknown",
                    "claim_details": {"Description": f"Invalid JSON output: {str(parse_error)}"},
                    "policy_details": {"Policy Number": "Unknown", "Holder": "Unknown"}
                }
            print(f"Parsed analysis: {analysis}")
            logger.info("Analysis completed")
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

        # Generate table rows
        claim_table_rows = generate_claim_table_rows(analysis, extracted_data)

        # Generate structured report
        report_prompt = ChatPromptTemplate.from_template("""
        You are an insurance claims reporting assistant.

        Input: {analysis_json}
        Claim Table Rows: {claim_table_rows}

        Task: Generate a comprehensive claim report in Markdown format:

        ---
        Policy Suggestion: <policy_suggestion>
        Estimated Claim: <estimated_claim>
        Claim Details: <claim_details>
        Policy Details: <policy_details>

        ## Executive Summary:
        - Provide a 1-2 paragraph overview of the claim(s), financial exposure, and 2-3 underwriting recommendations.
        - Mention total loss or NCB eligibility impacts.

        ## Claim Details Table:
        | Claim ID/Policy # | Date of Loss | Type of Claim | Description (brief) | Estimated Loss Amount | Total Loss (Yes/No) | No Claim Bonus (Yes/No/Unknown) | Status |
        |-------------------|--------------|---------------|---------------------|-----------------------|---------------------|-------------------------------|--------|
        Populate from Claim Table Rows, limit to 5-10 rows, highlight total loss rows.

        ## Risk Analysis:
        - Bullet points on key drivers, trends, quantifications, total loss patterns, NCB impacts.

        ## Underwriting Implications:
        - Bulleted recommendations with rationale and next steps.
        - Address NCB adjustments.

        ## Appendices:
        - Raw data excerpts or chart descriptions (e.g., claim frequency by type).

        Output strictly in Markdown format.
        """)

        try:
            report_response = llm.invoke(
                report_prompt.format(
                    analysis_json=json.dumps(analysis, ensure_ascii=False),
                    claim_table_rows=json.dumps(claim_table_rows, ensure_ascii=False)
                )
            )
            report_content = report_response.content
            print(f"Generated report: {report_content}")
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            report_content = """
            ---
            Policy Suggestion: Unknown
            Estimated Claim: Unknown
            Claim Details: Report generation failed
            Policy Details: Unknown

            ## Executive Summary:
            Unable to generate report due to processing error. Manual review required.

            ## Claim Details Table:
            | Claim ID/Policy # | Date of Loss | Type of Claim | Description (brief) | Estimated Loss Amount | Total Loss (Yes/No) | No Claim Bonus (Yes/No/Unknown) | Status |
            |-------------------|--------------|---------------|---------------------|-----------------------|---------------------|-------------------------------|--------|
            | Unknown           | Unknown      | Motor         | Report generation failed | Unknown             | No                  | Unknown                       | Open   |

            ## Risk Analysis:
            - Unable to analyze due to processing error.

            ## Underwriting Implications:
            - Manual review required to process claim.
            """
            logger.warning("Fallback report generated")

        return JSONResponse(content={
            "status": "success",
            "analysis": analysis,
            "claims_report": report_content
        })

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/workshop_suggestion/")
async def workshop_suggestion(
    workshop1: UploadFile = File(...),
    workshop2: UploadFile = File(...),
    workshop3: UploadFile = File(...)
):
    """Process uploaded workshop summaries for analysis and suggestion."""
    try:
        # Validate file sizes
        for file in [workshop1, workshop2, workshop3]:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(status_code=422, detail=f"File {file.filename} exceeds 10MB limit")
            await file.seek(0)
            logger.info(f"Received file: {file.filename}, size: {len(content)} bytes")

        extracted_data = {}

        # Process workshop summaries
        for doc_type, file in [
            ("workshop1", workshop1),
            ("workshop2", workshop2),
            ("workshop3", workshop3)
        ]:
            logger.info(f"Processing {doc_type}: {file.filename}")
            async with aiofiles.tempfile.NamedTemporaryFile(suffix=f".{file.filename.split('.')[-1]}", delete=False) as temp_file:
                content = await file.read()
                await temp_file.write(content)
                temp_path = temp_file.name

            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(temp_path)
            if mime_type not in SUPPORTED_FILE_TYPES:
                logger.error(f"Unsupported file type for {doc_type}: {mime_type}")
                extracted_data[doc_type] = {
                    "extracted_details": {"error": f"Unsupported file type: {mime_type}"},
                    "summary": "Failed to process document"
                }
                os.unlink(temp_path)
                continue

            try:
                with open(temp_path, "rb") as f:
                    document_content = f.read()
                    # Try prebuilt-document, fall back to prebuilt-read
                    model_id = "prebuilt-document"
                    try:
                        poller = document_intelligence_client.begin_analyze_document(
                            model_id=model_id,
                            body=document_content
                        )
                        result: AnalyzeResult = poller.result()
                    except ResourceNotFoundError:
                        logger.warning(f"Model {model_id} not found for {doc_type}, falling back to prebuilt-read")
                        model_id = "prebuilt-read"
                        poller = document_intelligence_client.begin_analyze_document(
                            model_id=model_id,
                            body=document_content
                        )
                        result: AnalyzeResult = poller.result()

                extracted_details = {}
                if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
                    for kv_pair in result.key_value_pairs:
                        if kv_pair.key and kv_pair.value:
                            extracted_details[kv_pair.key.content] = kv_pair.value.content
                else:
                    extracted_details["raw_text"] = result.content

                summary = result.content[:200] + "..." if len(result.content) > 200 else result.content
                extracted_data[doc_type] = {
                    "extracted_details": extracted_details,
                    "summary": summary
                }
                print(f"Extracted data for {doc_type}: {extracted_data[doc_type]}")
                logger.info(f"Document Intelligence processed {doc_type} successfully with model {model_id}")
            except (ResourceNotFoundError, HttpResponseError) as e:
                logger.error(f"Document Intelligence failed for {doc_type}: {str(e)}")
                extracted_data[doc_type] = {
                    "extracted_details": {"error": f"Processing failed: {str(e)}"},
                    "summary": "Failed to process document"
                }
                logger.warning(f"Fallback applied for {doc_type}")
            except Exception as e:
                logger.error(f"Unexpected error for {doc_type}: {str(e)}")
                extracted_data[doc_type] = {
                    "extracted_details": {"error": f"Unexpected error: {str(e)}"},
                    "summary": "Failed to process document"
                }
                logger.warning(f"Fallback applied for {doc_type}")
            finally:
                os.unlink(temp_path)

        print(f"Final extracted data: {extracted_data}")

        # Analyze workshop summaries
        analysis_prompt = ChatPromptTemplate.from_template("""
        You are an insurance workshop analyst. Analyze the extracted workshop summaries: {extracted_data}

        Instructions:
        - For each workshop, extract key factors: estimated cost, repair time, quality of repairs, parts used, warranty, and any other relevant details.
        - Compare the workshops based on cost-effectiveness, quality, speed, and overall benefit to customer (e.g., convenience, warranty) and insurance agency (e.g., cost savings, reliability).
        - Suggest the best workshop, explaining why it's beneficial for both parties.
        - If data is incomplete, note it and suggest manual review.
        - Output must be valid JSON, enclosed in ```json``` delimiters.
        - Do not use indentation or newlines inside the JSON object that could cause parsing errors.

        ```json{{"workshop1_analysis": "<summary of workshop1>","workshop2_analysis": "<summary of workshop2>","workshop3_analysis": "<summary of workshop3>","comparison": "<comparison details>","suggestion": "<suggested workshop and reasoning>"}}```
        """)

        logger.info("Analyzing workshop data")
        try:
            analysis_response = llm.invoke(analysis_prompt.format(extracted_data=json.dumps(extracted_data, ensure_ascii=False)))
            print(f"Raw LLM workshop analysis response: {analysis_response.content}")
            try:
                response_content = analysis_response.content.strip()
                response_content = re.sub(r'^\s*```json\s*|\s*```\s*$', '', response_content).strip()
                response_content = re.sub(r'^\s+', '', response_content)
                response_content = response_content.replace('\n', '').replace('  ', '')
                print(f"Cleaned response for parsing: {response_content}")
                analysis = parser.parse(response_content)
                if not isinstance(analysis, dict):
                    logger.error(f"Parsed workshop analysis is not a dict: {type(analysis)} - {analysis}")
                    analysis = {
                        "workshop1_analysis": "Analysis failed",
                        "workshop2_analysis": "Analysis failed",
                        "workshop3_analysis": "Analysis failed",
                        "comparison": "Insufficient data",
                        "suggestion": "Manual review required"
                    }
            except Exception as parse_error:
                logger.error(f"Workshop JSON parsing failed: {str(parse_error)} - Raw: {analysis_response.content}")
                analysis = {
                    "workshop1_analysis": "Invalid JSON output from LLM",
                    "workshop2_analysis": "Invalid JSON output from LLM",
                    "workshop3_analysis": "Invalid JSON output from LLM",
                    "comparison": "Insufficient data",
                    "suggestion": "Manual review required"
                }
            print(f"Parsed workshop analysis: {analysis}")
            logger.info("Workshop analysis completed")
        except Exception as e:
            logger.error(f"Workshop analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Workshop analysis error: {str(e)}")

        # Generate workshop suggestion report
        report_prompt = ChatPromptTemplate.from_template("""
        You are a workshop suggestion assistant.

        Input: {analysis_json}

        Task: Generate a comprehensive workshop suggestion report in Markdown format:

        ---
        ## Workshop 1 Analysis:
        <workshop1_analysis>

        ## Workshop 2 Analysis:
        <workshop2_analysis>

        ## Workshop 3 Analysis:
        <workshop3_analysis>

        ## Comparison:
        <comparison>

        ## Suggested Workshop:
        <suggestion>

        Output strictly in Markdown format.
        """)

        try:
            report_response = llm.invoke(
                report_prompt.format(
                    analysis_json=json.dumps(analysis, ensure_ascii=False)
                )
            )
            report_content = report_response.content
            print(f"Generated workshop report: {report_content}")
        except Exception as e:
            logger.error(f"Workshop report generation failed: {str(e)}")
            report_content = """
            ---
            ## Workshop 1 Analysis:
            Analysis failed

            ## Workshop 2 Analysis:
            Analysis failed

            ## Workshop 3 Analysis:
            Analysis failed

            ## Comparison:
            Insufficient data

            ## Suggested Workshop:
            Manual review required
            """
            logger.warning("Fallback workshop report generated")

        return JSONResponse(content={
            "status": "success",
            "analysis": analysis,
            "workshop_report": report_content
        })

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/policy_qa/")
async def policy_qa(request: PolicyQARequest):
    """Answer policy-related questions using RAG pipeline."""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=422, detail="Question cannot be empty")
        
        logger.info(f"Processing question: {request.question}")
        final_answer, debug_info = rag_pipeline.ask(
            question=request.question,
            thread_id=request.thread_id
        )
        debug_info["evidence_docs"] = [
            {"metadata": doc.metadata, "page_content": doc.page_content}
            for doc in debug_info.get("evidence_docs", [])
        ]
        logger.info(f"Question processed successfully: {request.question}")
        return JSONResponse(content={
            "status": "success",
            "answer": final_answer,
            "debug_info": debug_info
        })
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint to verify server is running."""
    return JSONResponse(content={"status": "healthy"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
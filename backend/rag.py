import os
from dotenv import load_dotenv
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pinecone import Pinecone
from langchain_community.vectorstores import Pinecone as Pine
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from openai import OpenAI
import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
import PyPDF2

load_dotenv(override=True)
OPENAI_KEY=os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
parser = StrOutputParser()

pc=Pinecone(api_key=PINECONE_API_KEY)
index=pc.Index("pdscreening")
embeddings = OpenAIEmbeddings( model="text-embedding-3-small", openai_api_key=OPENAI_KEY)
vectorstore=PineconeVectorStore(index, embeddings)

messages=[{
             'role': 'system',
                'content': f""""You are an AI assistant for the take2 Parkinson's Disease screening platform. Your role is to:
                1. Explain test results and risk assessments to users in clear, non-technical language
                2. Provide information about PD biomarkers, symptoms, and early detection
                3. Answer questions about the scientific research behind each screening method (typing dynamics, voice analysis, eye blink detection)
                4. Offer guidance on next steps based on risk levels
                5. Always emphasize that this is a screening tool, not a diagnostic tool, and recommend professional medical consultation when appropriate

                Use the provided context to give accurate, evidence-based responses. Be empathetic and clear, especially when discussing health concerns.
                """
            }]

client=OpenAI(api_key=OPENAI_KEY)

def load_data(publications_dir="publications"):
    """
    Loads all PDF research documents from a directory, splits into chunks,
    creates embeddings and uploads to Pinecone.

    Args:
        publications_dir: Path to directory containing PDF files with PD research/documentation
    """
    import glob
    import os

    # Find all PDF files in the publications directory
    pdf_files = glob.glob(os.path.join(publications_dir, "*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {publications_dir}")
        return

    print(f"Found {len(pdf_files)} PDF files to process:")
    for pdf_file in pdf_files:
        print(f"  - {os.path.basename(pdf_file)}")

    all_chunks = []

    # Extract text from all PDFs
    for pdf_path in pdf_files:
        print(f"\nProcessing: {os.path.basename(pdf_path)}")
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ''
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n\n'

                if not text.strip():
                    print(f"  Warning: No text extracted from {os.path.basename(pdf_path)}")
                    continue

                # Split text into chunks with metadata
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=2000,
                    chunk_overlap=200,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )

                # Create documents with metadata
                chunks = text_splitter.create_documents(
                    [text],
                    metadatas=[{"source": os.path.basename(pdf_path)}]
                )

                all_chunks.extend(chunks)
                print(f"  Extracted {len(chunks)} chunks from {os.path.basename(pdf_path)}")

        except Exception as e:
            print(f"  Error processing {os.path.basename(pdf_path)}: {str(e)}")
            continue

    if not all_chunks:
        print("No chunks extracted from any PDFs")
        return

    print(f"\nTotal chunks to upload: {len(all_chunks)}")

    # Create embeddings and upload to Pinecone
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_KEY
    )

    vectorstore_upload = PineconeVectorStore.from_existing_index(
        index_name="pdscreening",
        embedding=embeddings
    )

    # Upload in batches
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        vectorstore_upload.add_documents(batch)
        print(f"Uploaded batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")

    print(f"\n✅ Data loaded successfully! {len(all_chunks)} chunks from {len(pdf_files)} PDFs")
    
def get_relevant_info(query):
    context=vectorstore.similarity_search(query, k=6)
    formatted_user_query = f"""
        This is the User's Query:\n
        {query}
        This is the context retrieved:\n
        {context}
    
    """
    messages.append(
            {
                'role': 'user',
                'content': formatted_user_query
            })
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )
    out = response.choices[0].message.content
    print(out)
    return out



def chat_with_context(query: str, user_results: dict = None) -> str:
    """
    Enhanced chat function that includes user's test results as context

    Args:
        query: User's question
        user_results: Optional dict with typing_results, voice_results, blink_results

    Returns:
        AI response with RAG context
    """
    # Build context with user results if provided
    user_context = ""
    if user_results:
        user_context = "\n\nUser's Test Results:\n"
        if user_results.get("typing_results"):
            typing = user_results["typing_results"]
            user_context += f"- Typing Risk Score: {typing.get('risk_score', 'N/A')}\n"
        if user_results.get("voice_results"):
            voice = user_results["voice_results"]
            llm = voice.get("llm_analysis", {}).get("risk_assessment", {})
            user_context += f"- Voice Risk Score: {llm.get('overall_risk_score', 'N/A')}\n"
            user_context += f"- Voice Risk Category: {llm.get('risk_category', 'N/A')}\n"
        if user_results.get("blink_results"):
            blink = user_results["blink_results"]
            user_context += f"- Blink Rate: {blink.get('blink_rate', 'N/A')} blinks/min\n"

    # Get RAG context
    context = vectorstore.similarity_search(query, k=6)

    # Format query with context
    formatted_query = f"""
    User's Query: {query}
    {user_context}

    Relevant Knowledge Base Context:
    {context}

    Please provide a helpful, accurate response based on the context provided.
    """

    messages_copy = messages.copy()
    messages_copy.append({
        'role': 'user',
        'content': formatted_query
    })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages_copy,
    )

    return response.choices[0].message.content

if __name__=="__main__":
    query="What are the early signs of Parkinson's disease?"
    output=chat_with_context(query)
    print(output)
    # load_data()
import os
from dotenv import load_dotenv

# Authentication (Standard for Storage)
from azure.identity import DefaultAzureCredential

# Authentication (Keys for Search)
from azure.core.credentials import AzureKeyCredential

# Azure AI Search
from azure.search.documents import SearchClient

# Azure OpenAI
from openai import AzureOpenAI

# Azure Storage
from azure.storage.blob import BlobServiceClient

# -------------------------------------------------------------------------
# SETUP
# -------------------------------------------------------------------------

load_dotenv()

# Storage Config (No Connection String needed)
STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")

# Search Config (Key-based)
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

# OpenAI Config (Key-based)
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")


# -------------------------------------------------------------------------
# FUNCTION 1: UPLOAD FILES (Identity Based)
# -------------------------------------------------------------------------

def upload_file(username: str, local_file_path: str):
    """
    Uploads using your 'az login' credentials.
    Requires 'Storage Blob Data Contributor' role.
    """
    try:
        print(f"\n--- Authenticating Upload for User: {username} ---")

        # Use DefaultAzureCredential
        # This looks for: Environment Vars -> Workload Identity -> Managed Identity -> AZ CLI (az login)
        credential = DefaultAzureCredential()

        # Connect using the URL + Credential (No keys)
        blob_service_client = BlobServiceClient(account_url=STORAGE_ACCOUNT_URL, credential=credential)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)

        filename = os.path.basename(local_file_path)

        # Virtual Folder Structure
        blob_name = f"{username}/{filename}"

        print(f"Uploading '{filename}' to '{blob_name}'...")

        blob_client = container_client.get_blob_client(blob_name)

        with open(local_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        print("✅ Upload Successful!")
        print("⚠️  REMINDER: You must run the Azure AI Search Indexer manually for this file to appear in search.")
        return True

    except Exception as e:
        print(f"❌ Upload Failed: {e}")
        print("\n[TROUBLESHOOTING]")
        print("1. Did you run 'az login' in your terminal?")
        print("2. Does your account have 'Storage Blob Data Contributor' role on this storage account?")
        return False


# -------------------------------------------------------------------------
# FUNCTION 2: SEARCH (Server-Side Filtering)
# -------------------------------------------------------------------------

def search_documents(username: str, query: str, top_k: int = 3):
    """
    Searches Azure AI Search using SERVER-SIDE FILTERING.
    """
    try:
        print(f"--- Searching index '{SEARCH_INDEX_NAME}' for: '{query}' ---")

        search_client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=SEARCH_INDEX_NAME,
            credential=AzureKeyCredential(SEARCH_API_KEY)
        )

        user_folder_url_prefix = f"{STORAGE_ACCOUNT_URL}/{CONTAINER_NAME}/{username}/"
        upper_bound = user_folder_url_prefix + "~"

        filter_expression = (
            f"metadata_storage_path ge '{user_folder_url_prefix}' and "
            f"metadata_storage_path lt '{upper_bound}'"
        )

        results = search_client.search(
            search_text=query,
            filter=filter_expression,
            select=["content", "metadata_storage_path"],
            top=top_k
        )

        documents = []
        for result in results:
            documents.append({
                "content": result.get("content"),
                "source": result.get("metadata_storage_path")
            })

        print(f"Found {len(documents)} relevant documents for user '{username}'.")
        return documents

    except Exception as e:
        print(f"ERROR: Search failed. Details: {e}")
        return []


# -------------------------------------------------------------------------
# FUNCTION 3: GENERATE ANSWER
# -------------------------------------------------------------------------

def generate_rag_answer(user_question: str, context_docs: list):
    try:
        print("--- Generating answer with Azure OpenAI... ---")

        if not context_docs:
            return "No relevant documents found. (Did the Indexer run?)"

        context_text = "\n\n".join([f"Source: {doc['source']}\nContent: {doc['content']}" for doc in context_docs])

        client = AzureOpenAI(
            azure_endpoint=OPENAI_ENDPOINT,
            api_key=OPENAI_API_KEY,
            api_version=OPENAI_API_VERSION
        )

        response = client.chat.completions.create(
            model=OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Answer based only on context."},
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {user_question}"}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"ERROR: OpenAI generation failed. Details: {e}")
        return "Error generating answer."


# -------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("      STUDENT PDF RAG SYSTEM (Identity Auth)      ")
    print("=" * 60)

    # 1. Login
    current_username = input("Enter your username (e.g., Dheeraj): ").strip()
    if not current_username: return

    # 2. Upload (Uses az login credentials)
    print("-" * 60)
    upload_choice = input("Do you want to upload a new PDF file? (yes/no): ").lower().strip()

    if upload_choice in ['yes', 'y']:
        file_path = input("Enter the full path to your PDF file: ").strip()
        file_path = file_path.replace('"', '').replace("'", "")

        if os.path.exists(file_path):
            upload_file(current_username, file_path)
        else:
            print("❌ File not found.")

    # 3. Question Loop
    while True:
        print("\n" + "=" * 60)
        user_query = input(f"Ask a question (or type 'exit'): ").strip()

        if user_query.lower() in ['exit', 'quit']:
            break

        if not user_query: continue

        docs = search_documents(current_username, user_query)
        answer = generate_rag_answer(user_query, docs)

        print("\n" + "-" * 30)
        print("AI ANSWER:")
        print(answer)
        print("-" * 30)


if __name__ == "__main__":
    main()
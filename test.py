print("🔍 Checking imports...")

try:
    from groq import Groq
    print("✅ groq installed")
except Exception as e:
    print("❌ groq error:", e)

try:
    from langchain_text_splitters import CharacterTextSplitter
    print("✅ langchain_text_splitters installed")
except Exception as e:
    print("❌ langchain_text_splitters error:", e)

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    print("✅ langchain_community.embeddings installed")
except Exception as e:
    print("❌ langchain_community.embeddings error:", e)

try:
    from langchain_community.vectorstores import FAISS
    print("✅ langchain_community.vectorstores installed")
except Exception as e:
    print("❌ langchain_community.vectorstores error:", e)

print("🔍 Test complete.")
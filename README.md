# IUB Hybrid Chatbot Patch

This patch upgrades the chatbot from simple RAG-only answering to:

1. Structured deterministic answering for high-confidence university facts
2. RAG fallback for broad descriptive questions
3. Simple terminal memory for follow-up questions such as "what about Group-B?"
4. Safer API response with optional memory support
5. DOCX table extraction support for future re-ingestion

## Files included

- backend/rag/structured_kb.py
- backend/rag/structured_answer.py
- backend/terminal_chat.py
- backend/app.py
- backend/rag/extract.py

## How to apply

Copy these files into your existing project:

D:\Projects\iubc\backend

Then run:

```powershell
cd D:\Projects\iubc\backend
python terminal_chat.py
```

## Test questions

- Who is Director IT?
- Who is VC of IUB?
- What campuses does IUB have?
- What is fee of CS?
- What is full fee of CS?
- and what about Group-B?
- What is admission criteria for BS Computer Science?
- What scholarships are available at IUB?
- What hostel facilities are available at IUB?

## Optional re-ingestion

Because extract.py now supports DOCX tables, you can later rebuild the vector database:

```powershell
cd D:\Projects\iubc\backend
Remove-Item -Recurse -Force .\chroma_db
Remove-Item -Recurse -Force .\processed_data
python -m rag.ingest
```

Do this only after testing the patch first.

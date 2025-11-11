from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
import tempfile
import requests
import os
import json
from dotenv import load_dotenv
import groq

load_dotenv()
app = FastAPI(title="PDF Query System")
groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

class QueryRequest(BaseModel):
    documents: str
    questions: List[str]

def extract_text_from_pdf(pdf_path):
    import fitz
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text

def find_relevant_text(question, full_text, max_length=3000):
    paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]
    question_words = set(question.lower().split())
    
    scored_paragraphs = []
    for para in paragraphs:
        para_words = set(para.lower().split())
        score = len(question_words.intersection(para_words))
        if score > 0:
            scored_paragraphs.append((score, para))
    
    scored_paragraphs.sort(reverse=True)
    relevant_text = ""
    
    for score, para in scored_paragraphs:
        if len(relevant_text) + len(para) < max_length:
            relevant_text += para + "\n\n"
        else:
            break
    
    if not relevant_text:
        relevant_text = full_text[:max_length]
    
    return relevant_text

def answer_with_groq(question, relevant_text):
    try:
        prompt = f"""Answer briefly and naturally based on this document content:

{relevant_text}

Question: {question}

Give a direct 1-2 sentence answer. Don't quote the document."""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>PDF Query System</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }
        .container { 
            max-width: 800px; margin: 0 auto; background: white; 
            border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .content { padding: 40px; }
        .tabs { display: flex; margin-bottom: 30px; background: #f8f9fa; border-radius: 10px; padding: 5px; }
        .tab { flex: 1; padding: 15px; text-align: center; border-radius: 8px; cursor: pointer; transition: all 0.3s; font-weight: 600; }
        .tab.active { background: #667eea; color: white; }
        .tab:hover:not(.active) { background: #e9ecef; }
        .form-group { margin-bottom: 25px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #495057; }
        input, textarea { 
            width: 100%; padding: 15px; border: 2px solid #e9ecef; 
            border-radius: 10px; font-size: 16px; transition: border-color 0.3s;
        }
        input:focus, textarea:focus { outline: none; border-color: #667eea; }
        .drop-zone { 
            border: 3px dashed #dee2e6; border-radius: 15px; padding: 50px; 
            text-align: center; transition: all 0.3s; cursor: pointer;
        }
        .drop-zone:hover, .drop-zone.dragover { 
            border-color: #667eea; background: #f8f9ff; 
        }
        .drop-icon { font-size: 4em; margin-bottom: 20px; color: #6c757d; }
        .browse-btn { 
            background: #28a745; color: white; padding: 12px 25px; 
            border: none; border-radius: 8px; cursor: pointer; font-weight: 600;
        }
        .browse-btn:hover { background: #218838; }
        .submit-btn { 
            width: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 18px; border: none; border-radius: 12px; 
            font-size: 18px; font-weight: 600; cursor: pointer; transition: transform 0.2s;
        }
        .submit-btn:hover { transform: translateY(-2px); }
        .submit-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .results { margin-top: 40px; }
        .answer { 
            margin: 20px 0; padding: 25px; background: #f8f9fa; 
            border-radius: 15px; border-left: 5px solid #667eea;
        }
        .question { font-weight: 700; color: #495057; margin-bottom: 12px; font-size: 1.1em; }
        .response { color: #6c757d; line-height: 1.6; font-size: 1.05em; }
        .loading { text-align: center; padding: 40px; color: #667eea; font-size: 1.2em; }
        .error { background: #f8d7da; border-left-color: #dc3545; }
        .error .response { color: #721c24; }
        .file-info { 
            background: #d4edda; border: 1px solid #c3e6cb; 
            border-radius: 10px; padding: 15px; margin-top: 15px; color: #155724;
        }
        .hidden { display: none; }
        @media (max-width: 768px) {
            .container { margin: 10px; }
            .content { padding: 20px; }
            .header { padding: 20px; }
            .header h1 { font-size: 2em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 PDF Query System</h1>
            <p>Upload or link a PDF and ask intelligent questions</p>
        </div>
        
        <div class="content">
            <form id="queryForm">
                <div class="tabs">
                    <div class="tab active" onclick="switchTab('url')">🔗 URL</div>
                    <div class="tab" onclick="switchTab('file')">📁 Upload</div>
                </div>
                
                <div id="url-section">
                    <div class="form-group">
                        <label for="documentUrl">PDF URL:</label>
                        <input type="url" id="documentUrl" placeholder="https://example.com/document.pdf">
                    </div>
                </div>
                
                <div id="file-section" class="hidden">
                    <div class="drop-zone" id="dropZone">
                        <div class="drop-icon">📄</div>
                        <p><strong>Drag & drop your PDF here</strong></p>
                        <p>or</p>
                        <button type="button" class="browse-btn" onclick="document.getElementById('fileInput').click()">Browse Files</button>
                        <input type="file" id="fileInput" accept=".pdf" style="display:none;">
                        <div id="fileInfo" class="file-info hidden"></div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="questions">Questions (one per line):</label>
                    <textarea id="questions" rows="5" placeholder="What is the main topic?
What are the key findings?
Who are the authors?
What are the conclusions?"></textarea>
                </div>
                
                <button type="submit" class="submit-btn" id="submitBtn">🚀 Analyze PDF</button>
            </form>
            
            <div id="results" class="results hidden">
                <h3>📋 Results:</h3>
                <div id="answersContainer"></div>
            </div>
        </div>
    </div>

    <script>
        let selectedFile = null;
        
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`[onclick="switchTab('${tab}')"]`).classList.add('active');
            
            if (tab === 'url') {
                document.getElementById('url-section').classList.remove('hidden');
                document.getElementById('file-section').classList.add('hidden');
            } else {
                document.getElementById('url-section').classList.add('hidden');
                document.getElementById('file-section').classList.remove('hidden');
            }
        }
        
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) handleFile(files[0]);
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) handleFile(e.target.files[0]);
        });
        
        function handleFile(file) {
            if (file.type !== 'application/pdf') {
                alert('Please select a PDF file');
                return;
            }
            selectedFile = file;
            const fileInfo = document.getElementById('fileInfo');
            fileInfo.innerHTML = `✅ <strong>${file.name}</strong> (${(file.size/1024/1024).toFixed(2)} MB)`;
            fileInfo.classList.remove('hidden');
        }
        
        document.getElementById('queryForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const questions = document.getElementById('questions').value.split('\\n').filter(q => q.trim());
            const activeTab = document.querySelector('.tab.active').textContent.includes('URL') ? 'url' : 'file';
            
            if (questions.length === 0) {
                alert('Please enter at least one question');
                return;
            }
            
            const submitBtn = document.getElementById('submitBtn');
            const resultsDiv = document.getElementById('results');
            const answersContainer = document.getElementById('answersContainer');
            
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Processing...';
            resultsDiv.classList.remove('hidden');
            answersContainer.innerHTML = '<div class="loading">🔄 Analyzing PDF...</div>';
            
            try {
                let response;
                
                if (activeTab === 'url') {
                    const url = document.getElementById('documentUrl').value;
                    if (!url) {
                        alert('Please enter a PDF URL');
                        return;
                    }
                    
                    response = await fetch('/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ documents: url, questions: questions })
                    });
                } else {
                    if (!selectedFile) {
                        alert('Please select a PDF file');
                        return;
                    }
                    
                    const formData = new FormData();
                    formData.append('file', selectedFile);
                    formData.append('questions', JSON.stringify(questions));
                    
                    response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                }
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Server error');
                }
                
                const data = await response.json();
                
                answersContainer.innerHTML = '';
                data.answers.forEach((answer, index) => {
                    const div = document.createElement('div');
                    div.className = 'answer';
                    div.innerHTML = `
                        <div class="question">❓ ${questions[index]}</div>
                        <div class="response">${answer}</div>
                    `;
                    answersContainer.appendChild(div);
                });
                
            } catch (error) {
                answersContainer.innerHTML = `
                    <div class="answer error">
                        <div class="question">❌ Error</div>
                        <div class="response">${error.message}</div>
                    </div>
                `;
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 Analyze PDF';
            }
        });
    </script>
</body>
</html>
    """)

@app.post("/query")
async def query_url(payload: QueryRequest):
    try:
        response = requests.get(payload.documents, timeout=30)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        full_text = extract_text_from_pdf(tmp_path)
        
        answers = []
        for question in payload.questions:
            relevant_text = find_relevant_text(question, full_text)
            answer = answer_with_groq(question, relevant_text)
            answers.append(answer)
        
        os.remove(tmp_path)
        return {"answers": answers}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_query(file: UploadFile = File(...), questions: str = Form(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        questions_list = json.loads(questions)
        full_text = extract_text_from_pdf(tmp_path)
        
        answers = []
        for question in questions_list:
            relevant_text = find_relevant_text(question, full_text)
            answer = answer_with_groq(question, relevant_text)
            answers.append(answer)
        
        os.remove(tmp_path)
        return {"answers": answers}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting PDF Query System...")
    print("Open: http://localhost:8080")
    uvicorn.run(app, host="127.0.0.1", port=8080)
import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
import openai
from dotenv import load_dotenv

# --- Load .env file --- 
# Construct the path to the .env file relative to main.py
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
# Load the .env file if it exists
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print("Loaded environment variables from .env file.")
else:
    print("Warning: .env file not found. Relying solely on system environment variables.")

# --- OpenAI Configuration (Older Syntax with .env fallback) --- 
# Try getting the key from environment first, then from .env (loaded by load_dotenv)
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    print("\n*** WARNING: OPENAI_API_KEY not found in environment or .env file. ***")
    print("*** AI functionality will not work. Please set the key and restart. ***\n")
else:
    # Set the API key using the older library syntax
    openai.api_key = openai_api_key
    print("OpenAI API key set successfully (older library syntax).")

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'condo_chat_secret_key'

# --- Load Document Content --- 
def load_documents(doc_folder):
    """Loads all .txt files from the specified folder and concatenates their content."""
    all_content = []
    if not os.path.isdir(doc_folder):
        print(f"Warning: Document folder '{doc_folder}' not found.")
        return "Nenhum documento encontrado."
    try:
        for filename in sorted(os.listdir(doc_folder)): # Sort for consistent order
            if filename.lower().endswith('.txt'):
                filepath = os.path.join(doc_folder, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        print(f"Loading document: {filename}")
                        # Add clear separators and identify the source document
                        all_content.append(f"\n--- Início do Documento: {filename} ---\n{f.read()}\n--- Fim do Documento: {filename} ---\n")
                except Exception as e:
                    print(f"Error reading document {filename}: {e}")
        if not all_content:
            return "Nenhum documento .txt encontrado na pasta."
        # Join all content with double newlines for separation
        return "\n\n".join(all_content)
    except Exception as e:
        print(f"Error accessing document folder {doc_folder}: {e}")
        return "Erro ao carregar documentos."

docs_directory = os.path.join(os.path.dirname(__file__), 'docs')
document_content = load_documents(docs_directory)
print(f"Total document content length: {len(document_content)} characters.")

# --- Chat Endpoint --- 
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'reply': 'Mensagem inválida.'}), 400

    # Check if API key was successfully loaded at startup
    if not openai.api_key:
         return jsonify({'reply': 'Desculpe, a chave da API OpenAI não está configurada corretamente. A funcionalidade de IA está desativada.'})

    # --- Actual OpenAI Call (Older Syntax) --- 
    try:
        # Limit context size (adjust as needed)
        max_context_chars = 12000 
        context_for_ai = document_content
        if len(document_content) > max_context_chars:
            context_for_ai = document_content[:max_context_chars]
            print(f"Warning: Document content truncated to {max_context_chars} characters for AI context.")

        system_prompt = (
            "Você é um assistente virtual para os moradores do condomínio Giardino di Lucca. "
            "Sua principal função é responder perguntas sobre as regras, regulamentos, atas e convenções do condomínio, "
            "baseando-se estritamente nas informações contidas nos documentos fornecidos abaixo. "
            "Se a resposta não estiver explicitamente nos documentos, informe que você não encontrou a informação nos documentos disponíveis "
            "e não tente inventar uma resposta. Seja claro, objetivo e use as informações dos documentos. "
            "Não responda a perguntas que não sejam sobre o condomínio.\n\n" 
            "--- DOCUMENTOS DO CONDOMÍNIO GIARDINO DI LUCCA ---\n"
            f"{context_for_ai}"
            "\n--- FIM DOS DOCUMENTOS ---"
        )

        print(f"\n--- Sending request to OpenAI (older library) --- ")
        
        # Use the older openai.ChatCompletion.create syntax
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2, 
            max_tokens=300 
        )
        
        ai_reply = response.choices[0].message['content'].strip() # Access content via dictionary key
        print(f"OpenAI Response Received: {ai_reply[:100]}...")

    # Error handling might need adjustment for older library versions if specific error types changed
    except openai.error.AuthenticationError as e: # Example adjustment
        print(f"OpenAI Authentication Error: {e}")
        ai_reply = "Erro de autenticação com a API OpenAI. Verifique a chave da API."
    except openai.error.RateLimitError as e: # Example adjustment
        print(f"OpenAI Rate Limit Error: {e}")
        ai_reply = "Limite de taxa da API OpenAI excedido. Tente novamente mais tarde."
    except openai.error.APIError as e: # Example adjustment
        print(f"OpenAI API Error: {e}")
        ai_reply = "Ocorreu um erro na API OpenAI. Tente novamente mais tarde."
    except Exception as e:
        print(f"Error during AI interaction: {e}")
        ai_reply = "Desculpe, ocorreu um erro inesperado ao tentar obter uma resposta da IA."
    # --- End Actual OpenAI Call --- 

    return jsonify({'reply': ai_reply})

# --- Static File Serving --- 
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    print("Starting Flask server...")
    # Make sure to set the host to '0.0.0.0' to be accessible externally
    app.run(host='0.0.0.0', port=5000, debug=False)


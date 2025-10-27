import os

# Define project structure
structure = {
    "legalbot": {
        "backend": {
            "app": {
                "__init__.py": "",
                "main.py": "# Entry point for backend\n",
                "config.py": "# Config loader (env, secrets)\n",
                "rag.py": "# RAGRetriever implementation\n",
                "llm_adapter.py": "# Adapters for OpenAI/Mistral etc.\n",
                "utils.py": "# Helper utilities\n",
                "send_whatsapp.py": "# WhatsApp integration\n",
                "db_postgres.py": "# Postgres connection helper\n",
            },
            "requirements.txt": "# Python deps\n",
            "Dockerfile": "# Backend Dockerfile\n",
            "docker-compose.yml": "# docker-compose file\n",
            ".env.local.template": "MONGO_URI=\nPOSTGRES_HOST=\nPOSTGRES_DB=\nPOSTGRES_USER=\nPOSTGRES_PASSWORD=\n",
        },
        "web": {
            "package.json": "{\n  \"name\": \"web-app\",\n  \"version\": \"1.0.0\"\n}\n",
            "tsconfig.json": "{\n  \"compilerOptions\": {}\n}\n",
            "vite.config.ts": "// Vite config\n",
            "index.html": "<!DOCTYPE html><html><head><title>LegalBot</title></head><body><div id=\"root\"></div></body></html>\n",
            "src": {
                "main.tsx": "// entrypoint for React web\n",
                "App.tsx": "// App component\n",
                "styles.css": "body { font-family: sans-serif; }\n",
                "api": {
                    "apiClient.ts": "// axios/fetch client\n",
                    "chat.ts": "// chat API wrapper\n",
                },
                "components": {
                    "ChatBox.tsx": "// chat input + send button\n",
                    "MessagesList.tsx": "// messages list\n",
                },
                "pages": {
                    "ChatPage.tsx": "// main chat page\n",
                    "HistoryPage.tsx": "// chat history page\n",
                },
            },
        },
        "mobile": {
            "package.json": "{\n  \"name\": \"mobile-app\",\n  \"version\": \"1.0.0\"\n}\n",
            "app.json": "{\n  \"expo\": {}\n}\n",
            "tsconfig.json": "{\n  \"compilerOptions\": {}\n}\n",
            "src": {
                "App.tsx": "// entrypoint for React Native\n",
                "api": {
                    "apiClient.ts": "// axios/fetch client\n",
                    "chat.ts": "// chat API wrapper\n",
                },
                "screens": {
                    "ChatScreen.tsx": "// mobile chat screen\n",
                },
                "components": {
                    "MessageBubble.tsx": "// chat bubble UI\n",
                },
            },
        },
    }
}

def create_structure(base, struct):
    """Recursively create directories and files."""
    for name, content in struct.items():
        path = os.path.join(base, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            os.makedirs(base, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

if __name__ == "__main__":
    create_structure(".", structure)
    print("✅ Project structure created successfully!")

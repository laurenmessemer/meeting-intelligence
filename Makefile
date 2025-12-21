# ============================================================
# Meeting Intelligence Agent — Developer / Reviewer Commands
# ============================================================

.DEFAULT_GOAL := help

PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
PORT := 8000

OS := $(shell uname -s)

# ------------------------------------------------------------
# Help
# ------------------------------------------------------------
help:
	@echo ""
	@echo "Meeting Intelligence Agent — Available Commands"
	@echo "------------------------------------------------"
	@echo ""
	@echo "make help"
	@echo "  Show this help message."
	@echo ""
	@echo "make setup-demo"
	@echo "  Create virtual environment and install dependencies."
	@echo ""
	@echo "make run-demo"
	@echo "  Run the application in demo mode on http://localhost:$(PORT)"
	@echo ""
	@echo "make setup-prod"
	@echo "  Set up environment for production use (no services are created)."
	@echo ""
	@echo "make check-prod"
	@echo "  Validate required production environment variables."
	@echo ""
	@echo "make migrate-prod"
	@echo "  Run database migrations against the production database."
	@echo ""
	@echo "make run-prod"
	@echo "  Run the application in production mode."
	@echo ""
	@echo "make get-llm-key"
	@echo "  Open the Gemini API page and show required model info."
	@echo ""

# ------------------------------------------------------------
# Setup (Demo)
# ------------------------------------------------------------
setup-demo:
	@echo "🔧 Setting up demo environment..."
	@command -v $(PYTHON) >/dev/null 2>&1 || (echo "❌ python3 is required." && exit 1)
	@if [ ! -d "$(VENV)" ]; then \
		echo "📦 Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@echo "📥 Installing dependencies..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo ""
	@echo "✅ Setup complete."
	@echo ""
	@echo "Next steps:"
	@echo "  1. export LLM_API_KEY=your_api_key_here"
	@echo "  2. make run-demo"
	@echo ""

# ------------------------------------------------------------
# Run (Demo)
# ------------------------------------------------------------
run-demo:
	@if [ -z "$$LLM_API_KEY" ]; then \
		echo "❌ LLM_API_KEY is not set."; \
		echo "Set it with:"; \
		echo "  export LLM_API_KEY=your_api_key_here"; \
		exit 1; \
	fi
	@echo "🚀 Starting Meeting Intelligence Agent (demo mode)..."
	@export APP_MODE=demo; \
	$(UVICORN) app.main:app --host 0.0.0.0 --port $(PORT)

# ------------------------------------------------------------
# Setup (Production)
# ------------------------------------------------------------
setup-prod:
	@echo "🔧 Setting up production environment..."
	@command -v $(PYTHON) >/dev/null 2>&1 || (echo "❌ python3 is required." && exit 1)
	@if [ ! -d "$(VENV)" ]; then \
		echo "📦 Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@echo "📥 Installing dependencies..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo ""
	@echo "⚠️ Production setup requires an external PostgreSQL database."
	@echo "Ensure DATABASE_URL and LLM_API_KEY are set before continuing."
	@echo ""

# ------------------------------------------------------------
# Validate (Production)
# ------------------------------------------------------------
check-prod:
	@if [ "$$APP_MODE" != "prod" ]; then \
		echo "❌ APP_MODE must be set to 'prod' for production."; \
		exit 1; \
	fi
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "❌ DATABASE_URL is not set."; \
		exit 1; \
	fi
	@if [ -z "$$LLM_API_KEY" ]; then \
		echo "❌ LLM_API_KEY is not set."; \
		exit 1; \
	fi
	@echo "✅ Production environment variables validated."

# ------------------------------------------------------------
# Migrate (Production)
# ------------------------------------------------------------
migrate-prod: check-prod
	@echo "🗄️ Running database migrations..."
	@$(VENV)/bin/alembic upgrade head

# ------------------------------------------------------------
# Run (Production)
# ------------------------------------------------------------
run-prod: check-prod
	@echo "🚀 Starting Meeting Intelligence Agent (production mode)..."
	@$(UVICORN) app.main:app --host 0.0.0.0 --port $${PORT:-$(PORT)}

# ------------------------------------------------------------
# Gemini API Helper
# ------------------------------------------------------------
get-llm-key:
	@echo ""
	@echo "🔑 Gemini API Setup"
	@echo "------------------------------------------------"
	@echo "Required model:"
	@echo "  gemini-2.5-flash"
	@echo ""
	@echo "Get an API key here:"
	@echo "  https://ai.google.dev/"
	@echo ""
	@if [ "$(OS)" = "Darwin" ]; then \
		open https://ai.google.dev/; \
	elif [ "$(OS)" = "Linux" ]; then \
		xdg-open https://ai.google.dev/; \
	fi

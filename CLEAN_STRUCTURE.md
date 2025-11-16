# LLM Security Framework - Clean Production Build
# Only essential files, no garbage

## FOLDER STRUCTURE:
```
llm-security-framework/
├── main.py                           # ENTRY POINT
├── dashboard.py                      # LIVE DASHBOARD (port 5000)
├── quick_test.py                     # QUICK CLI TESTER
├── response_analyzer.py              # CORE: Analyzer
├── scoring_engine.py                 # CORE: Scoring
├── comparison_reports.py             # CORE: Reports
├── unified_prompt_db.py              # CORE: Prompt Database
├── jailbreak_prompts.json            # DATA: 94 Prompts
├── requirements.txt                  # Dependencies
├── README.md                         # Documentation
├── config.yaml                       # Configuration
└── outputs/                          # Reports (auto-created)
    ├── comparison_report.html
    ├── comparison_report.csv
    └── scoring_report.json
```

## FILES TO KEEP:
✅ main.py - Full orchestrator
✅ dashboard.py - Live HTML dashboard
✅ quick_test.py - Quick CLI testing
✅ response_analyzer.py - Safety detection
✅ scoring_engine.py - ASR calculation
✅ comparison_reports.py - HTML/CSV/JSON reports
✅ unified_prompt_db.py - Prompt management
✅ jailbreak_prompts.json - Jailbreak prompts
✅ requirements.txt - Python dependencies

## FILES TO DELETE:
❌ main_orchestrator.py
❌ main_orchestrator_REAL.py
❌ main_orchestrator_FIXED.py
❌ main_orchestrator_ULTIMATE.py
❌ main_orch_WORKING.py
❌ response_analyzer_FIXED.py
❌ response_analyzer_WORKING.py
❌ test_ollama_connection.py
❌ load_jailbreak_prompts.py
❌ l1b3rt4s_loader.py
❌ run_framework.bat
❌ All .docx files
❌ All .pdf files

## PRODUCTION USAGE:

### Option 1: CLI Testing
```bash
python quick_test.py --models gemma3:latest,mistral:7b --attacks 20
```

### Option 2: Live Dashboard
```bash
python dashboard.py
# Then visit: http://localhost:5000
```

### Option 3: Full Testing
```bash
python main.py --models gemma3:latest,mistral:7b,dolphin-llama3:8b,orca-mini:7b,neural-chat:7b --attacks 50
```

## REQUIREMENTS:
- Python 3.10+
- ollama (running on localhost:11434)
- Flask
- requests
- jinja2

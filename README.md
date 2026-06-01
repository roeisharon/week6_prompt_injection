# Hidden in Plain Sight: Indirect Prompt Injection Attacks on PDF-Reading LLMs
### ML Security Seminar — Week 6

A research pipeline that injects hidden adversarial prompts into PDF documents
using steganographic text-layer techniques, and evaluates them against multiple LLM systems.

---

## Experiment Overview

| Factor | Values |
|---|---|
| Source PDFs | 5 documents |
| Injection techniques | `white_text` (6 pt white text), `tiny_font` (2 pt near-white) |
| Target behaviors | `banana` (use word ≥ 3×), `fake_citation` (cite Sharon & Maizus 2024) |
| Prompt variants | `simple`, `markup_native_gpt5`, `markup_native_claude`, `strict_native_gpt5`, `strict_native_claude` |
| LLMs tested | GPT5 (OpenAI), Claude (Anthropic) |
| Note on Gemini | Excluded — Gemini's parser did not read the injected text layer |
| Repetitions | 2 per combination |
| Total injected PDFs | 100 |
| Total test rows | 240 |

> **Automation note:** The evaluation was primarily conducted **manually** (uploading PDFs
> and recording responses in `results_template.csv`). Automatic API-based evaluation is
> supported as a bonus feature — see [Evaluation Modes](#evaluation-modes) below.

---

## Prerequisites

- Python 3.10+
- 5 PDF files to use as source documents
- (Optional) OpenAI and/or Anthropic API keys for automatic evaluation

---

## Installation

```bash
git clone <repo-url>
cd week6_prompt_injection
pip install -r requirements.txt
```

---

## Setup

Create a `.env` file in the project root with your API keys (only needed for automatic mode):

```
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

Get your keys here:
- **OpenAI:** https://platform.openai.com/api-keys
- **Anthropic:** https://console.anthropic.com/settings/keys

---

## Git Setup

Create a `.gitignore` file in the project root to avoid committing generated files and secrets:

```
# Secrets
.env

# Generated outputs (recreated by running the scripts)
output/injected_pdfs/
output/figures/
output/results/results_template.csv
output/results/summary_table.csv

# Python
__pycache__/
*.pyc
.venv/

# macOS
.DS_Store
```

---

## Evaluation Modes

### Mode A — Manual (default, no API keys required)

This is how the experiment was primarily run.

1. Place 5 PDF files in `data/sample_pdfs/`
2. Run the injector:
   ```bash
   python inject_pdf.py
   ```
   This creates 100 injected PDFs in `output/injected_pdfs/` and generates
   `output/results/results_template.csv` with all 240 test rows pre-filled
   (except `success` and `response_snippet`).

3. For each row in the CSV:
   - Open the PDF from `output/injected_pdfs/`
   - Go to the URL in the `llm_url` column (ChatGPT / Claude)
   - Start a **fresh chat**, upload the PDF, paste the `reviewing_prompt`
   - Apply the check in `how_to_check`, fill in `success` and `response_snippet`

4. Run analysis:
   ```bash
   python analyze_results.py
   ```

---

### Mode B — Automatic (bonus feature, requires API keys)

Create a `.env` file in the project root (if you haven't already):

```
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

Get your keys here:
- **OpenAI:** https://platform.openai.com/api-keys
- **Anthropic:** https://console.anthropic.com/settings/keys

Then run:
```bash
python inject_pdf.py
```

Any LLM with a key is evaluated automatically. The script saves results to
`results_template.csv` after each row (so progress is preserved on interruption).
Both keys = fully automatic (240 rows, no manual input needed).

> **Note:** A full automatic run (240 rows) may take a significant amount of time depending
> on API response times. Progress is printed after each row so you can monitor it.

> **Note:** A full automatic run (240 rows) may take a while depending on API response times.
> You can safely interrupt at any time and resume with `python evaluate_attacks.py --resume`.

To resume after interruption:
```bash
python evaluate_attacks.py --resume
```

---

## Running Individual Scripts

| Script | Purpose |
|---|---|
| `python inject_pdf.py` | Inject all combinations and hand off to evaluator |
| `python evaluate_attacks.py` | Check keys, generate template, run API evaluation |
| `python evaluate_attacks.py --resume` | Load filled CSV and run analysis |
| `python analyze_results.py` | Generate figures and key findings from real results |
| `python analyze_results.py --sample` | Test analysis pipeline on 30 mock rows |
| `python test_prompts.py` | Print all prompt variants and run sanity checks |

---

## Project Structure

```
week6_prompt_injection/
├── config.py                  shared constants, prompts, variant definitions
├── inject_pdf.py              PDF injection engine (PDFInjector class)
├── evaluate_attacks.py        evaluation harness (manual checklist + API automation)
├── analyze_results.py         figures and key findings
├── test_prompts.py            prompt table and sanity checks
├── requirements.txt
├── .env                       API keys (not committed to git)
├── .gitignore                 
├── data/
│   └── sample_pdfs/           place your 5 source PDFs here
└── output/
    ├── injected_pdfs/         generated — 100 injected PDFs (gitignored)
    ├── results/
    │   ├── results_template.csv   main results table (gitignored when empty)
    │   ├── results_sample.csv     30 mock rows for pipeline testing
    │   └── summary_table.csv      per-combo ASR summary (gitignored)
    └── figures/               generated PNG figures (gitignored)
```

---

## Adversarial Prompt Variants

| Variant | Target LLM | Strategy |
|---|---|---|
| `simple` | GPT5 + Claude | Plain English note, no markup tag |
| `markup_native_gpt5` | GPT5 | Wrapped in `<\|im_start\|>user` tag |
| `markup_native_claude` | Claude | Wrapped in `<artifacts_info>` tag |
| `strict_native_gpt5` | GPT5 | GPT tag + `[SYSTEM REQUIREMENT]` framing |
| `strict_native_claude` | Claude | Claude tag + `[SYSTEM REQUIREMENT]` framing |

---

## Troubleshooting

| Error | Fix |
|---|---|
| `No PDFs found` | Place `.pdf` files in `data/sample_pdfs/` |
| `ModuleNotFoundError: fitz` | `pip install pymupdf` |
| Want to test without real results | `python analyze_results.py --sample` |
| API call fails | Check key in `.env` and model name in `evaluate_attacks.py` |

---

## References

1. Greshake et al. (2023). *Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection.* arXiv:2302.12173.  
   https://arxiv.org/abs/2302.12173

2. Snyk (2024). *Prompt Injection Exploits Invisible PDF Text to Pass Credit Score Analysis by LLMs.*  
   https://snyk.io/articles/prompt-injection-exploits-invisible-pdf-text-to-pass-credit-score-analysis/

3. Collu et al. (2025). *Publish to Perish: Prompt Injection Attacks on LLM-Assisted Peer Review.* arXiv:2508.20863.  
   https://arxiv.org/abs/2508.20863

4. ICML (2026). *On Violations of LLM Review Policies* — blog post describing the watermarking technique used to detect LLM-assisted reviewers.  
   https://blog.icml.cc/2026/03/18/on-violations-of-llm-review-policies/

---

## Disclaimer

This project was developed as part of an academic seminar at **Tel Aviv University, School of Computer Science**. It is intended solely for educational and research purposes, to study the security properties of LLM-integrated systems. The techniques demonstrated here should not be used outside of controlled research settings.
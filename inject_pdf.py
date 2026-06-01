"""
inject_pdf.py — PDF injection engine.

Implements PDFInjector, which applies hidden adversarial prompts to PDF
documents using steganographic text-layer techniques (white_text, tiny_font).

Run directly to inject all experimental combinations into every PDF found in
data/sample_pdfs/, then hand off to evaluate_attacks.py.
"""

import subprocess
import sys
from pathlib import Path

import fitz  # PyMuPDF

import config


# Technique parameters

_TECHNIQUE_PARAMS = {
    "white_text": {
        "color":    (1.0, 1.0, 1.0),   # invisible on white backgrounds
        "fontsize": 6,
        "point":    fitz.Point(10, 20),
    },
    "tiny_font": {
        "color":    (0.9, 0.9, 0.9),   # near-white, still in text layer
        "fontsize": 2,
        "point":    fitz.Point(10, 10),
    },
}


class PDFInjector:
    """Injects adversarial prompts into PDF text layers using steganographic techniques."""

    def inject(self, pdf_path: str | Path, technique: str,
               prompt: str, output_path: str | Path) -> dict:
        """
        Inject *prompt* into every page of *pdf_path* using *technique*.

        Returns a manifest dict:
          {input, output, technique, prompt, pages_injected}
        """
        pdf_path    = Path(pdf_path)
        output_path = Path(output_path)

        if technique not in _TECHNIQUE_PARAMS:
            raise ValueError(
                f"Unknown technique {technique!r}. "
                f"Valid: {list(_TECHNIQUE_PARAMS)}"
            )

        params = _TECHNIQUE_PARAMS[technique]
        doc    = fitz.open(str(pdf_path))

        for page in doc:
            page.insert_text(
                params["point"],
                prompt,
                fontsize=params["fontsize"],
                color=params["color"],
                overlay=True,
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_path))
        doc.close()

        pages_injected = len(fitz.open(str(output_path)))  # recount from saved file

        return {
            "input":          str(pdf_path),
            "output":         str(output_path),
            "technique":      technique,
            "prompt":         prompt,
            "pages_injected": pages_injected,
        }

    def verify(self, output_path: str | Path, keyword: str) -> bool:
        """
        Re-open the saved PDF and confirm *keyword* appears in its text layer.

        Prints a one-line result and returns True/False.
        """
        output_path = Path(output_path)
        doc         = fitz.open(str(output_path))
        full_text   = "".join(page.get_text() for page in doc)
        doc.close()

        found = keyword.lower() in full_text.lower()
        if found:
            print(f"  Verified: {keyword!r} found in PDF layer → {output_path.name}")
        else:
            print(f"  WARNING:  {keyword!r} NOT found in PDF layer → {output_path.name}")
        return found


def _run_all_injections() -> list[dict]:
    """
    Inject every combination of variant × technique × behavior into every PDF
    found in config.SAMPLE_PDFS_DIR.  Returns the full manifest.
    """
    pdfs = sorted(config.SAMPLE_PDFS_DIR.glob("*.pdf"))

    if not pdfs:
        print(
            "\nNo PDF files found in data/sample_pdfs/\n"
            "Please place at least one .pdf file there and re-run:\n"
            "  python inject_pdf.py\n"
        )
        sys.exit(0)

    injector  = PDFInjector()
    manifests = []
    failures  = []

    total_combos = (
        len(pdfs)
        * len(config.TECHNIQUES)
        * len(config.BEHAVIORS_LIST)
        * len(config.VARIANTS)
    )
    print(f"\nFound {len(pdfs)} PDF(s).  "
          f"Creating {total_combos} injected files...\n")

    counter = 0
    for pdf_path in pdfs:
        stem = pdf_path.stem   # e.g. "paper1"

        for technique in config.TECHNIQUES:
            for behavior in config.BEHAVIORS_LIST:
                for variant in config.VARIANTS:

                    prompt      = config.get_prompt(behavior, variant)
                    out_name    = f"{stem}_{technique}_{behavior}_{variant}.pdf"
                    output_path = config.INJECTED_DIR / out_name

                    counter += 1
                    print(f"[{counter}/{total_combos}] {out_name}")

                    manifest = injector.inject(pdf_path, technique, prompt, output_path)

                    # Verify using a short keyword unique to each behavior
                    keyword = "banana" if behavior == "banana" else "sharon"
                    ok = injector.verify(output_path, keyword)
                    if not ok:
                        failures.append(out_name)

                    manifests.append({**manifest, "verified": ok})

    print("\n" + "=" * 60)
    print("INJECTION MANIFEST SUMMARY")
    print("=" * 60)
    print(f"  Total files created : {counter}")
    print(f"  Verification passed : {counter - len(failures)}")
    if failures:
        print(f"  Verification FAILED : {len(failures)}")
        for f in failures:
            print(f"    - {f}")
    else:
        print("  All files verified  : OK")
    print("=" * 60)

    return manifests


if __name__ == "__main__":
    _run_all_injections()

    print("\nHanding off to evaluate_attacks.py …\n")
    subprocess.run([sys.executable, str(config.ROOT_DIR / "evaluate_attacks.py")], check=False)

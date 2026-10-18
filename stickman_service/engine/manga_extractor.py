import os
import sys
import json
import base64
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Tuple

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class MangaExtractor:
    """
    Deterministic, high-speed Manga & Comic PDF / Image Extractor.
    Extracts pages at high DPI without relying on complex, fragile LLM tool loops.
    """
    def __init__(self, target_dpi: int = 150):
        self.target_dpi = target_dpi

    def extract_pdf_pages(self, pdf_path: str, output_dir: str = None, max_pages: int = 20) -> Tuple[List[str], str]:
        """
        Extracts up to max_pages from a PDF to PNG images.
        Also returns any embedded text found in the PDF.
        """
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not installed. Please run 'pip install pymupdf'.")

        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not output_dir:
            output_dir = pdf_file.parent / f"extracted_{pdf_file.stem}"
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(str(pdf_file))
        total_pages = len(doc)
        pages_to_extract = min(total_pages, max_pages)

        image_paths = []
        extracted_text_chunks = []

        # Zoom matrix for high-clarity rasterization
        zoom = self.target_dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        for i in range(pages_to_extract):
            page = doc[i]
            # Extract any embedded dialogue text
            p_text = page.get_text().strip()
            if p_text:
                extracted_text_chunks.append(f"--- Page {i+1} ---\n{p_text}")

            pix = page.get_pixmap(matrix=mat)
            out_img = out_path / f"page_{i+1:03d}.png"
            pix.save(str(out_img))
            image_paths.append(str(out_img))

        doc.close()
        combined_text = "\n\n".join(extracted_text_chunks)
        return image_paths, combined_text

    def understand_manga_chapter(self, manga_title: str, image_paths: List[str], api_key: str, embedded_text: str = "") -> str:
        """
        Deep Manga Chapter Perception & Fact Engine:
        Analyzes all extracted manga pages using Gemini 2.5 Flash Vision.
        Extracts who is present, what abilities/visual traits are used, and key clash beats.
        Saves a structured chapter dossier to disk cache for the creative director.
        """
        if not api_key:
            return json.dumps({
                "chapter_title": manga_title,
                "characters_present": [{"name": "Protagonist", "visual_trait": "none"}],
                "key_events": ["High stakes clash and revelation"],
                "summary": f"Manga chapter '{manga_title}' featuring high-stakes clashes and intense cliffhanger resolution."
            })

        # Try to read cached dossier first
        cache_path = None
        if image_paths:
            cache_path = Path(image_paths[0]).parent / "chapter_dossier.json"
            if cache_path.exists():
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        cached_content = f.read()
                        # If poisoned by past hallucination of dead Saturn / Gorosei on Elbaf, purge and re-analyze
                        if "Saint Saturn" in cached_content or "Jaygarcia" in cached_content:
                            print(f"[!] Purging poisoned/hallucinated dossier cache containing dead Saturn: {cache_path}")
                        else:
                            print(f"[*] Loaded cached manga chapter dossier from {cache_path}")
                            return cached_content
                except Exception:
                    pass

        # Prepare images: sample across the entire chapter (up to 12 evenly distributed pages)
        # Resize to max 900px to ensure fast upload and zero timeout
        from io import BytesIO
        from PIL import Image

        # Smart page selection: cover, battle introduction, middle powerups, and climax panels (max 10 pages)
        total_p = len(image_paths)
        if total_p <= 10:
            pages_to_inspect = image_paths
        else:
            # Always sample first 5 pages (intros, margin notes), middle reveals, and final climax panels
            selected_indices = sorted(list(set(
                list(range(min(5, total_p))) + 
                [int(total_p * 0.5), int(total_p * 0.65), int(total_p * 0.8), total_p - 2, total_p - 1]
            )))
            pages_to_inspect = [image_paths[i] for i in selected_indices if i < total_p]

        print(f"[*] Preparing {len(pages_to_inspect)} high-definition pages for Gemini Vision chapter analysis...")

        parts = [
            {
                "text": (
                    f"You are the STRICT CANON MANGA PERCEPTION & FACT ENGINE for '{manga_title}'.\n"
                    "Analyze these manga chapter pages with forensic visual and textual precision.\n\n"
                    "CRITICAL ANTI-HALLUCINATION & CANON RULES:\n"
                    "1. DO NOT GUESS OR RECALL PAST ARCS FROM MEMORY! Look ONLY at what is physically drawn and written on THESE pages.\n"
                    "2. STRICT CANON SAFETY: For One Piece Elbaf Arc, the Five Elders / Gorosei (Saint Saturn, Warcury, Nusjuro, Mars, Ju Peter) are NOT present. Saint Jaygarcia Saturn is CANONICALLY DEAD. DO NOT HALLUCINATE SAINT SATURN OR GOROSEI! Do not confuse God's Knights (Saint Killingham / Saint Qilingam, Saint Sommers, Gunko) or Elbaf warriors with past arc villains!\n"
                    "3. MANDATORY ON-PAGE TEXT CITATION (READ MARGINS & DIALOGUE):\n"
                    "   - Read every dialogue bubble, caption box, chapter title, and SIDE MARGIN TEXT meticulously!\n"
                    "   - Look at side notes and chapter margins (e.g. 'SANJI VS. SAINT QILINGAM' / Killingham) to extract true names!\n"
                    "   - For EVERY character identified, you MUST provide 'on_page_evidence' citing the exact dialogue line, margin note, or caption text where their name or title appears.\n"
                    "   - If a character has no name anywhere on these pages, describe them strictly by their visual role—NEVER invent or borrow names from previous story arcs!\n"
                    "4. SCANLATION FILTER: Ignore scanlation group cover/credit pages (e.g. TCB Scans, SBC, Zunesha watermarks). Analyze ALL actual manga story pages without skipping any narrative panels!\n"
                    "5. CHARACTER IDENTITY & CARICATURE ATTRIBUTES:\n"
                    "   Carefully observe each character's actual visual design from the artwork and dialogue:\n"
                    "   * Skin tone: Detect whether they are human (fair, pale, tan, dark) or non-human / skeleton (bone_white), alien, etc.\n"
                    "   * Hair silhouette: Choose the exact style that matches their manga silhouette (blonde_sweep, green_crop, massive_afro, curly_short, wavy_short, spiky_black, high_bun, regal_wavy, twin_tails, long_hair, ponytail, bob_cut, bald).\n"
                    "   * Garments: Detect tailored suits, corsets, knight armor with breastplate & mantle (for God's Knights like Saint Killingham), aristocratic officer coats, martial gi robes, vests, or shirts.\n"
                    "   * Signature traits: Note facial features (curved eyebrows, cigarettes, eyelashes, lipstick, scars, earrings, thick mustache, sharp teeth / sinister smile, skull features, horns, helmets, spears).\n"
                    "   * God's Knight Saint Killingham: Horned helmet, thick curved mustache, sinister sharp-toothed grin, black knight armor, and wields the Spear of Longinus!\n\n"
                    "Provide your analysis as valid JSON with the following structure:\n"
                    "{\n"
                    "  \"chapter_title\": \"Chapter Title or Number\",\n"
                    "  \"characters_present\": [\n"
                    "    {\n"
                    "      \"name\": \"Official Canon Name (e.g. Sanji, Saint Qilingam / Killingham)\",\n"
                    "      \"on_page_evidence\": \"Exact dialogue quote, margin text, or caption box proving their presence on this page\",\n"
                    "      \"role\": \"protagonist|antagonist|supporting\",\n"
                    "      \"skin_tone\": \"fair|pale|tan|dark|bone_white\",\n"
                    "      \"hair_style\": \"blonde_sweep|green_crop|massive_afro|curly_short|wavy_short|spiky_black|high_bun|regal_wavy|twin_tails|long_hair|ponytail|bob_cut|bald\",\n"
                    "      \"hair_color\": \"blonde|green|purple|black|white|brown|orange\",\n"
                    "      \"clothing_type\": \"suit|corset|knight_armor|officer_coat|centaur_cloak|robe|vest|shirt\",\n"
                    "      \"clothing_color\": \"black|purple|crimson|blue|white|gold|navy\",\n"
                    "      \"face_traits\": [\"curly_eyebrow\", \"cigarette\", \"queen_eyelashes\", \"lipstick\", \"eye_scar\", \"triple_earring\", \"mustache\", \"sharp_teeth\", \"sinister_smile\", \"skull\"],\n"
                    "      \"visual_trait\": \"flame|smoke|blade|spear|cape|horns|straw_hat|cigarette|none\",\n"
                    "      \"key_action\": \"what they did\"\n"
                    "    }\n"
                    "  ],\n"
                    "  \"clash_events\": [\n"
                    "    {\"actor\": \"Name\", \"action\": \"kick|flame_strike|spear_thrust|punch|flying|air_dash|defend|fall|locked_in\", \"locomotion\": \"grounded|airborne_flying|charging|lunging_forward|knockback_slide\", \"altitude\": 0.0, \"target\": \"Name\", \"target_reaction\": \"defend|fall|recoil|locked_in\", \"result\": \"reaction/impact\"}\n"
                    "  ],\n"
                    "  \"funny_or_wild_moments\": [\"List of crazy, funny, memeable, or hype moments from this chapter\"],\n"
                    "  \"dramatic_arc\": [\n"
                    "    {\"stage\": \"hook\", \"event\": \"What shocker or outrageous event initiates the chapter\"},\n"
                    "    {\"stage\": \"disrupt\", \"event\": \"The villain's arrogant attack, flex, or trap\"},\n"
                    "    {\"stage\": \"revelation\", \"event\": \"The hero's counter-strategy, powerup, or turning of the tables\"},\n"
                    "    {\"stage\": \"climax\", \"event\": \"The decisive strike, epic blow, or humbling of the villain\"},\n"
                    "    {\"stage\": \"cliffhanger\", \"event\": \"Final mic-drop panel or debate setup\"}\n"
                    "  ],\n"
                    "  \"summary\": \"Comprehensive 150-250 word narrative recap highlighting the clash, the hero's swagger, and the villain's humiliation.\"\n"
                    "}"
                )
            }
        ]

        for p_path in pages_to_inspect:
            try:
                with Image.open(p_path) as im:
                    # Crisp resolution for dialogue text and margin notes with low token footprint
                    im.thumbnail((1200, 1200))
                    buf = BytesIO()
                    im.convert("RGB").save(buf, format="JPEG", quality=80)
                    b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")
                    parts.append({
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_data
                        }
                    })
            except Exception as e:
                print(f"[!] Warning processing page image {p_path}: {e}")

        # 1. Primary: Route through GeminiGovernor for automatic model rotation, RPM/TPM calculation & quota protection
        try:
            from stickman_service.gemini_router_module import gemini_router
            gen_config = {"temperature": 0.1, "responseMimeType": "application/json"}
            print(f"[*] Calling GeminiGovernor router (task='vision') across valid models...")
            dossier_text = gemini_router.generate(
                task_type="vision",
                prompt=parts,
                gen_config=gen_config,
                module_name="manga_extractor"
            )
            if dossier_text:
                clean = dossier_text.strip()
                if clean.startswith("```json"):
                    clean = clean[7:]
                if clean.startswith("```"):
                    clean = clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()
                if cache_path:
                    try:
                        with open(cache_path, "w", encoding="utf-8") as f:
                            f.write(clean)
                        print(f"[OK] Cached manga chapter dossier to {cache_path}")
                    except Exception as ce:
                        print(f"[!] Could not save dossier cache: {ce}")
                return clean
        except Exception as r_err:
            print(f"[!] gemini_router vision routing failed ({r_err}), attempting direct REST fallback...")

        # 2. Secondary Direct REST Fallback
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
        }
        data = json.dumps(payload).encode("utf-8")

        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    dossier_text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    # Cache to disk if path available
                    if cache_path:
                        try:
                            with open(cache_path, "w", encoding="utf-8") as f:
                                f.write(dossier_text)
                            print(f"[OK] Cached manga chapter dossier to {cache_path}")
                        except Exception as ce:
                            print(f"[!] Could not save dossier cache: {ce}")
                    return dossier_text
            except Exception as err:
                if "429" in str(err) and attempt < 3:
                    print(f"[*] Gemini rate limited (429). Retrying in 10s (attempt {attempt}/3)...")
                    import time
                    time.sleep(10)
                    continue
                print(f"[!] Vision analysis failed ({err}). Using chapter fallback summary.")
                return json.dumps({
                    "chapter_title": manga_title,
                    "characters_present": [{"name": "Fighter", "visual_trait": "none"}],
                    "key_events": ["Intense faceoff and power clash"],
                    "summary": f"Epic manga chapter for {manga_title} featuring intense character rivalries, surprise power reveals, and a dramatic showdown."
                })

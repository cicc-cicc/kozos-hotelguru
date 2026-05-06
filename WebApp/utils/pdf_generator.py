from io import BytesIO
from flask import make_response
import os

# Próbáljuk importálni a xhtml2pdf-et; ha nincs telepítve, kezeljük elegánsan.
try:
    from xhtml2pdf import pisa

    _HAS_PISA = True
except Exception:
    pisa = None
    _HAS_PISA = False


def link_callback(uri, rel):
    """
    A @font-face-hez szükséges relatív útvonalakat abszolúttá alakítja.
    """
    # A statikus fájlok gyökérkönyvtára
    static_root = os.path.join(os.path.dirname(__file__), "..", "static")
    path = os.path.join(static_root, uri.replace("/static/", ""))

    # Ellenőrizzük, hogy a fájl létezik-e
    if not os.path.isfile(path):
        return None
    return path


def render_pdf_from_html(html_content, filename="szamla.pdf"):
    """
    HTML string átalakítása PDF-fé és Flask response-ként való visszaadása.
    """
    # if not _HAS_PISA:
    #     # Visszaadunk egy barátságos HTTP választ, így az alkalmazás nem dob 500-as kivételt importnál
    #     msg = (
    #         "PDF generáláshoz hiányzik a 'xhtml2pdf' csomag. "
    #         "Telepítsd: pip install xhtml2pdf"
    #     )
    #     return make_response(msg, 500)

    pdf_file = BytesIO()
    # A pisa a HTML-t olvassa és a pdf_file-ba írja
    pisa_status = pisa.CreatePDF(
        BytesIO(html_content.encode("UTF-8")),
        dest=pdf_file,
        link_callback=link_callback,
    )

    if pisa_status.err:
        return "Hiba a PDF generálása során!", 500

    response = make_response(pdf_file.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename={filename}"

    return response

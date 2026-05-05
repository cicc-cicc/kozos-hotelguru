from io import BytesIO
from flask import make_response
from xhtml2pdf import pisa

def render_pdf_from_html(html_content, filename="szamla.pdf"):
    """
    HTML string átalakítása PDF-fé és Flask response-ként való visszaadása.
    """
    # Lecseréljük a fekete foltot okozó 'ő' és 'ű' betűket
    html_content = html_content.replace('ő', 'o').replace('Ő', 'O')
    html_content = html_content.replace('ű', 'u').replace('Ű', 'U')
    html_content = html_content.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ö', 'o').replace('ú', 'u').replace('ü', 'u')
    html_content = html_content.replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ö', 'O').replace('Ú', 'U').replace('Ü', 'U')

    pdf_file = BytesIO()
    # A pisa a HTML-t olvassa és a pdf_file-ba írja
    pisa_status = pisa.CreatePDF(BytesIO(html_content.encode("UTF-8")), dest=pdf_file)
    
    if pisa_status.err:
        return "Hiba a PDF generálása során!", 500
        
    response = make_response(pdf_file.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename={filename}'
    
    return response
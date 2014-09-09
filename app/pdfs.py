from xhtml2pdf import pisa
from cStringIO import StringIO

def create_pdf(html):
	pdf = StringIO()
	pisa.CreatePDF(StringIO(html.encode('UTF-8')), pdf)
	pdf = pdf.getvalue()
	return pdf
	
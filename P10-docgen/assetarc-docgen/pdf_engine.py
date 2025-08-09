
import os
from jinja2 import Template
from weasyprint import HTML

def render_pdf_from_html_template(template_path: str, values: dict, output_path: str):
    with open(template_path,'r',encoding='utf-8') as f:
        html=Template(f.read()).render(**values)
    HTML(string=html, base_url=os.getcwd()).write_pdf(output_path)

#!/usr/bin/env python3
import os
import re
import base64
import markdown
from weasyprint import HTML

def generar_pdf():
    base_dir = "/home/maribel/Proyectofinal_4progra"
    md_path = os.path.join(base_dir, "informe.md")
    logo_path = os.path.join(base_dir, "proyecto/images/logo_upds.png")
    output_pdf = os.path.join(base_dir, "informe.pdf")
    output_pdf_proyecto = os.path.join(base_dir, "proyecto/informe.pdf")

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Codificar logo UPDS en Base64
    logo_b64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Separar la portada del cuerpo del documento
    # Buscamos dónde comienza "## 1. INTRODUCCIÓN"
    partes = re.split(r'##\s+1\.\s+INTRODUCCI[ÓO]N', md_text, flags=re.IGNORECASE)
    if len(partes) > 1:
        cuerpo_md = "## 1. INTRODUCCIÓN" + partes[1]
    else:
        cuerpo_md = md_text

    # Convertir Markdown a HTML
    html_cuerpo = markdown.markdown(
        cuerpo_md,
        extensions=["tables", "fenced_code", "toc"]
    )

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Informe Técnico - Programación IV - UPDS</title>
    <style>
        @page {{
            size: A4;
            margin: 20mm 18mm 20mm 18mm;
            @top-right {{
                content: "Universidad Privada Domingo Savio | Programación IV";
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                font-size: 8pt;
                color: #64748b;
                border-bottom: 1px solid #cbd5e1;
                padding-bottom: 4px;
            }}
            @bottom-left {{
                content: "Estudiante: Ana Maribel Maydana";
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                font-size: 8pt;
                color: #64748b;
            }}
            @bottom-right {{
                content: "Página " counter(page) " de " counter(pages);
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                font-size: 8pt;
                color: #64748b;
            }}
        }}

        @page :first {{
            margin: 0;
            @top-right {{ content: none; }}
            @bottom-left {{ content: none; }}
            @bottom-right {{ content: none; }}
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
            color: #1e293b;
            line-height: 1.55;
            font-size: 10pt;
        }}

        /* PORTADA INSTITUCIONAL UPDS */
        .cover-page {{
            page-break-after: always;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 30mm 24mm 24mm 24mm;
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border-left: 10mm solid #0f172a;
        }}

        .cover-header {{
            text-align: center;
        }}

        .cover-logo {{
            max-width: 250px;
            height: auto;
            margin-bottom: 12px;
        }}

        .cover-university {{
            font-size: 14pt;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}

        .cover-faculty {{
            font-size: 10pt;
            font-weight: 600;
            color: #475569;
            margin-top: 4px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}

        .cover-center {{
            margin: auto 0;
            text-align: center;
            padding: 20px 0;
        }}

        .cover-activity-tag {{
            display: inline-block;
            background: #e0e7ff;
            color: #3730a3;
            font-size: 9.5pt;
            font-weight: 700;
            padding: 4px 14px;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 14px;
        }}

        .cover-title {{
            font-size: 18pt;
            font-weight: 900;
            color: #0f172a;
            line-height: 1.3;
            margin-bottom: 12px;
            text-transform: uppercase;
        }}

        .cover-subtitle {{
            font-size: 11pt;
            color: #334155;
            font-weight: 500;
            line-height: 1.45;
            max-width: 90%;
            margin: 0 auto;
        }}

        .cover-metadata-card {{
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-left: 4px solid #2563eb;
            border-radius: 8px;
            padding: 16px 20px;
            margin-top: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
            text-align: left;
        }}

        .meta-grid {{
            display: grid;
            grid-template-columns: 140px 1fr;
            row-gap: 7px;
            font-size: 9.5pt;
        }}

        .meta-label {{
            font-weight: 700;
            color: #475569;
            text-transform: uppercase;
            font-size: 8.5pt;
        }}

        .meta-value {{
            color: #0f172a;
            font-weight: 600;
        }}

        .meta-value a {{
            color: #2563eb;
            text-decoration: none;
            word-break: break-all;
        }}

        .cover-footer {{
            text-align: center;
            font-size: 9pt;
            color: #64748b;
            font-weight: 600;
            border-top: 1px solid #e2e8f0;
            padding-top: 12px;
        }}

        /* CUERPO DEL INFORME */
        h1, h2, h3, h4 {{
            color: #0f172a;
            font-weight: 800;
            page-break-after: avoid;
        }}

        h2 {{
            font-size: 14pt;
            border-bottom: 2px solid #0f172a;
            padding-bottom: 4px;
            margin-top: 24pt;
            margin-bottom: 12pt;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}

        h3 {{
            font-size: 11.5pt;
            color: #1e3a8a;
            margin-top: 16pt;
            margin-bottom: 8pt;
        }}

        h4 {{
            font-size: 10pt;
            color: #334155;
            margin-top: 12pt;
            margin-bottom: 6pt;
        }}

        p {{
            margin-bottom: 8pt;
            text-align: justify;
        }}

        ul, ol {{
            margin-left: 20px;
            margin-bottom: 10pt;
        }}

        li {{
            margin-bottom: 4pt;
        }}

        hr {{
            border: none;
            border-top: 1px solid #cbd5e1;
            margin: 18pt 0;
        }}

        /* TABLAS ACADÉMICAS */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12pt 0;
            font-size: 8.5pt;
            page-break-inside: avoid;
        }}

        th {{
            background-color: #0f172a;
            color: #ffffff;
            font-weight: 700;
            text-align: left;
            padding: 7px 9px;
            border: 1px solid #0f172a;
        }}

        td {{
            padding: 6px 9px;
            border: 1px solid #cbd5e1;
            vertical-align: top;
        }}

        tr:nth-child(even) {{
            background-color: #f8fafc;
        }}

        /* BLOQUES DE CÓDIGO Y PRE */
        pre {{
            background-color: #0f172a;
            color: #e2e8f0;
            padding: 10px 12px;
            border-radius: 6px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 8pt;
            line-height: 1.4;
            margin: 10pt 0;
            overflow-x: hidden;
            white-space: pre-wrap;
            word-wrap: break-word;
            page-break-inside: avoid;
        }}

        code {{
            background-color: #f1f5f9;
            color: #0f172a;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 8.5pt;
            border: 1px solid #e2e8f0;
        }}

        pre code {{
            background-color: transparent;
            color: inherit;
            padding: 0;
            border: none;
        }}

        /* CITAS Y BLOQUES DESTACADOS */
        blockquote {{
            border-left: 4px solid #2563eb;
            background: #f8fafc;
            padding: 8px 14px;
            margin: 10pt 0;
            color: #334155;
            font-style: italic;
        }}

        /* ENLACES */
        a {{
            color: #2563eb;
            text-decoration: none;
        }}
    </style>
</head>
<body>

    <!-- PORTADA ACADÉMICA OFICIAL UPDS -->
    <div class="cover-page">
        <div class="cover-header">
            {"<img src='data:image/png;base64," + logo_b64 + "' class='cover-logo' alt='Logo UPDS'>" if logo_b64 else ""}
            <div class="cover-university">Universidad Privada Domingo Savio</div>
            <div class="cover-faculty">Facultad de Ingeniería &bull; Carrera de Ingeniería de Sistemas</div>
        </div>

        <div class="cover-center">
            <div class="cover-activity-tag">Programación IV &bull; Actividad N° 5</div>
            <h1 class="cover-title">Sistema de Gestión de Inventarios con CRUD, Patrones de Diseño e Inteligencia Artificial Local</h1>
            <p class="cover-subtitle">
                Implementación de un sistema web integral sobre Django, base de datos SQLite con 50 productos, arquitectura dual de IA con Ollama (invenbot) y menú analítico bajo el Patrón Strategy.
            </p>

            <div class="cover-metadata-card">
                <div class="meta-grid">
                    <div class="meta-label">Estudiante:</div>
                    <div class="meta-value">Ana Maribel Maydana</div>

                    <div class="meta-label">Docente:</div>
                    <div class="meta-value">Ing. Jared Lopez Leaños</div>

                    <div class="meta-label">Asignatura:</div>
                    <div class="meta-value">Programación IV</div>

                    <div class="meta-label">Fecha de Entrega:</div>
                    <div class="meta-value">28 de Septiembre de 2026</div>

                    <div class="meta-label">Entorno:</div>
                    <div class="meta-value">Debian 12 GNU/Linux &bull; Python 3.11 &bull; Django 5.2</div>

                    <div class="meta-label">Repositorio GitHub:</div>
                    <div class="meta-value">
                        <a href="https://github.com/AnaMaydana/programacion4">https://github.com/AnaMaydana/programacion4</a>
                    </div>
                </div>
            </div>
        </div>

        <div class="cover-footer">
            Santa Cruz de la Sierra / La Paz &bull; Bolivia &bull; 2026
        </div>
    </div>

    <!-- CUERPO PRINCIPAL DEL INFORME -->
    <main>
        {html_cuerpo}
    </main>

</body>
</html>
"""

    print("Renderizando PDF con WeasyPrint...")
    HTML(string=full_html, base_url=base_dir).write_pdf(output_pdf)
    print(f"PDF generado exitosamente en: {output_pdf}")

    # Copiar también dentro de proyecto/
    with open(output_pdf, "rb") as f_src, open(output_pdf_proyecto, "wb") as f_dst:
        f_dst.write(f_src.read())
    print(f"Copia del PDF guardada en: {output_pdf_proyecto}")

if __name__ == "__main__":
    generar_pdf()

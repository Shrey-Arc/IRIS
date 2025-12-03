"""
Dossier generation utilities for IRIS
Creates comprehensive ZIP packages with reports, certificates, and documents
"""

import os
import json
import hashlib
import zipfile
import tempfile
from typing import Tuple
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from .storage import create_signed_url_for_path, download_from_storage

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SERVICE_KEY)

def create_risk_report_pdf(analysis_data: dict, output_path: str):
    """Generate Risk Analysis Report PDF"""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Risk Analysis Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Risk Score
    risk_data = analysis_data.get('risk', {})
    risk_score = risk_data.get('risk_score', 0)
    
    score_style = ParagraphStyle(
        'Score',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=20
    )
    
    story.append(Paragraph(f"<b>Risk Score:</b> {risk_score:.2%}", score_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Risk Level
    if risk_score < 0.3:
        risk_level = "LOW"
        color = colors.green
    elif risk_score < 0.7:
        risk_level = "MEDIUM"
        color = colors.orange
    else:
        risk_level = "HIGH"
        color = colors.red
    
    story.append(Paragraph(f"<b>Risk Level:</b> <font color='{color.hexval()}'>{risk_level}</font>", score_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Top Risk Factors
    story.append(Paragraph("<b>Key Risk Factors:</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    factors = risk_data.get('top_factors', [])
    for i, factor in enumerate(factors, 1):
        story.append(Paragraph(f"{i}. {factor}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    # Explanation
    if 'explanation' in risk_data:
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("<b>Analysis Details:</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(risk_data['explanation'], styles['Normal']))
    
    # Generated timestamp
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        f"<i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        styles['Normal']
    ))
    
    doc.build(story)

def create_compliance_report_pdf(analysis_data: dict, output_path: str):
    """Generate Compliance Analysis Report PDF"""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Compliance Analysis Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Compliance Score
    compliance_data = analysis_data.get('compliance', {})
    compliance_score = compliance_data.get('compliance_score', 0)
    
    score_style = ParagraphStyle(
        'Score',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=20
    )
    
    story.append(Paragraph(f"<b>Compliance Score:</b> {compliance_score:.2%}", score_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Violations Table
    violations = compliance_data.get('violations', [])
    
    if violations:
        story.append(Paragraph(f"<b>Found {len(violations)} Compliance Issue(s):</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        # Create table
        table_data = [['#', 'Clause', 'Issue']]
        for i, violation in enumerate(violations, 1):
            table_data.append([
                str(i),
                Paragraph(violation.get('clause', 'N/A'), styles['Normal']),
                Paragraph(violation.get('issue', 'N/A'), styles['Normal'])
            ])
        
        table = Table(table_data, colWidths=[0.5*inch, 2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(table)
    else:
        story.append(Paragraph("<b>No compliance violations found.</b>", styles['Normal']))
    
    # Generated timestamp
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        f"<i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        styles['Normal']
    ))
    
    doc.build(story)

def create_crossverify_report_pdf(analysis_data: dict, output_path: str):
    """Generate Cross-Verification Report PDF"""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Cross-Verification Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Overall Score
    crossverify_data = analysis_data.get('crossverify', {})
    overall_score = crossverify_data.get('overall_score', 0)
    
    score_style = ParagraphStyle(
        'Score',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=20
    )
    
    story.append(Paragraph(f"<b>Overall Match Score:</b> {overall_score:.2%}", score_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Matches Table
    matches = crossverify_data.get('matches', {})
    
    if matches:
        story.append(Paragraph("<b>Field-by-Field Verification:</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        table_data = [['Field', 'Status']]
        for field, status in matches.items():
            status_color = colors.green if status == 'match' else colors.red
            table_data.append([
                field.upper(),
                Paragraph(f"<font color='{status_color.hexval()}'><b>{status.upper()}</b></font>", styles['Normal'])
            ])
        
        table = Table(table_data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(table)
    
    # Generated timestamp
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        f"<i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        styles['Normal']
    ))
    
    doc.build(story)

def create_certificate_pdf(dossier_data: dict, output_path: str):
    """Generate Blockchain Certificate PDF"""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("Certificate of Authenticity", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Certificate content
    cert_style = ParagraphStyle(
        'Certificate',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=15,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph(
        "This document certifies that the analysis dossier has been",
        cert_style
    ))
    story.append(Paragraph(
        "cryptographically verified and anchored on the Ethereum Sepolia blockchain.",
        cert_style
    ))
    story.append(Spacer(1, 0.5*inch))
    
    # Details
    details_style = ParagraphStyle(
        'Details',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10
    )
    
    story.append(Paragraph(f"<b>Dossier Hash:</b><br/>{dossier_data.get('sha256', 'N/A')}", details_style))
    story.append(Paragraph(f"<b>Transaction Hash:</b><br/>{dossier_data.get('tx_hash', 'Pending')}", details_style))
    story.append(Paragraph(f"<b>Timestamp:</b><br/>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", details_style))
    
    if dossier_data.get('explorer_url'):
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            f"<b>Verify on Blockchain:</b><br/><link href='{dossier_data['explorer_url']}'>{dossier_data['explorer_url']}</link>",
            details_style
        ))
    
    doc.build(story)

def generate_and_upload_dossier(document_id: str, user_id: str) -> Tuple[str, str, str]:
    """
    Generate comprehensive dossier ZIP file
    
    Args:
        document_id: Document UUID
        user_id: User UUID
        
    Returns:
        Tuple of (dossier_url, sha256, dossier_id)
    """
    # Fetch all related data
    doc_result = supabase.table("documents").select("*").eq("id", document_id).execute()
    analysis_result = supabase.table("analyses").select("*").eq("document_id", document_id).execute()
    heatmap_result = supabase.table("heatmaps").select("*").eq("user_id", user_id).execute()
    
    if not doc_result.data:
        raise Exception("Document not found")
    
    if not analysis_result.data:
        raise Exception("Analysis not found. Please wait for analysis to complete.")
    
    document = doc_result.data[0]
    analysis = analysis_result.data[0] if analysis_result.data else {}
    heatmaps = heatmap_result.data if heatmap_result.data else []
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create directory structure
        original_docs_dir = os.path.join(tmp_dir, "original_documents")
        reports_dir = os.path.join(tmp_dir, "reports")
        visuals_dir = os.path.join(tmp_dir, "visuals")
        
        os.makedirs(original_docs_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
        os.makedirs(visuals_dir, exist_ok=True)
        
        # 1. Download original PDF
        try:
            pdf_data = download_from_storage("documents", document['storage_path'])
            original_pdf_path = os.path.join(original_docs_dir, document['filename'])
            with open(original_pdf_path, 'wb') as f:
                f.write(pdf_data)
        except Exception as e:
            print(f"Warning: Could not download original PDF: {e}")
        
        # 2. Generate report PDFs
        risk_report_path = os.path.join(reports_dir, "risk_report.pdf")
        compliance_report_path = os.path.join(reports_dir, "compliance_report.pdf")
        crossverify_report_path = os.path.join(reports_dir, "cross_verify_report.pdf")
        
        create_risk_report_pdf(analysis, risk_report_path)
        create_compliance_report_pdf(analysis, compliance_report_path)
        create_crossverify_report_pdf(analysis, crossverify_report_path)
        
        # 3. Download heatmap images
        for i, heatmap in enumerate(heatmaps, 1):
            try:
                if heatmap.get('heatmap_path'):
                    heatmap_data = download_from_storage("heatmaps", heatmap['heatmap_path'])
                    heatmap_filename = f"heatmap{i}.png"
                    heatmap_path = os.path.join(visuals_dir, heatmap_filename)
                    with open(heatmap_path, 'wb') as f:
                        f.write(heatmap_data)
            except Exception as e:
                print(f"Warning: Could not download heatmap: {e}")
        
        # 4. Create metadata.json
        metadata = {
            "document": {
                "id": document['id'],
                "filename": document['filename'],
                "sha256": document['sha256'],
                "uploaded_at": str(document.get('created_at'))
            },
            "analysis": {
                "risk_score": analysis.get('risk', {}).get('risk_score'),
                "compliance_score": analysis.get('compliance', {}).get('compliance_score'),
                "crossverify_score": analysis.get('crossverify', {}).get('overall_score')
            },
            "generated_at": datetime.now().isoformat()
        }
        
        metadata_path = os.path.join(tmp_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # 5. Create certificate.pdf (placeholder until blockchain anchoring)
        certificate_path = os.path.join(tmp_dir, "certificate.pdf")
        create_certificate_pdf({
            "sha256": "To be generated",
            "tx_hash": "Pending blockchain anchoring",
            "explorer_url": None
        }, certificate_path)
        
        # 6. Create ZIP file
        zip_filename = f"{document_id}_dossier.zip"
        zip_path = os.path.join(tmp_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    if file == zip_filename:
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmp_dir)
                    zipf.write(file_path, arcname)
        
        # 7. Calculate SHA256 of ZIP
        with open(zip_path, 'rb') as f:
            zip_data = f.read()
            sha256 = hashlib.sha256(zip_data).hexdigest()
        
        # 8. Upload to storage
        storage_path = f"{user_id}/dossiers/{zip_filename}"
        
        from .storage import upload_bytes_to_storage
        upload_bytes_to_storage("dossiers", storage_path, zip_data, "application/zip")
        
        # 9. Generate signed URL
        dossier_url = create_signed_url_for_path("dossiers", storage_path, expires=86400)  # 24 hours
        
        # 10. Store in database
        dossier_result = supabase.table("dossiers").insert({
            "document_id": document_id,
            "user_id": user_id,
            "dossier_url": dossier_url,
            "sha256": sha256
        }).execute()
        
        if not dossier_result.data:
            raise Exception("Failed to store dossier record")
        
        dossier_id = dossier_result.data[0]["id"]
        
        return dossier_url, sha256, dossier_id
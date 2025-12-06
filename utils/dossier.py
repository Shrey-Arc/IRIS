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
    """Generate Credit Risk Analysis Report PDF"""
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
    story.append(Paragraph("Credit Risk Analysis Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Get risk data
    risk_data = analysis_data.get('risk', {})
    
    # Risk Score and Prediction
    score_style = ParagraphStyle(
        'Score',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=15
    )
    
    risk_score = risk_data.get('risk_score', 0)
    prediction = risk_data.get('prediction', 0)
    risk_class = risk_data.get('risk_class', 'unknown')
    probability = risk_data.get('probability', 0)
    
    # Display prediction result
    pred_text = "BAD CREDIT" if prediction == 1 else "GOOD CREDIT"
    pred_color = colors.red if prediction == 1 else colors.green
    
    story.append(Paragraph(
        f"<b>Credit Assessment:</b> <font color='{pred_color.hexval()}'><b>{pred_text}</b></font>",
        score_style
    ))
    story.append(Paragraph(f"<b>Risk Score:</b> {risk_score:.1%}", score_style))
    story.append(Paragraph(f"<b>Confidence:</b> {probability:.1%}", score_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Risk Factors
    story.append(Paragraph("<b>Risk Factors Identified:</b>", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    risk_factors = risk_data.get('risk_factors', [])
    if risk_factors:
        for i, factor in enumerate(risk_factors, 1):
            story.append(Paragraph(f"{i}. {factor}", styles['Normal']))
            story.append(Spacer(1, 0.08*inch))
    else:
        story.append(Paragraph("No significant risk factors detected.", styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Parsed Credit Application Details
    parsed_fields = risk_data.get('parsed_fields', {})
    if parsed_fields:
        story.append(Paragraph("<b>Credit Application Details:</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        # Create table for parsed fields
        field_data = [['Field', 'Value']]
        
        field_labels = {
            'age': 'Age',
            'gender': 'Gender',
            'job': 'Employment',
            'housing': 'Housing Status',
            'saving_accounts': 'Savings',
            'checking_account': 'Checking Account',
            'credit_amount': 'Credit Amount',
            'duration': 'Loan Duration',
            'purpose': 'Loan Purpose'
        }
        
        for field, label in field_labels.items():
            value = parsed_fields.get(field, 'N/A')
            if field == 'credit_amount' and value != 'N/A':
                value = f"₹{value:,.2f}"
            elif field == 'duration' and value != 'N/A':
                value = f"{value} months"
            field_data.append([label, str(value)])
        
        table = Table(field_data, colWidths=[2.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
    
    # Validation warnings if any
    validation_errors = risk_data.get('validation_errors', [])
    if validation_errors:
        story.append(Paragraph("<b>⚠️ Data Quality Warnings:</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        for error in validation_errors:
            story.append(Paragraph(f"• {error}", styles['Normal']))
            story.append(Spacer(1, 0.08*inch))
    
    # Timestamp
    story.append(Spacer(1, 0.4*inch))
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
    
    # Compliance data
    compliance_data = analysis_data.get('compliance', {})
    
    # Check if compliance is available
    status = compliance_data.get('status', 'unknown')
    if status == 'not_available':
        story.append(Paragraph(
            "<b>Note:</b> " + compliance_data.get('message', 'Compliance endpoint not yet available'),
            styles['Normal']
        ))
        story.append(Spacer(1, 0.2*inch))
    
    # Compliance Score
    score_style = ParagraphStyle(
        'Score',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=20
    )
    
    compliance_score = compliance_data.get('compliance_score', 0)
    story.append(Paragraph(f"<b>Compliance Score:</b> {compliance_score:.1%}", score_style))
    
    verification_status = compliance_data.get('status', 'unknown').upper()
    status_color = colors.green if compliance_score >= 0.8 else colors.red
    story.append(Paragraph(
        f"<b>Status:</b> <font color='{status_color.hexval()}'>{verification_status}</font>",
        score_style
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Violations Table
    violations = compliance_data.get('violations', [])
    
    if violations:
        story.append(Paragraph(f"<b>Found {len(violations)} Compliance Issue(s):</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        # Create table
        table_data = [['#', 'Regulation/Clause', 'Issue', 'Severity']]
        for i, violation in enumerate(violations, 1):
            severity = violation.get('severity', 'unknown').upper()
            table_data.append([
                str(i),
                Paragraph(violation.get('clause', 'N/A'), styles['Normal']),
                Paragraph(violation.get('issue', 'N/A'), styles['Normal']),
                severity
            ])
        
        table = Table(table_data, colWidths=[0.4*inch, 1.8*inch, 3.2*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(table)
    else:
        story.append(Paragraph("<b>✓ No compliance violations detected.</b>", styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Checks performed
    checks = compliance_data.get('checks_performed', [])
    if checks:
        story.append(Paragraph(f"<b>Checks Performed ({len(checks)}):</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        for check in checks:
            story.append(Paragraph(f"✓ {check}", styles['Normal']))
            story.append(Spacer(1, 0.05*inch))
    
    # Timestamp
    story.append(Spacer(1, 0.4*inch))
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
    story.append(Paragraph("Field Verification Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Cross-verify data
    crossverify_data = analysis_data.get('crossverify', {})
    
    # Check if cross-verify is available
    status = crossverify_data.get('status', 'unknown')
    if status == 'not_available':
        story.append(Paragraph(
            "<b>Note:</b> " + crossverify_data.get('message', 'Cross-verification endpoint not yet available'),
            styles['Normal']
        ))
        story.append(Spacer(1, 0.2*inch))
    
    # Overall Score
    score_style = ParagraphStyle(
        'Score',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=20
    )
    
    overall_score = crossverify_data.get('overall_score', 0)
    story.append(Paragraph(f"<b>Overall Verification Score:</b> {overall_score:.1%}", score_style))
    
    verification_status = crossverify_data.get('verification_status', 'unknown').upper()
    status_color = colors.green if overall_score >= 0.8 else colors.red
    story.append(Paragraph(
        f"<b>Status:</b> <font color='{status_color.hexval()}'>{verification_status}</font>",
        score_style
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Matches Table
    matches = crossverify_data.get('matches', {})
    
    if matches:
        story.append(Paragraph("<b>Field-by-Field Verification:</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        table_data = [['Field', 'Status', 'Details']]
        for field, match_status in matches.items():
            # Color code status
            if match_status == 'match':
                status_text = f"<font color='green'><b>✓ MATCH</b></font>"
            elif match_status == 'partial_match':
                status_text = f"<font color='orange'><b>~ PARTIAL</b></font>"
            elif match_status == 'mismatch':
                status_text = f"<font color='red'><b>✗ MISMATCH</b></font>"
            else:
                status_text = match_status.upper()
            
            table_data.append([
                field.replace('_', ' ').title(),
                Paragraph(status_text, styles['Normal']),
                ""
            ])
        
        table = Table(table_data, colWidths=[2*inch, 2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Discrepancies
    discrepancies = crossverify_data.get('discrepancies', [])
    if discrepancies:
        story.append(Paragraph(f"<b>⚠️ Discrepancies Detected ({len(discrepancies)}):</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        for disc in discrepancies:
            field = disc.get('field', 'Unknown')
            details = disc.get('details', 'No details')
            story.append(Paragraph(f"<b>{field.upper()}:</b> {details}", styles['Normal']))
            story.append(Spacer(1, 0.08*inch))
    
    # Timestamp
    story.append(Spacer(1, 0.4*inch))
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
import os
from fpdf import FPDF
import datetime

def generate_pdf_report(tx_data: dict, risk_score: int, risk_level: str, reasons: list):
    # Ensure reports directory exists
    if not os.path.exists('reports'):
        os.makedirs('reports')

    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(220, 53, 69) # Red
    pdf.cell(200, 10, txt="SENTINEL SDK - INCIDENT REPORT", ln=True, align='C')
    pdf.ln(10)

    # Executive Summary
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, txt="Executive Summary", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 10, txt=f"On {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, the Sentinel Anomaly Engine intercepted a highly suspicious transaction. The transaction was classified as {risk_level} with a Risk Score of {risk_score}/100.")
    pdf.ln(5)

    # Transaction Details
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Transaction Details", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 8, txt=f"Account ID: {tx_data.get('account_id')}", ln=True)
    pdf.cell(100, 8, txt=f"Amount: {tx_data.get('amount')} {tx_data.get('currency', 'INR')}", ln=True)
    pdf.cell(100, 8, txt=f"Recipient/Beneficiary: {tx_data.get('recipient')}", ln=True)
    pdf.cell(100, 8, txt=f"Memo: {tx_data.get('memo')}", ln=True)
    pdf.ln(5)

    # Device & Network Fingerprint
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Device & Network Fingerprint", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 8, txt=f"IP Address: {tx_data.get('device_ip')}", ln=True)
    pdf.cell(100, 8, txt=f"Is VPN/Proxy/Tor: {'Yes' if (tx_data.get('is_vpn') or tx_data.get('is_proxy') or tx_data.get('is_tor')) else 'No'}", ln=True)
    pdf.cell(100, 8, txt=f"OS: {tx_data.get('os', 'Unknown')}", ln=True)
    pdf.cell(100, 8, txt=f"Device Fingerprint: {tx_data.get('device_fingerprint', 'Unknown')}", ln=True)
    pdf.cell(100, 8, txt=f"Location (Lat/Long): {tx_data.get('latitude')}, {tx_data.get('longitude')}", ln=True)
    pdf.ln(5)

    # Triggered Rules
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Triggered Detection Rules & Breakdown", ln=True)
    pdf.set_font("Arial", '', 10)
    for reason in reasons:
        pdf.cell(200, 8, txt=f"- {reason}", ln=True)
    pdf.ln(5)

    # AI Recommended Actions
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Recommended Actions", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 10, txt="1. Immediately freeze the user's account.\n2. Trigger the Voice AI Assistant to call the user and verify intent.\n3. Escalate to the Fraud Ops team for manual review.\n4. Add IP and Device Fingerprint to the global blacklist.")

    # Save PDF
    file_name = f"reports/Incident_{tx_data.get('account_id')}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    pdf.output(file_name)
    return file_name

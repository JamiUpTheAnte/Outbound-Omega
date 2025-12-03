"""
Utility functions for Outbound Omega v2
"""
import secrets
from urllib.parse import urlparse


def generate_unsubscribe_token() -> str:
    """Generate a secure unsubscribe token"""
    return secrets.token_urlsafe(32)


def normalize_domain(url: str) -> str:
    """
    Extract and normalize domain from URL

    Example: 'https://www.example.com/page' -> 'example.com'
    """
    if not url:
        return ''

    if not url.startswith('http'):
        url = 'https://' + url

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Remove www.
    if domain.startswith('www.'):
        domain = domain[4:]

    return domain


def calculate_lead_score(lead) -> int:
    """
    Calculate a basic lead score

    Scoring factors:
    - Has phone: +10
    - Has contact name: +10
    - Times contacted but no reply: -5 each
    - Website available: +5
    - Email opened (future): +20
    - Replied: +50
    """
    score = 0

    if lead.contact.phone:
        score += 10

    if lead.contact.name and lead.contact.name != 'there':
        score += 10

    if lead.company.website:
        score += 5

    # Penalty for multiple attempts without response
    if lead.times_contacted > 2:
        score -= (lead.times_contacted - 2) * 5

    # Check activities for positive signals
    for activity in lead.activities:
        if activity.type == 'reply':
            score += 50
        elif activity.type == 'email_opened':
            score += 20
        elif activity.type == 'audit_form_completed':
            score += 40

    return max(0, score)  # Don't go negative

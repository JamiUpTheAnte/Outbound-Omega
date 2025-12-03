"""
Outbound Machine - Core logic for email sequences and outbound campaigns
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import requests

from models import db, Lead, LeadSequence, EmailStep, Email, Activity, Contact
from services.anthropic_service import AnthropicService
from services.email_service import EmailService


class OutboundMachine:
    """
    Core outbound engine that:
    - Determines which leads need emails
    - Generates email content via AI
    - Sends emails via Zoho
    - Tracks sends and updates CRM
    """

    def __init__(
        self,
        anthropic_service: AnthropicService,
        email_service: EmailService,
        max_emails_per_day: int
    ):
        self.anthropic_service = anthropic_service
        self.email_service = email_service
        self.max_emails_per_day = max_emails_per_day

    def run_outbound_cycle(self, from_address: str, dry_run: bool = False) -> Dict:
        """
        Main function to run an outbound cycle

        Args:
            from_address: Which from address to use for sending
            dry_run: If True, don't actually send, just report what would be sent

        Returns:
            Dict with stats about the cycle
        """

        stats = {
            'checked': 0,
            'eligible': 0,
            'sent': 0,
            'failed': 0,
            'skipped_opt_out': 0,
            'skipped_limit': 0,
            'errors': []
        }

        # Check daily send limit
        emails_sent_today = self._count_emails_sent_today(from_address)
        remaining_sends = self.max_emails_per_day - emails_sent_today

        if remaining_sends <= 0:
            stats['skipped_limit'] = 1
            return stats

        # Find leads that need emails
        leads_to_email = self._find_leads_due_for_email(limit=remaining_sends)
        stats['checked'] = len(leads_to_email)

        for lead_sequence in leads_to_email:
            lead = lead_sequence.lead
            contact = lead.contact

            # Check opt-out
            if contact.opt_out:
                stats['skipped_opt_out'] += 1
                continue

            stats['eligible'] += 1

            try:
                # Get the email step
                step = self._get_current_step(lead_sequence)
                if not step:
                    continue

                # Fetch website content for context (optional)
                website_content = self._fetch_website_homepage(lead.company.website)

                # Generate email content with AI
                lead_info = {
                    'company_name': lead.company.name,
                    'contact_name': contact.name or 'there',
                    'market_type': lead.company.market_type,
                    'website': lead.company.website,
                    'location': lead.company.location
                }

                template_context = json.loads(step.template_context) if step.template_context else None

                email_content = self.anthropic_service.generate_email_content(
                    lead_info=lead_info,
                    sequence_step=step.step_order,
                    template_context=template_context,
                    website_content=website_content
                )

                if dry_run:
                    print(f"[DRY RUN] Would send to {contact.email}:")
                    print(f"  Subject: {email_content['subject']}")
                    print(f"  Body preview: {email_content['body_text'][:100]}...")
                    stats['sent'] += 1
                    continue

                # Send the email
                result = self.email_service.send_email(
                    from_address=from_address,
                    to_address=contact.email,
                    subject=email_content['subject'],
                    body_text=email_content['body_text'],
                    body_html=email_content['body_html'],
                    unsubscribe_token=contact.unsubscribe_token
                )

                if result['success']:
                    # Record email in database
                    email = Email(
                        lead_id=lead.id,
                        sequence_id=lead_sequence.sequence_id,
                        step_order=step.step_order,
                        from_address=from_address,
                        to_address=contact.email,
                        subject=email_content['subject'],
                        body_text=email_content['body_text'],
                        body_html=email_content['body_html'],
                        status='sent',
                        provider_message_id=result['message_id'],
                        sent_at=datetime.utcnow()
                    )
                    db.session.add(email)

                    # Update lead
                    lead.times_contacted += 1
                    lead.last_contacted_at = datetime.utcnow()
                    lead.status = 'contacted'

                    # Update lead_sequence
                    lead_sequence.last_sent_at = datetime.utcnow()
                    lead_sequence.current_step += 1

                    # Check if sequence is complete
                    max_step = db.session.query(db.func.max(EmailStep.step_order)).filter(
                        EmailStep.sequence_id == lead_sequence.sequence_id,
                        EmailStep.is_active == True
                    ).scalar()

                    if lead_sequence.current_step > max_step:
                        lead_sequence.status = 'completed'

                    # Log activity
                    activity = Activity(
                        lead_id=lead.id,
                        type='email_sent',
                        activity_metadata=json.dumps({
                            'subject': email_content['subject'],
                            'from': from_address,
                            'sequence_step': step.step_order
                        })
                    )
                    db.session.add(activity)

                    db.session.commit()
                    stats['sent'] += 1

                else:
                    # Record failed email
                    email = Email(
                        lead_id=lead.id,
                        sequence_id=lead_sequence.sequence_id,
                        step_order=step.step_order,
                        from_address=from_address,
                        to_address=contact.email,
                        subject=email_content['subject'],
                        body_text=email_content['body_text'],
                        body_html=email_content['body_html'],
                        status='failed',
                        error_message=result['error']
                    )
                    db.session.add(email)
                    db.session.commit()

                    stats['failed'] += 1
                    stats['errors'].append({
                        'lead_id': lead.id,
                        'email': contact.email,
                        'error': result['error']
                    })

            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append({
                    'lead_id': lead.id,
                    'error': str(e)
                })
                db.session.rollback()

        return stats

    def _find_leads_due_for_email(self, limit: int) -> List[LeadSequence]:
        """Find lead_sequences that are due for an email"""

        # Get active lead sequences
        lead_sequences = LeadSequence.query.filter(
            LeadSequence.status == 'active'
        ).limit(limit * 2).all()  # Get extra in case some are filtered out

        due_sequences = []

        for ls in lead_sequences:
            # Skip if contact has opted out
            if ls.lead.contact.opt_out:
                continue

            # Get current step
            step = self._get_current_step(ls)
            if not step or not step.is_active:
                continue

            # Check if due
            if ls.last_sent_at is None:
                # Never sent, so it's due
                due_sequences.append(ls)
            else:
                # Check delay
                days_since_last = (datetime.utcnow() - ls.last_sent_at).days
                if days_since_last >= step.delay_days:
                    due_sequences.append(ls)

            if len(due_sequences) >= limit:
                break

        return due_sequences

    def _get_current_step(self, lead_sequence: LeadSequence) -> Optional[EmailStep]:
        """Get the current email step for a lead sequence"""
        return EmailStep.query.filter(
            EmailStep.sequence_id == lead_sequence.sequence_id,
            EmailStep.step_order == lead_sequence.current_step,
            EmailStep.is_active == True
        ).first()

    def _count_emails_sent_today(self, from_address: str) -> int:
        """Count how many emails were sent today from this address"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        count = Email.query.filter(
            Email.from_address == from_address,
            Email.status == 'sent',
            Email.sent_at >= today_start
        ).count()

        return count

    def _fetch_website_homepage(self, website_url: str, timeout: int = 5) -> Optional[str]:
        """
        Fetch website homepage for context (simple GET request)

        Returns first 2000 characters or None if fetch fails
        """
        if not website_url:
            return None

        try:
            response = requests.get(website_url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; OutboundBot/1.0)'
            })
            response.raise_for_status()

            # Return first 2000 chars of text content
            return response.text[:2000]

        except Exception as e:
            print(f"Failed to fetch website {website_url}: {e}")
            return None

    def add_lead_to_sequence(self, lead_id: int, sequence_id: int) -> LeadSequence:
        """Add a lead to an email sequence"""

        # Check if already in this sequence
        existing = LeadSequence.query.filter(
            LeadSequence.lead_id == lead_id,
            LeadSequence.sequence_id == sequence_id
        ).first()

        if existing:
            # Reactivate if paused
            if existing.status in ['paused', 'unsubscribed']:
                existing.status = 'active'
                db.session.commit()
            return existing

        # Create new lead_sequence
        lead_sequence = LeadSequence(
            lead_id=lead_id,
            sequence_id=sequence_id,
            current_step=1,
            status='active'
        )

        db.session.add(lead_sequence)

        # Update lead status
        lead = Lead.query.get(lead_id)
        if lead.status == 'new':
            lead.status = 'queued'

        db.session.commit()

        return lead_sequence

"""
Main Flask application for Outbound Omega v2
"""
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from datetime import datetime
import json
import secrets

from config import config
from models import (
    db, Company, Contact, Lead, Campaign, EmailSequence, EmailStep,
    LeadSequence, Email, Activity
)
from services.anthropic_service import AnthropicService
from services.email_service import EmailService
from services.outbound_machine import OutboundMachine
from utils import generate_unsubscribe_token, normalize_domain, calculate_lead_score


def create_app(config_name='default'):
    """Application factory"""

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Initialize services
    anthropic_service = AnthropicService(
        api_key=app.config['ANTHROPIC_API_KEY'],
        model=app.config['ANTHROPIC_MODEL']
    )

    email_service = EmailService(
        smtp_host=app.config['ZOHO_SMTP_HOST'],
        smtp_port=app.config['ZOHO_SMTP_PORT'],
        username=app.config['ZOHO_USERNAME'],
        password=app.config['ZOHO_PASSWORD'],
        physical_address=app.config['PHYSICAL_ADDRESS'],
        unsubscribe_base_url=app.config['UNSUBSCRIBE_BASE_URL'],
        company_name=app.config['COMPANY_NAME']
    )

    outbound_machine = OutboundMachine(
        anthropic_service=anthropic_service,
        email_service=email_service,
        max_emails_per_day=app.config['MAX_EMAILS_PER_DAY_PER_ADDRESS']
    )

    # Create tables
    with app.app_context():
        db.create_all()

    # ============================================================================
    # FRONTEND ROUTES
    # ============================================================================

    @app.route('/')
    def index():
        """Serve the main React app"""
        return render_template('index.html')

    # ============================================================================
    # SCRAPER INTEGRATION ROUTES
    # ============================================================================

    @app.route('/api/scraper/ingest', methods=['POST'])
    def ingest_leads():
        """
        Ingest leads from scraper JSON

        Expected JSON format:
        {
            "leads": [
                {
                    "company_name": "...",
                    "website": "...",
                    "contact_name": "...",
                    "contact_email": "...",
                    "phone": "...",
                    "location": "...",
                    "market_type": "...",
                    "tags": [...],
                    "source": "..."
                }
            ],
            "search_criteria": {
                "business_type": "...",
                "location": "...",
                "market_type": "..."
            }
        }
        """
        data = request.json
        leads_data = data.get('leads', [])
        search_criteria = data.get('search_criteria', {})

        stats = {
            'processed': 0,
            'companies_created': 0,
            'companies_updated': 0,
            'contacts_created': 0,
            'contacts_updated': 0,
            'leads_created': 0,
            'errors': []
        }

        for lead_data in leads_data:
            try:
                # Upsert company
                website = lead_data.get('website', '')
                domain = normalize_domain(website)

                company = Company.query.filter_by(website=website).first()

                if company:
                    # Update existing
                    company.name = lead_data.get('company_name', company.name)
                    company.location = lead_data.get('location', company.location)
                    company.market_type = lead_data.get('market_type', company.market_type)
                    company.updated_at = datetime.utcnow()
                    stats['companies_updated'] += 1
                else:
                    # Create new
                    company = Company(
                        name=lead_data.get('company_name', 'Unknown'),
                        website=website,
                        location=lead_data.get('location'),
                        market_type=lead_data.get('market_type')
                    )
                    db.session.add(company)
                    db.session.flush()  # Get the ID
                    stats['companies_created'] += 1

                # Upsert contact
                email = lead_data.get('contact_email', '').strip().lower()
                if not email:
                    stats['errors'].append(f"No email for {lead_data.get('company_name')}")
                    continue

                contact = Contact.query.filter_by(email=email).first()

                if contact:
                    # Update existing
                    contact.name = lead_data.get('contact_name', contact.name)
                    contact.phone = lead_data.get('phone', contact.phone)
                    contact.company_id = company.id
                    contact.updated_at = datetime.utcnow()
                    stats['contacts_updated'] += 1
                else:
                    # Create new
                    contact = Contact(
                        company_id=company.id,
                        name=lead_data.get('contact_name'),
                        email=email,
                        phone=lead_data.get('phone'),
                        unsubscribe_token=generate_unsubscribe_token()
                    )
                    db.session.add(contact)
                    db.session.flush()  # Get the ID
                    stats['contacts_created'] += 1

                # Check if lead already exists
                existing_lead = Lead.query.filter_by(
                    company_id=company.id,
                    contact_id=contact.id
                ).first()

                if not existing_lead:
                    # Create lead
                    lead = Lead(
                        company_id=company.id,
                        contact_id=contact.id,
                        source=lead_data.get('source', 'scraper_google'),
                        status='new',
                        search_criteria=json.dumps(search_criteria),
                        extra_fields=json.dumps({
                            'tags': lead_data.get('tags', [])
                        })
                    )
                    db.session.add(lead)
                    stats['leads_created'] += 1

                stats['processed'] += 1

            except Exception as e:
                stats['errors'].append(str(e))
                db.session.rollback()
                continue

        db.session.commit()

        return jsonify(stats), 201

    # ============================================================================
    # COMPANY ROUTES
    # ============================================================================

    @app.route('/api/companies', methods=['GET'])
    def list_companies():
        """List companies with pagination"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        pagination = Company.query.order_by(Company.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'companies': [c.to_dict() for c in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })

    @app.route('/api/companies/<int:company_id>', methods=['GET'])
    def get_company(company_id):
        """Get a single company"""
        company = Company.query.get_or_404(company_id)
        return jsonify(company.to_dict())

    @app.route('/api/companies', methods=['POST'])
    def create_company():
        """Create a new company"""
        data = request.json

        company = Company(
            name=data['name'],
            website=data.get('website'),
            location=data.get('location'),
            market_type=data.get('market_type'),
            size_estimate=data.get('size_estimate')
        )

        db.session.add(company)
        db.session.commit()

        return jsonify(company.to_dict()), 201

    @app.route('/api/companies/<int:company_id>', methods=['PUT'])
    def update_company(company_id):
        """Update a company"""
        company = Company.query.get_or_404(company_id)
        data = request.json

        company.name = data.get('name', company.name)
        company.website = data.get('website', company.website)
        company.location = data.get('location', company.location)
        company.market_type = data.get('market_type', company.market_type)
        company.size_estimate = data.get('size_estimate', company.size_estimate)
        company.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify(company.to_dict())

    # ============================================================================
    # CONTACT ROUTES
    # ============================================================================

    @app.route('/api/contacts', methods=['GET'])
    def list_contacts():
        """List contacts"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        pagination = Contact.query.order_by(Contact.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'contacts': [c.to_dict() for c in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })

    @app.route('/api/contacts/<int:contact_id>', methods=['GET'])
    def get_contact(contact_id):
        """Get a single contact"""
        contact = Contact.query.get_or_404(contact_id)
        return jsonify(contact.to_dict())

    # ============================================================================
    # LEAD ROUTES
    # ============================================================================

    @app.route('/api/leads', methods=['GET'])
    def list_leads():
        """List leads with filters"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status = request.args.get('status')
        campaign_id = request.args.get('campaign_id', type=int)
        market_type = request.args.get('market_type')

        query = Lead.query

        if status:
            query = query.filter(Lead.status == status)
        if campaign_id:
            query = query.filter(Lead.campaign_id == campaign_id)
        if market_type:
            query = query.join(Company).filter(Company.market_type == market_type)

        pagination = query.order_by(Lead.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'leads': [l.to_dict(include_relations=True) for l in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })

    @app.route('/api/leads/<int:lead_id>', methods=['GET'])
    def get_lead(lead_id):
        """Get a single lead with full details"""
        lead = Lead.query.get_or_404(lead_id)

        data = lead.to_dict(include_relations=True)

        # Add emails
        data['emails'] = [e.to_dict() for e in lead.emails]

        # Add activities
        data['activities'] = [a.to_dict() for a in lead.activities]

        # Add sequences
        data['sequences'] = [ls.to_dict() for ls in lead.lead_sequences]

        return jsonify(data)

    @app.route('/api/leads/<int:lead_id>', methods=['PUT'])
    def update_lead(lead_id):
        """Update a lead"""
        lead = Lead.query.get_or_404(lead_id)
        data = request.json

        if 'status' in data:
            old_status = lead.status
            lead.status = data['status']

            # Log status change
            activity = Activity(
                lead_id=lead.id,
                type='status_change',
                activity_metadata=json.dumps({
                    'old_status': old_status,
                    'new_status': lead.status
                })
            )
            db.session.add(activity)

        if 'campaign_id' in data:
            lead.campaign_id = data['campaign_id']

        if 'lead_score' in data:
            lead.lead_score = data['lead_score']

        if 'extra_fields' in data:
            lead.extra_fields = json.dumps(data['extra_fields'])

        lead.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify(lead.to_dict(include_relations=True))

    @app.route('/api/leads/<int:lead_id>/score', methods=['POST'])
    def recalculate_lead_score(lead_id):
        """Recalculate lead score"""
        lead = Lead.query.get_or_404(lead_id)
        lead.lead_score = calculate_lead_score(lead)
        db.session.commit()

        return jsonify({'lead_id': lead.id, 'score': lead.lead_score})

    # ============================================================================
    # CAMPAIGN ROUTES
    # ============================================================================

    @app.route('/api/campaigns', methods=['GET'])
    def list_campaigns():
        """List campaigns"""
        campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
        return jsonify([c.to_dict() for c in campaigns])

    @app.route('/api/campaigns/<int:campaign_id>', methods=['GET'])
    def get_campaign(campaign_id):
        """Get a campaign"""
        campaign = Campaign.query.get_or_404(campaign_id)
        return jsonify(campaign.to_dict())

    @app.route('/api/campaigns', methods=['POST'])
    def create_campaign():
        """Create a campaign"""
        data = request.json

        campaign = Campaign(
            name=data['name'],
            description=data.get('description'),
            niche=data.get('niche'),
            market=data.get('market'),
            offer=data.get('offer'),
            is_active=data.get('is_active', True)
        )

        db.session.add(campaign)
        db.session.commit()

        return jsonify(campaign.to_dict()), 201

    @app.route('/api/campaigns/<int:campaign_id>', methods=['PUT'])
    def update_campaign(campaign_id):
        """Update a campaign"""
        campaign = Campaign.query.get_or_404(campaign_id)
        data = request.json

        campaign.name = data.get('name', campaign.name)
        campaign.description = data.get('description', campaign.description)
        campaign.niche = data.get('niche', campaign.niche)
        campaign.market = data.get('market', campaign.market)
        campaign.offer = data.get('offer', campaign.offer)
        campaign.is_active = data.get('is_active', campaign.is_active)
        campaign.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify(campaign.to_dict())

    # ============================================================================
    # EMAIL SEQUENCE ROUTES
    # ============================================================================

    @app.route('/api/sequences', methods=['GET'])
    def list_sequences():
        """List email sequences"""
        sequences = EmailSequence.query.order_by(EmailSequence.created_at.desc()).all()
        return jsonify([s.to_dict(include_steps=True) for s in sequences])

    @app.route('/api/sequences/<int:sequence_id>', methods=['GET'])
    def get_sequence(sequence_id):
        """Get a sequence"""
        sequence = EmailSequence.query.get_or_404(sequence_id)
        return jsonify(sequence.to_dict(include_steps=True))

    @app.route('/api/sequences', methods=['POST'])
    def create_sequence():
        """Create an email sequence"""
        data = request.json

        sequence = EmailSequence(
            name=data['name'],
            description=data.get('description'),
            default_from_address=data.get('default_from_address')
        )

        db.session.add(sequence)
        db.session.flush()

        # Add steps
        for step_data in data.get('steps', []):
            step = EmailStep(
                sequence_id=sequence.id,
                step_order=step_data['step_order'],
                delay_days=step_data.get('delay_days', 0),
                template_context=json.dumps(step_data.get('template_context', {})),
                is_active=step_data.get('is_active', True)
            )
            db.session.add(step)

        db.session.commit()

        return jsonify(sequence.to_dict(include_steps=True)), 201

    @app.route('/api/sequences/<int:sequence_id>/steps', methods=['POST'])
    def add_sequence_step(sequence_id):
        """Add a step to a sequence"""
        sequence = EmailSequence.query.get_or_404(sequence_id)
        data = request.json

        step = EmailStep(
            sequence_id=sequence.id,
            step_order=data['step_order'],
            delay_days=data.get('delay_days', 0),
            template_context=json.dumps(data.get('template_context', {})),
            is_active=data.get('is_active', True)
        )

        db.session.add(step)
        db.session.commit()

        return jsonify(step.to_dict()), 201

    # ============================================================================
    # OUTBOUND MACHINE ROUTES
    # ============================================================================

    @app.route('/api/outbound/run', methods=['POST'])
    def run_outbound():
        """
        Trigger an outbound cycle

        Body:
        {
            "from_address": "email@domain.com",
            "dry_run": false
        }
        """
        data = request.json
        from_address = data.get('from_address', app.config['FROM_ADDRESSES'][0])
        dry_run = data.get('dry_run', False)

        try:
            stats = outbound_machine.run_outbound_cycle(
                from_address=from_address,
                dry_run=dry_run
            )

            return jsonify({
                'success': True,
                'stats': stats
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/outbound/add-to-sequence', methods=['POST'])
    def add_to_sequence():
        """
        Add leads to a sequence

        Body:
        {
            "lead_ids": [1, 2, 3],
            "sequence_id": 1
        }
        """
        data = request.json
        lead_ids = data.get('lead_ids', [])
        sequence_id = data['sequence_id']

        added = []
        errors = []

        for lead_id in lead_ids:
            try:
                lead_sequence = outbound_machine.add_lead_to_sequence(lead_id, sequence_id)
                added.append(lead_sequence.to_dict())
            except Exception as e:
                errors.append({'lead_id': lead_id, 'error': str(e)})

        return jsonify({
            'added': added,
            'errors': errors
        })

    # ============================================================================
    # UNSUBSCRIBE ROUTE
    # ============================================================================

    @app.route('/unsubscribe', methods=['GET'])
    def unsubscribe():
        """Handle unsubscribe requests"""
        token = request.args.get('token')

        if not token:
            return "Invalid unsubscribe link", 400

        # Find contact by token
        contact = Contact.query.filter_by(unsubscribe_token=token).first()

        if not contact:
            return "Invalid unsubscribe link", 404

        if contact.opt_out:
            return render_template('unsubscribed.html', already_unsubscribed=True)

        # Opt out the contact
        contact.opt_out = True
        contact.opt_out_at = datetime.utcnow()

        # Pause all active sequences for this contact's leads
        for lead in contact.leads:
            for ls in lead.lead_sequences:
                if ls.status == 'active':
                    ls.status = 'unsubscribed'

        db.session.commit()

        return render_template('unsubscribed.html', already_unsubscribed=False)

    # ============================================================================
    # ACTIVITY ROUTES
    # ============================================================================

    @app.route('/api/leads/<int:lead_id>/activities', methods=['POST'])
    def add_activity(lead_id):
        """Add an activity to a lead"""
        lead = Lead.query.get_or_404(lead_id)
        data = request.json

        activity = Activity(
            lead_id=lead.id,
            type=data['type'],
            activity_metadata=json.dumps(data.get('metadata', {}))
        )

        db.session.add(activity)

        # Handle special activity types
        if data['type'] == 'reply':
            lead.status = 'replied'
        elif data['type'] == 'audit_form_completed':
            lead.status = 'qualified'

        db.session.commit()

        return jsonify(activity.to_dict()), 201

    # ============================================================================
    # DASHBOARD / ANALYTICS ROUTES
    # ============================================================================

    @app.route('/api/dashboard/stats', methods=['GET'])
    def dashboard_stats():
        """Get dashboard statistics"""

        # Leads by status
        status_counts = db.session.query(
            Lead.status,
            db.func.count(Lead.id)
        ).group_by(Lead.status).all()

        # Emails sent today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        emails_today = Email.query.filter(
            Email.status == 'sent',
            Email.sent_at >= today_start
        ).count()

        # Active campaigns
        active_campaigns = Campaign.query.filter_by(is_active=True).count()

        # Recent activities
        recent_activities = Activity.query.order_by(
            Activity.created_at.desc()
        ).limit(10).all()

        return jsonify({
            'leads_by_status': dict(status_counts),
            'emails_sent_today': emails_today,
            'active_campaigns': active_campaigns,
            'recent_activities': [a.to_dict() for a in recent_activities],
            'total_leads': Lead.query.count(),
            'total_companies': Company.query.count()
        })

    # ============================================================================
    # CONFIGURATION ROUTES
    # ============================================================================

    @app.route('/api/config', methods=['GET'])
    def get_config():
        """Get current configuration"""
        return jsonify({
            'from_addresses': app.config['FROM_ADDRESSES'],
            'max_emails_per_day': app.config['MAX_EMAILS_PER_DAY_PER_ADDRESS'],
            'physical_address': app.config['PHYSICAL_ADDRESS'],
            'company_name': app.config['COMPANY_NAME']
        })

    return app


if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5001, debug=True)

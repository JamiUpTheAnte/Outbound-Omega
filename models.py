"""
Database models for Outbound Omega v2
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()


class Company(db.Model):
    """Companies table"""
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    website = db.Column(db.String(500), unique=True, index=True)
    location = db.Column(db.String(255))
    market_type = db.Column(db.String(100))
    size_estimate = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contacts = db.relationship('Contact', back_populates='company', cascade='all, delete-orphan')
    leads = db.relationship('Lead', back_populates='company', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'website': self.website,
            'location': self.location,
            'market_type': self.market_type,
            'size_estimate': self.size_estimate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Contact(db.Model):
    """Contacts table"""
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(50))
    role = db.Column(db.String(100))
    linkedin_url = db.Column(db.String(500))

    # Opt-out tracking
    opt_out = db.Column(db.Boolean, default=False, index=True)
    opt_out_at = db.Column(db.DateTime, nullable=True)

    # Unsubscribe token
    unsubscribe_token = db.Column(db.String(64), unique=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = db.relationship('Company', back_populates='contacts')
    leads = db.relationship('Lead', back_populates='contact', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'linkedin_url': self.linkedin_url,
            'opt_out': self.opt_out,
            'opt_out_at': self.opt_out_at.isoformat() if self.opt_out_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Campaign(db.Model):
    """Campaigns table"""
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    niche = db.Column(db.String(255))
    market = db.Column(db.String(255))
    offer = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    leads = db.relationship('Lead', back_populates='campaign')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'niche': self.niche,
            'market': self.market,
            'offer': self.offer,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Lead(db.Model):
    """Leads table"""
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=True)

    source = db.Column(db.String(100), default='scraper_google')
    status = db.Column(
        db.String(50),
        default='new',
        index=True
    )  # new, queued, contacted, replied, qualified, won, lost

    lead_score = db.Column(db.Integer, default=0)
    search_criteria = db.Column(db.Text)  # JSON string
    extra_fields = db.Column(db.Text)  # JSON string for flexible metadata

    times_contacted = db.Column(db.Integer, default=0)
    last_contacted_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = db.relationship('Company', back_populates='leads')
    contact = db.relationship('Contact', back_populates='leads')
    campaign = db.relationship('Campaign', back_populates='leads')
    emails = db.relationship('Email', back_populates='lead', cascade='all, delete-orphan')
    activities = db.relationship('Activity', back_populates='lead', cascade='all, delete-orphan')
    lead_sequences = db.relationship('LeadSequence', back_populates='lead', cascade='all, delete-orphan')

    def to_dict(self, include_relations=False):
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'contact_id': self.contact_id,
            'campaign_id': self.campaign_id,
            'source': self.source,
            'status': self.status,
            'lead_score': self.lead_score,
            'search_criteria': json.loads(self.search_criteria) if self.search_criteria else None,
            'extra_fields': json.loads(self.extra_fields) if self.extra_fields else None,
            'times_contacted': self.times_contacted,
            'last_contacted_at': self.last_contacted_at.isoformat() if self.last_contacted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_relations:
            data['company'] = self.company.to_dict() if self.company else None
            data['contact'] = self.contact.to_dict() if self.contact else None
            data['campaign'] = self.campaign.to_dict() if self.campaign else None

        return data


class EmailSequence(db.Model):
    """Email sequences table"""
    __tablename__ = 'email_sequences'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    default_from_address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    steps = db.relationship('EmailStep', back_populates='sequence', cascade='all, delete-orphan', order_by='EmailStep.step_order')
    lead_sequences = db.relationship('LeadSequence', back_populates='sequence', cascade='all, delete-orphan')
    emails = db.relationship('Email', back_populates='sequence')

    def to_dict(self, include_steps=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'default_from_address': self.default_from_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_steps:
            data['steps'] = [step.to_dict() for step in self.steps]

        return data


class EmailStep(db.Model):
    """Email steps within sequences"""
    __tablename__ = 'email_steps'

    id = db.Column(db.Integer, primary_key=True)
    sequence_id = db.Column(db.Integer, db.ForeignKey('email_sequences.id'), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    delay_days = db.Column(db.Integer, default=0)  # Days after previous step
    template_context = db.Column(db.Text)  # JSON string with template hints for AI
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sequence = db.relationship('EmailSequence', back_populates='steps')

    def to_dict(self):
        return {
            'id': self.id,
            'sequence_id': self.sequence_id,
            'step_order': self.step_order,
            'delay_days': self.delay_days,
            'template_context': json.loads(self.template_context) if self.template_context else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class LeadSequence(db.Model):
    """Tracks which leads are in which sequences"""
    __tablename__ = 'lead_sequences'

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    sequence_id = db.Column(db.Integer, db.ForeignKey('email_sequences.id'), nullable=False)
    current_step = db.Column(db.Integer, default=1)
    last_sent_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        db.String(50),
        default='active',
        index=True
    )  # active, paused, completed, unsubscribed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lead = db.relationship('Lead', back_populates='lead_sequences')
    sequence = db.relationship('EmailSequence', back_populates='lead_sequences')

    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'sequence_id': self.sequence_id,
            'current_step': self.current_step,
            'last_sent_at': self.last_sent_at.isoformat() if self.last_sent_at else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Email(db.Model):
    """Emails sent table"""
    __tablename__ = 'emails'

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    sequence_id = db.Column(db.Integer, db.ForeignKey('email_sequences.id'), nullable=True)
    step_order = db.Column(db.Integer, nullable=True)

    from_address = db.Column(db.String(255), nullable=False)
    to_address = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(500))
    body_text = db.Column(db.Text)
    body_html = db.Column(db.Text)

    status = db.Column(db.String(50), default='pending', index=True)  # pending, sent, failed
    provider_message_id = db.Column(db.String(255), nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lead = db.relationship('Lead', back_populates='emails')
    sequence = db.relationship('EmailSequence', back_populates='emails')

    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'sequence_id': self.sequence_id,
            'step_order': self.step_order,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'subject': self.subject,
            'body_text': self.body_text,
            'body_html': self.body_html,
            'status': self.status,
            'provider_message_id': self.provider_message_id,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Activity(db.Model):
    """Activity log for leads"""
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    type = db.Column(db.String(100), nullable=False, index=True)
    # Types: email_sent, email_opened, reply, note, audit_form_sent, audit_form_completed, status_change
    activity_metadata = db.Column(db.Text)  # JSON string (renamed from 'metadata' to avoid SQLAlchemy conflict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    lead = db.relationship('Lead', back_populates='activities')

    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'type': self.type,
            'metadata': json.loads(self.activity_metadata) if self.activity_metadata else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

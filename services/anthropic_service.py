"""
Anthropic AI service for generating email content
"""
import os
import requests
from typing import Dict, Optional


class AnthropicService:
    """Service for generating email content using Anthropic Claude API"""

    def __init__(self, api_key: str, model: str = 'claude-3-5-sonnet-20241022'):
        self.api_key = api_key
        self.model = model
        self.base_url = 'https://api.anthropic.com/v1/messages'

    def generate_email_content(
        self,
        lead_info: Dict,
        sequence_step: int,
        template_context: Optional[Dict] = None,
        website_content: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate email content using Anthropic Claude API

        Args:
            lead_info: Dict containing company, contact, market_type, website, etc.
            sequence_step: Which step in the sequence (1 = initial, 2+ = follow-ups)
            template_context: Optional template hints/guidance
            website_content: Optional scraped website content for context

        Returns:
            Dict with 'subject', 'body_text', and 'body_html'
        """

        if not self.api_key:
            # Return placeholder if API key not configured
            return self._generate_placeholder_email(lead_info, sequence_step)

        # Build the prompt for Claude
        prompt = self._build_prompt(lead_info, sequence_step, template_context, website_content)

        try:
            # Make API call to Anthropic
            response = requests.post(
                self.base_url,
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': self.api_key,
                    'anthropic-version': '2023-06-01'
                },
                json={
                    'model': self.model,
                    'max_tokens': 1024,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                },
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Parse the response
            content = result['content'][0]['text']
            return self._parse_email_response(content)

        except Exception as e:
            print(f"Error generating email with Anthropic: {e}")
            # Fallback to placeholder
            return self._generate_placeholder_email(lead_info, sequence_step)

    def _build_prompt(
        self,
        lead_info: Dict,
        sequence_step: int,
        template_context: Optional[Dict],
        website_content: Optional[str]
    ) -> str:
        """Build the prompt for Claude"""

        company_name = lead_info.get('company_name', 'the company')
        contact_name = lead_info.get('contact_name', 'there')
        market_type = lead_info.get('market_type', 'your industry')
        website = lead_info.get('website', '')
        location = lead_info.get('location', '')

        step_type = "initial outreach" if sequence_step == 1 else f"follow-up #{sequence_step - 1}"

        prompt = f"""You are writing a professional {step_type} email for a B2B outreach campaign.

RECIPIENT INFORMATION:
- Company: {company_name}
- Contact: {contact_name}
- Industry/Market: {market_type}
- Location: {location}
- Website: {website}

"""

        if website_content:
            prompt += f"""WEBSITE CONTEXT:
{website_content[:1000]}

"""

        if template_context:
            prompt += f"""CAMPAIGN CONTEXT:
{template_context}

"""

        prompt += """INSTRUCTIONS:
1. Write a personalized, professional email
2. Keep it concise (under 150 words)
3. Focus on value and relevance to their business
4. Use a conversational, authentic tone
5. Include a clear call-to-action
6. DO NOT make false claims or fabricate information
7. DO NOT use manipulative tactics
8. Be respectful of their time

"""

        if sequence_step == 1:
            prompt += """This is the INITIAL email. Introduce yourself briefly and explain why you're reaching out.
"""
        else:
            prompt += f"""This is FOLLOW-UP #{sequence_step - 1}. Reference the previous email briefly and provide additional value or a different angle.
"""

        prompt += """
FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
SUBJECT: [your subject line here]

BODY:
[your email body here]

Do not include any unsubscribe text or footer - that will be added automatically.
"""

        return prompt

    def _parse_email_response(self, content: str) -> Dict[str, str]:
        """Parse Claude's response into subject and body"""

        lines = content.strip().split('\n')
        subject = ''
        body_lines = []
        in_body = False

        for line in lines:
            if line.startswith('SUBJECT:'):
                subject = line.replace('SUBJECT:', '').strip()
            elif line.startswith('BODY:'):
                in_body = True
            elif in_body:
                body_lines.append(line)

        body_text = '\n'.join(body_lines).strip()

        # Convert to HTML (simple paragraph wrapping)
        body_html = self._text_to_html(body_text)

        return {
            'subject': subject or 'Quick question',
            'body_text': body_text,
            'body_html': body_html
        }

    def _text_to_html(self, text: str) -> str:
        """Convert plain text to simple HTML"""
        paragraphs = text.split('\n\n')
        html_paragraphs = [f'<p>{p.replace(chr(10), "<br>")}</p>' for p in paragraphs if p.strip()]
        return '\n'.join(html_paragraphs)

    def _generate_placeholder_email(self, lead_info: Dict, sequence_step: int) -> Dict[str, str]:
        """Generate placeholder email when API is not configured"""

        company_name = lead_info.get('company_name', 'your company')
        contact_name = lead_info.get('contact_name', 'there')

        if sequence_step == 1:
            subject = f"Quick question about {company_name}"
            body_text = f"""Hi {contact_name},

I noticed {company_name} and wanted to reach out about something that might be relevant to your business.

Would you be open to a brief conversation?

Best regards"""
        else:
            subject = f"Following up - {company_name}"
            body_text = f"""Hi {contact_name},

I wanted to follow up on my previous email. I understand you're busy, so I'll keep this brief.

Is this something you'd be interested in discussing?

Thanks"""

        body_html = self._text_to_html(body_text)

        return {
            'subject': subject,
            'body_text': body_text,
            'body_html': body_html
        }

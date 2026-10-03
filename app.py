"""
ElevanceSkills Internship - Customer Support AI Engine
Consolidated Application: Task 1 (Sentiment & Escalation) + Task 2 (Ticket Workflow & Routing)
"""

import json
import re
from datetime import datetime, time, timedelta
from typing import Dict, List, Any, Optional


# =====================================================================
# TASK 1: MULTILINGUAL SENTIMENT & TONE ADAPTATION ENGINE
# =====================================================================
class SentimentEscalationEngine:
    """
    Analyzes message sentiment, adjusts chatbot response tone, 
    and handles automatic escalation for high-risk or time-sensitive issues.
    """

    def __init__(
        self, 
        business_hours_start: time = time(9, 0), 
        business_hours_end: time = time(17, 0),
        unresolved_limit_minutes: float = 15.0
    ):
        self.business_hours_start = business_hours_start
        self.business_hours_end = business_hours_end
        self.unresolved_limit = timedelta(minutes=unresolved_limit_minutes)

        self.high_risk_keywords = {
            "account_compromise": ["hacked", "unauthorized access", "account stolen", "breach", "compromised"],
            "duplicate_payment": ["charged twice", "double payment", "duplicate charge", "billed two times"],
            "legal_threats": ["lawyer", "attorney", "sue", "legal action", "court", "consumer court"]
        }

    def is_within_business_hours(self, current_time: datetime) -> bool:
        """Returns True if timestamp falls inside Monday-Friday, 9 AM - 5 PM."""
        if current_time.weekday() >= 5:  # Saturday or Sunday
            return False
        return self.business_hours_start <= current_time.time() <= self.business_hours_end

    def detect_sentiment(self, message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Calculates primary sentiment and confidence scores."""
        text_lower = message.lower()

        # Sarcasm detection rule
        sarcasm_markers = ["oh great", "wonderful job", "thanks for nothing", "brilliant service"]
        is_sarcastic = any(m in text_lower for m in sarcasm_markers) or ("great" in text_lower and "broken" in text_lower)

        # Urgency detection
        urgent_markers = ["asap", "immediately", "urgent", "emergency", "right now"]
        is_urgent = any(m in text_lower for m in urgent_markers)

        # High-risk detection
        detected_risks = [
            category for category, terms in self.high_risk_keywords.items()
            if any(term in text_lower for term in terms)
        ]

        # Historical frustration tracking
        neg_count = sum(1 for m in history if m.get("sentiment") in ["negative", "frustrated"])

        if is_sarcastic:
            primary, confidence = "sarcastic", 0.88
        elif detected_risks or is_urgent:
            primary, confidence = ("urgent" if is_urgent else "negative"), 0.95
        elif neg_count >= 2 or any(term in text_lower for term in ["angry", "upset", "terrible", "unacceptable"]):
            primary, confidence = "frustrated", 0.92
        elif any(term in text_lower for term in ["thanks", "thank you", "great", "awesome"]):
            primary, confidence = "positive", 0.90
        else:
            primary, confidence = "neutral", 0.85

        return {
            "primary_sentiment": primary,
            "confidence_score": confidence,
            "is_sarcastic": is_sarcastic,
            "is_urgent": is_urgent,
            "high_risk_categories": detected_risks,
            "repeated_negative_count": neg_count
        }

    def adjust_response_tone(self, policy_response: str, sentiment_data: Dict[str, Any]) -> str:
        """Adapts output tone based on customer emotional state."""
        sentiment = sentiment_data["primary_sentiment"]
        if sentiment in ["frustrated", "sarcastic"]:
            prefix = "I understand how frustrating this situation is, and I apologize for the inconvenience. "
        elif sentiment == "urgent":
            prefix = "I recognize the urgency of your issue and am prioritizing this for you. "
        elif sentiment == "positive":
            prefix = "Thank you for reaching out! "
        else:
            prefix = ""
        return f"{prefix}{policy_response}"

    def evaluate_escalation(
        self, 
        message: str, 
        history: List[Dict[str, Any]], 
        conv_start_time: datetime,
        current_time: datetime
    ) -> Dict[str, Any]:
        """Evaluates whether to escalate and selects the target queue."""
        sentiment_data = self.detect_sentiment(message, history)
        in_business_hours = self.is_within_business_hours(current_time)

        should_escalate = False
        condition = None
        reason = None

        if sentiment_data["high_risk_categories"]:
            should_escalate = True
            condition = "High-Risk Category Detected"
            reason = f"Detected: {', '.join(sentiment_data['high_risk_categories'])}"

        elif sentiment_data["repeated_negative_count"] >= 2:
            should_escalate = True
            condition = "Repeated Negative Sentiment"
            reason = "Customer expressed repeated frustration across multiple messages."

        elif (current_time - conv_start_time) > self.unresolved_limit and sentiment_data["primary_sentiment"] in ["negative", "frustrated", "urgent", "sarcastic"]:
            should_escalate = True
            condition = "Unresolved Limit Exceeded (>15 mins)"
            reason = f"Unresolved negative interaction active for {int((current_time - conv_start_time).total_seconds() / 60)} minutes."

        target_queue = None
        if should_escalate or sentiment_data["is_urgent"]:
            should_escalate = True
            if not in_business_hours:
                target_queue = "On-Call Emergency Queue" if (sentiment_data["is_urgent"] or sentiment_data["high_risk_categories"]) else "Next-Working-Day Queue"
            else:
                target_queue = "Tier 2 Live Support Queue"

        record = None
        if should_escalate:
            hist_str = " | ".join([f"{m.get('role', 'user')}: {m.get('text', '')}" for m in history[-2:]])
            record = {
                "escalated": True,
                "reason": reason or "Urgent complaint handling",
                "activated_condition": condition or "Urgent Complaint Route",
                "target_queue": target_queue,
                "timestamp": current_time.isoformat(),
                "conversation_summary": f"Context: [{hist_str}] -> Message: '{message}'"
            }

        return {"sentiment_analysis": sentiment_data, "escalation_record": record}


# =====================================================================
# TASK 2: STRUCTURED TICKET WORKFLOW & ROUTING ENGINE
# =====================================================================
class TicketWorkflowEngine:
    """
    Extracts structured ticket details, checks missing information, 
    calculates priority and SLA status, and routes to appropriate agents.
    """

    def __init__(self, holidays: Optional[List[str]] = None):
        self.holidays = set(holidays or ["2026-01-01", "2026-12-25"])
        self.agents = [
            {"id": "AGENT_01", "name": "Alice", "skills": ["payments", "billing"], "workload": 2, "available": True},
            {"id": "AGENT_02", "name": "Bob", "skills": ["technical", "account"], "workload": 5, "available": True},
            {"id": "AGENT_03", "name": "Diana", "skills": ["legal", "high_priority"], "workload": 0, "available": True}
        ]
        self.existing_tickets: List[Dict[str, Any]] = []

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extracts customer, order, and issue details."""
        order_match = re.search(r'\b(ORD-\d{4,8}|\b\d{5,8}\b)', text)
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        phone_match = re.search(r'\+?\d{10,12}', text)

        category = "general"
        text_lower = text.lower()
        if any(w in text_lower for w in ["charged", "payment", "refund", "invoice", "double"]):
            category = "payments"
        elif any(w in text_lower for w in ["hacked", "login", "password", "compromise"]):
            category = "account"
        elif any(w in text_lower for w in ["lawyer", "legal", "sue"]):
            category = "legal"

        extracted = {
            "order_id": order_match.group(0) if order_match else None,
            "contact_email": email_match.group(0) if email_match else None,
            "contact_phone": phone_match.group(0) if phone_match else None,
            "issue_category": category,
            "issue_description": text
        }

        missing = [f for f in ["order_id", "contact_email"] if not extracted[f]]
        extracted["missing_mandatory_info"] = missing
        return extracted

    def generate_masked_summary(self, text: str) -> str:
        """Masks sensitive PII for secure agent handoffs."""
        masked = re.sub(r'([\w\.-]+)@([\w\.-]+\.\w+)', r'***@\2', text)
        masked = re.sub(r'\+?\d{6,12}', r'******', masked)
        masked = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '****-****-****-****', masked)
        return masked

    def is_business_day(self, dt: datetime) -> bool:
        """Checks if date is a working business day."""
        if dt.weekday() >= 5 or dt.strftime("%Y-%m-%d") in self.holidays:
            return False
        return True

    def calculate_sla_hours(self, start: datetime, end: datetime) -> float:
        """Calculates working hours spent excluding weekends and holidays."""
        curr = start
        hours = 0.0
        while curr < end:
            if self.is_business_day(curr) and 9 <= curr.hour < 17:
                hours += 1.0
            curr += timedelta(hours=1)
        return hours

    def calculate_priority(self, severity: str, sentiment: str, impact: str) -> Dict[str, Any]:
        """Calculates weighted priority score and SLA allowance."""
        score = 0
        score += {"critical": 40, "high": 30, "medium": 20, "low": 10}.get(severity.lower(), 10)
        score += {"urgent": 25, "frustrated": 20, "negative": 15, "neutral": 5}.get(sentiment.lower(), 5)
        score += {"high": 25, "medium": 15, "low": 5}.get(impact.lower(), 5)

        if score >= 75:
            return {"priority": "P1 - Critical", "score": score, "allowed_hours": 2.0}
        elif score >= 50:
            return {"priority": "P2 - High", "score": score, "allowed_hours": 6.0}
        elif score >= 30:
            return {"priority": "P3 - Medium", "score": score, "allowed_hours": 12.0}
        else:
            return {"priority": "P4 - Low", "score": score, "allowed_hours": 24.0}

    def check_duplicate(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Detects duplicates or groups related customer requests."""
        for existing in self.existing_tickets:
            if entities["order_id"] and entities["order_id"] == existing.get("order_id"):
                return {"action": "DUPLICATE_DETECTED", "parent_ticket_id": existing["ticket_id"]}
            if entities["contact_email"] and entities["contact_email"] == existing.get("contact_email"):
                return {"action": "RELATED_ISSUE_GROUPED", "parent_ticket_id": existing["ticket_id"]}
        return {"action": "CREATE_NEW_TICKET", "parent_ticket_id": None}

    def route_ticket(self, category: str, priority: str, current_time: datetime) -> Dict[str, Any]:
        """Matches tickets to available agents based on skill and workload."""
        if not (self.is_business_day(current_time) and 9 <= current_time.hour < 17):
            return {"assigned_agent": None, "queue": "AFTER_HOURS_HOLD_QUEUE", "reason": "Outside business hours."}

        candidates = [a for a in self.agents if a["available"] and category in a["skills"]]
        if not candidates or "P1" in priority:
            candidates = [a for a in self.agents if a["available"]]

        if not candidates:
            return {"assigned_agent": None, "queue": "UNASSIGNED_BACKLOG_QUEUE", "reason": "No agents available."}

        selected = min(candidates, key=lambda x: x["workload"])
        selected["workload"] += 1
        return {"assigned_agent": selected["name"], "agent_id": selected["id"], "queue": f"TIER_1_{category.upper()}_QUEUE"}


# =====================================================================
# MAIN PIPELINE DEMO
# =====================================================================
def main():
    print("=" * 60)
    print("CUSTOMER SUPPORT AI PIPELINE - TASKS 1 & 2")
    print("=" * 60)

    task1_engine = SentimentEscalationEngine()
    task2_engine = TicketWorkflowEngine()

    # Simulated input
    conversation_start = datetime(2026, 10, 5, 10, 0)
    current_time = datetime(2026, 10, 5, 10, 18)  # 18 mins elapsed
    user_message = "I was charged twice for order ORD-88123 ($150). My email is user@example.com. Fix this ASAP!"
    history = [
        {"role": "user", "text": "My order ORD-88123 payment failed.", "sentiment": "negative"},
        {"role": "assistant", "text": "Let me check that for you.", "sentiment": "neutral"}
    ]

    print("\n[1] SENTIMENT & ESCALATION ANALYSIS")
    escalation_res = task1_engine.evaluate_escalation(
        message=user_message,
        history=history,
        conv_start_time=conversation_start,
        current_time=current_time
    )
    print(json.dumps(escalation_res, indent=2))

    adapted_reply = task1_engine.adjust_response_tone(
        policy_response="We have logged your refund request under ticket guidelines.",
        sentiment_data=escalation_res["sentiment_analysis"]
    )
    print("\n[2] ADAPTED CHATBOT RESPONSE TONE")
    print(f"Bot Output: \"{adapted_reply}\"")

    print("\n[3] TICKET EXTRACTION & ROUTING WORKFLOW")
    entities = task2_engine.extract_entities(user_message)
    if entities["missing_mandatory_info"]:
        print(f"Status: INFO_REQUIRED. Missing: {entities['missing_mandatory_info']}")
    else:
        priority_info = task2_engine.calculate_priority("high", escalation_res["sentiment_analysis"]["primary_sentiment"], "high")
        routing_info = task2_engine.route_ticket(entities["issue_category"], priority_info["priority"], current_time)
        dup_info = task2_engine.check_duplicate(entities)
        masked_summary = task2_engine.generate_masked_summary(user_message)

        ticket_payload = {
            "ticket_id": "TICK-101",
            "masked_summary": masked_summary,
            "extracted_entities": entities,
            "priority": priority_info,
            "routing": routing_info,
            "duplication_check": dup_info
        }
        print(json.dumps(ticket_payload, indent=2))


if __name__ == "__main__":
    main()

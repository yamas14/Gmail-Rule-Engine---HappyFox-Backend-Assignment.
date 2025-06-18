from datetime import datetime, timedelta
import pytest
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rule_processor import RuleProcessor
import json
import tempfile

@pytest.fixture
def sample_rules():
    rules = {
        "rules": [
            {
                "conditions": [
                    {"field": "received_date", "predicate": "less than", "value": "7 days"},
                    {"field": "subject", "predicate": "does not contain", "value": "spam"}
                ],
                "predicate": "any",
                "actions": [{"type": "move_message", "label": "Important"}]
            },
            {
                "conditions": [
                    {"field": "subject", "predicate": "contains", "value": "urgent"},
                    {"field": "from_address", "predicate": "equals", "value": "boss@company.com"}
                ],
                "predicate": "all",
                "actions": [{"type": "mark_as_read"}]
            }
        ]
    }
    return rules

@pytest.fixture
def rule_processor(sample_rules, tmp_path):
    rules_file = tmp_path / "test_rules.json"
    with open(rules_file, 'w') as f:
        json.dump(sample_rules, f)
    return RuleProcessor(str(rules_file))

def test_rule_loading(rule_processor):
    assert len(rule_processor.rules) == 2
    # Rules are sorted by complexity, so the 'any' rule with date condition comes first
    assert rule_processor.rules[0]['predicate'] == 'any'
    assert rule_processor.rules[1]['predicate'] == 'all'

def test_rule_complexity_calculation(rule_processor):
    # Test complexity calculation for 'any' predicate
    any_rule = rule_processor.rules[0]
    complexity = rule_processor._calculate_rule_complexity(any_rule)
    assert complexity == 2.0  # 2 conditions * 1.0 ('any' predicate)

    # Test complexity calculation for 'all' predicate
    all_rule = rule_processor.rules[1]
    complexity = rule_processor._calculate_rule_complexity(all_rule)
    assert complexity == 3.0  # 2 conditions * 1.5 ('all' predicate)

def test_string_condition_evaluation(rule_processor):
    # Test contains predicate
    assert rule_processor._evaluate_string_condition(
        "Urgent meeting tomorrow", "contains", "urgent")
    
    # Test does not contain predicate
    assert rule_processor._evaluate_string_condition(
        "Important meeting", "does not contain", "urgent")
    
    # Test equals predicate
    assert rule_processor._evaluate_string_condition(
        "boss@company.com", "equals", "boss@company.com")
    
    # Test does not equal predicate
    assert rule_processor._evaluate_string_condition(
        "employee@company.com", "does not equal", "boss@company.com")

def test_date_condition_evaluation(rule_processor):
    now = datetime.now()
    five_days_ago = now - timedelta(days=5)
    ten_days_ago = now - timedelta(days=10)

    # Test less than predicate
    assert rule_processor._evaluate_date_condition(five_days_ago, "less than", "7 days")
    assert not rule_processor._evaluate_date_condition(ten_days_ago, "less than", "7 days")

    # Test greater than predicate
    assert not rule_processor._evaluate_date_condition(five_days_ago, "greater than", "7 days")
    assert rule_processor._evaluate_date_condition(ten_days_ago, "greater than", "7 days")

def test_rule_evaluation(rule_processor):
    # Test matching 'all' conditions rule
    email_data = {
        "subject": "URGENT: Meeting Today",
        "from_address": "boss@company.com",
        "received_date": datetime.now()
    }
    assert rule_processor._evaluate_rule(rule_processor.rules[1], email_data)  # Using the 'all' rule

    # Test non-matching 'all' conditions rule
    email_data = {
        "subject": "URGENT: Meeting Today",
        "from_address": "colleague@company.com",
        "received_date": datetime.now()
    }
    assert not rule_processor._evaluate_rule(rule_processor.rules[1], email_data)  # Should fail for non-matching address

def test_process_email(rule_processor):
    email_data = {
        "subject": "URGENT: Meeting Today",
        "from_address": "boss@company.com",
        "received_date": datetime.now()
    }
    actions = rule_processor.process_email(email_data)
    # Both rules will match: one for recent date + non-spam, one for urgent + boss
    assert len(actions) == 2
    action_types = {action['type'] for action in actions}
    assert 'mark_as_read' in action_types
    assert 'move_message' in action_types

def test_edge_cases(rule_processor):
    # Test empty email data
    empty_email = {}
    # Should handle missing fields gracefully
    try:
        assert not rule_processor._evaluate_rule(rule_processor.rules[1], empty_email)
    except (TypeError, AttributeError):
        pytest.fail("Rule processor should handle empty email data gracefully")

    # Test missing fields
    partial_email = {"subject": "Test"}
    try:
        assert not rule_processor._evaluate_rule(rule_processor.rules[1], partial_email)
    except (TypeError, AttributeError):
        pytest.fail("Rule processor should handle partial email data gracefully")

    # Test case insensitivity
    email_data = {
        "subject": "URGENT MEETING",
        "from_address": "BOSS@COMPANY.COM",
        "received_date": datetime.now()
    }
    assert rule_processor._evaluate_rule(rule_processor.rules[0], email_data)
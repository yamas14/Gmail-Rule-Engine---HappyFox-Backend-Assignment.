from gmail_client import GmailClient
from models import Session, Email
from rule_processor import RuleProcessor

def sync_emails(): # Fetch new emails and skip existing ones to avoid duplicates
    gmail_client = GmailClient()
    session = Session()
    
    emails = gmail_client.fetch_emails(batch_size=100)  
    print(f"\nFetched {len(emails)} new emails.")
    
    print("Storing to PostgreSQL...")
    
    existing_ids = set(id_tuple[0] for id_tuple in 
                      session.query(Email.message_id)
                      .filter(Email.message_id.in_([e['message_id'] for e in emails]))
                      .all())
    
    new_emails = [Email(**email_data) for email_data in emails 
                 if email_data['message_id'] not in existing_ids]
    
    if new_emails:
        session.bulk_save_objects(new_emails)
        session.commit()
    
    print(f"Saved {len(new_emails)} new emails. {len(emails) - len(new_emails)} duplicates skipped.\n")
    session.close()

def process_rules(): # Track rule matches and actions for reporting
    gmail_client = GmailClient()
    rule_processor = RuleProcessor('rules.json')
    session = Session()
    
    rules_count = len(rule_processor.rules)
    print(f"\nLoaded {rules_count} rules from rules.json")
    
    emails = session.query(Email).all()
    print(f"Scanning {len(emails)} emails...")
    
    rule_matches = {i+1: 0 for i in range(rules_count)}
    rule_actions = {i+1: set() for i in range(rules_count)}
    
    for email in emails:
        email_data = {
            'message_id': email.message_id,
            'from_address': email.from_address,
            'subject': email.subject,
            'received_date': email.received_date,
            'message_body': email.message_body
        }
        
        for rule_index, rule in enumerate(rule_processor.rules, 1):
            if rule_processor._evaluate_rule(rule, email_data):
                rule_matches[rule_index] += 1
                for action in rule['actions']:
                    if action['type'] == 'mark_as_read':
                        gmail_client.mark_as_read(email.message_id)
                        rule_actions[rule_index].add('Marked as read')
                    elif action['type'] == 'mark_as_unread':
                        gmail_client.mark_as_unread(email.message_id)
                        rule_actions[rule_index].add('Marked as unread')
                    elif action['type'] == 'move_message':
                        gmail_client.move_message(email.message_id, action['label'])
                        rule_actions[rule_index].add(f'Moved to label "{action["label"]}"')
    
    for rule_num in range(1, rules_count + 1):
        matches = rule_matches[rule_num]
        actions = list(rule_actions[rule_num])
        action_text = actions[0] if actions else 'No action taken'
        status = '[PASS]' if matches > 0 else '[FAIL]'
        print(f"{status} Rule {rule_num} matched {matches} emails — {action_text}")
    
    session.close()

if __name__ == '__main__':
    sync_emails()
    process_rules()

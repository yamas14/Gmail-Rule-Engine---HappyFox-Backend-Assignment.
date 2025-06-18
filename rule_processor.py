import json
from datetime import datetime, timedelta
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import re

class RuleProcessor:
    def __init__(self, rules_file):
        self._load_rules(rules_file)
        self._compile_rules()
        self.max_workers = 4 
    
    def _load_rules(self, rules_file):
        with open(rules_file, 'r') as f:
            data = json.load(f)
            self.rules = data['rules']
    
    def _compile_rules(self): #keywords/conditions/predicates for processing rules.json
        for rule in self.rules:
            for condition in rule['conditions']:
                if condition['predicate'] == 'contains' and condition['field'] != 'received_date':
                    condition['pattern'] = re.compile(re.escape(condition['value'].lower()))
            
            rule['complexity'] = self._calculate_rule_complexity(rule)
        
        self.rules.sort(key=lambda x: x['complexity'])
    
    def _calculate_rule_complexity(self, rule):
        base_score = len(rule['conditions'])
        predicate_score = 1.5 if rule['predicate'] == 'all' else 1
        return base_score * predicate_score
    
    def process_email(self, email_data): # Process rules concurrently for better performance
        actions = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_rule = {executor.submit(self._evaluate_rule, rule, email_data): rule 
                             for rule in self.rules}
            
            for future in future_to_rule:
                rule = future_to_rule[future]
                try:
                    if future.result():
                        actions.extend(rule['actions'])
                except Exception as e:
                    print(f"Error processing rule: {e}")
        
        return actions
    
    @lru_cache(maxsize=128)
    def _evaluate_condition(self, condition_key, field_value):
        field, predicate, value = condition_key
        
        if field == 'received_date':
            return self._evaluate_date_condition(field_value, predicate, value)
        else:
            return self._evaluate_string_condition(field_value, predicate, value)
    
    def _evaluate_rule(self, rule, email_data):
        conditions = rule['conditions']
        predicate = rule['predicate']
        
        results = []
        for condition in conditions:
            condition_key = (condition['field'], condition['predicate'], condition['value'])
            field_value = email_data.get(condition['field'], '')
            
            if 'pattern' in condition:
                result = bool(condition['pattern'].search(str(field_value).lower()))
            else:
                result = self._evaluate_condition(condition_key, field_value)
            
            results.append(result)
            
            if predicate == 'any' and result:
                return True
            elif predicate == 'all' and not result:
                return False
        
        return all(results) if predicate == 'all' else any(results)
    
    def _evaluate_date_condition(self, date_value, predicate, value):
        days = int(value.split()[0])
        threshold = datetime.now() - timedelta(days=days)
        
        if predicate == 'less than':
            return date_value > threshold
        else:  
            return date_value < threshold
    
    def _evaluate_string_condition(self, field_value, predicate, value):
        field_value = str(field_value).lower()
        value = str(value).lower()
        
        if predicate == 'contains':
            return value in field_value
        elif predicate == 'does not contain':
            return value not in field_value
        elif predicate == 'equals':
            return value == field_value
        else: 
            return value != field_value

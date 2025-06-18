# Gmail-Rule-Engine---HappyFox-Backend-Assignment.

This project is a backend automation tool that connects to the Gmail API, fetches emails, stores them in a PostgreSQL database, and applies user-defined rules (via `rules.json`) to perform actions such as marking emails as read/unread or moving them to custom labels.

---

## 🚀 Features

- ✅ OAuth2-based Gmail authentication (no IMAP)
- ✅ Fetch emails from inbox and store in a relational database
- ✅ Configurable rule engine (`rules.json`)
- ✅ Supported actions: mark as read/unread, move message to label
- ✅ Batch processing and duplicate prevention
- ✅ Custom label creation (if missing)
- ✅ Pytest-based test suite

---

## 🛠️ Tech Stack

- Python 3.12
- Gmail API (via `google-api-python-client`)
- SQLAlchemy (ORM)
- PostgreSQL (you can also use SQLite)
- Pytest for testing

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/happyfox-backend-assignment.git
cd happyfox-backend-assignment
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up gmail API Credentials
-Go to Google Cloud Console
-Create a new project and enable the Gmail API
-Generate OAuth credentials (Desktop App) and download the credentials.json
-Place credentials.json in the root of the project
-On first run, a browser window will open to authenticate and create a token.pkl file.

### 4. Configuration
```python
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pkl'
```

### 5. Usage
## Run the main Script
```bash
python main.py
```
-Fetches emails from your Gmail inbox
-Saves them to PostgreSQL
-Applies rules.json conditions
-Executes corresponding actions (via Gmail API)

### 6. Sample Output
```bash
Fetched 45 new emails.
Saved 30 new emails. 15 duplicates skipped.

✅ Rule 1 matched 3 emails — Moved to label "Spam-like"
✅ Rule 2 matched 1 emails — Marked as read
✅ Rule 3 matched 2 emails — Moved to label "HappyFox"
❌ Rule 4 matched 0 emails — No action taken
```
### 7. Rule Engine
-Each rule includes:
-One or more conditions (field, predicate, value)
-One or more actions (e.g. mark_as_read, move_message)
-A rule-level predicate: "all" or "any"
-✅ Supported Fields
from_address, subject, message_body, received_date
-✅ Supported Predicates
contains, equals, does not contain, less than (for date)
-✅ Supported Actions
mark_as_read, mark_as_unread, move_message 

## Sample Rule
```json
{
      "predicate": "all",
      "conditions": [
        {
          "field": "from_address",
          "predicate": "contains",
          "value": "avinas"
        },
        {
          "field": "subject",
          "predicate": "contains",
          "value": "HappyFox"
        }
      ],
      "actions": [
        {
          "type": "move_message",
          "label": "HappyFox"
        }
      ]
}
```

### 8. Run Tests
```bash
pytest tests/
```
![Alt Text]()

## Tests include:
-Email parsing
-Rule evaluation
-DB insertions

### 9. SnapShots


### 10. Demo Video

👉 [Click here to watch the demo](https://drive.google.com/file/d/12b245yowZ62F6O8EfyMbS0Fw99qOQIRj/view?usp=sharing)



### 11. Folder Structure
```pgsql
happyfox-backend/
├── main.py
├── gmail_client.py
├── rule_processor.py
├── config.py
├── rules.json
├── models.py
├── requirements.txt
├── token.pkl
├── credentials.json (ignored via .gitignore)
├── tests/
│   └── test_rule_processor.py/test_gmail_client.py/test_main.py/test_models.py
```





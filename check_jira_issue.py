#!/usr/bin/env python3
"""Check JIRA issue details"""
import os
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("JIRA_BASE_URL")
username = os.getenv("JIRA_USERNAME")
token = os.getenv("JIRA_TOKEN")

jira = JIRA(server=base_url, auth=(username, token))

# Check the latest issue
issue_key = "KAN-12"
issue = jira.issue(issue_key)

print(f"\n{'='*80}")
print(f"JIRA Issue: {issue.key}")
print(f"{'='*80}")
print(f"Summary: {issue.fields.summary}")
print(f"Status: {issue.fields.status.name}")
print(f"\nComments ({len(issue.fields.comment.comments)} total):")
print("-" * 80)

for i, comment in enumerate(issue.fields.comment.comments, 1):
    print(f"\n[Comment {i}] {comment.author.displayName} - {comment.created[:10]}")
    print(f"{comment.body}")
    print("-" * 80)

print(f"\nActivity Log:")
print("-" * 80)
# Get change history
for history in issue.changelog.histories:
    print(f"\n{history.created[:19]}: {history.author.displayName}")
    for item in history.items:
        if item.field == "status":
            print(f"  Status changed: {item.fromString} → {item.toString}")
        elif item.field == "Comment":
            print(f"  Comment added")

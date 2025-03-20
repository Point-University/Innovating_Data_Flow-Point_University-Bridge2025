import os
import logging
import json
from datetime import datetime
import requests
import azure.functions as func
from typing import Dict, Any

# Fetch HubSpot API key once
HUBSPOT_API_KEY = os.getenv("Hubspot_API_Key")

# Constants for HubSpot API
HUBSPOT_BASE_URL = "https://api.hubapi.com/crm/v3/objects"

# Standardized Headers
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {HUBSPOT_API_KEY}',
    'Accept': 'application/json'
}

def send_request(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    # Helper function to send a POST request to HubSpot API.
    url = f"{HUBSPOT_BASE_URL}/{endpoint}"
    response = requests.post(url, headers=HEADERS, data=json.dumps(data))

    if not response.ok:
        logging.error(f"Request to {url} failed: {response.status_code} {response.text}")
        raise Exception(f"HubSpot API request failed with status {response.status_code}")
    
    return response.json()

def create_hubspot_object(obj_type: str, properties: Dict[str, Any], associations: list = None) -> Dict[str, Any]:
    # Generic function to create a HubSpot object (Company, Contact, Deal).
    payload = {"properties": properties}
    
    if associations:
        payload["associations"] = associations
    
    return send_request(obj_type, payload)

def create_parent_company(parent_name: str, company_id: str) -> Dict[str, Any]:
    return create_hubspot_object("companies", {"name": parent_name, "re_id": company_id})

def create_child_org(child_org: str, parent_org_id: str) -> Dict[str, Any]:
    associations = [{
        "to": {"id": parent_org_id},
        "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 14}]
    }]
    return create_hubspot_object("companies", {"name": child_org}, associations)

def create_contact(firstname: str, lastname: str, email: str, company: str, parent_org_id: str) -> Dict[str, Any]:
    properties = {
        "email": email,
        "firstname": firstname,
        "lastname": lastname,
        "company": company,
        "poc": "true"
    }
    associations = [{
        "to": {"id": parent_org_id},
        "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 1}]
    }]
    return create_hubspot_object("contacts", properties, associations)

def create_deal(comp_name: str, amount: str, sub_start: str, sub_end: str, term: str, parent_org_id: str) -> Dict[str, Any]:
    properties = {
        "dealname": f"{comp_name} Main",
        "amount": amount,
        "closedate": datetime.today().strftime('%Y-%m-%d'),
        "pipeline": "28258969",
        "dealstage": "64210478",
        "subscription_start_date": sub_start,
        "subscription_end_date": sub_end,
        "subscription_servicer": "Point",
        "subscription_type": "GAP",
        "subscription_term": term
    }
    associations = [{
        "to": {"id": parent_org_id},
        "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 5}]
    }]
    return create_hubspot_object("deals", properties, associations)

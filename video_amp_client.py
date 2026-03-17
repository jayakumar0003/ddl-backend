import http.client
import json
import os
from urllib.parse import urlparse, unquote
import requests
import pandas as pd
from datetime import datetime

class VideoAmpClient:
    def __init__(self, username, password, client_id):
        self.username = username
        self.password = password
        self.client_id = client_id
        self.host = "login.videoamp.com"
        self.api_host = "api.videoamp.dev"

    def get_access_token(self):
        conn = http.client.HTTPSConnection(self.host)
        payload = json.dumps({
            "grant_type": "password",
            "scope": "openid profile email offline_access",
            "client_id": self.client_id,
            "username": self.username,
            "password": self.password
        })
        headers = {
            'Content-Type': 'application/json'
        }

        conn.request("POST", "/oauth/token?Content-Type=application/json", payload, headers)
        res = conn.getresponse()
        data = res.read()
        token_output = data.decode("utf-8")

        try:
            token_dict = json.loads(token_output)
            return token_dict.get("access_token")
        except json.JSONDecodeError:
            print("Failed to parse token response.")
            return None

    def search_audiences(self, type, audience_name, currency_of_record, status,  access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        audience_name_cond = ""
        if audience_name != "":
            audience_name_cond = f"&query={audience_name}"

        currency_record_cond = ""
        if currency_of_record != "":
            currency_record_cond = f"&currencyOfRecord={currency_of_record}"

        status_cond = ""
        if status != "":
            status_cond = f"&status={status}"

        endpoint = f"/v1/audiences?type={type}&pageSize=500{currency_record_cond}{audience_name_cond}{status_cond}"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_audiences(self, type, currency_of_record, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        currency_record_cond = ""
        if currency_of_record > 0:
            currency_record_cond = f"&currencyOfRecord={currency_of_record}"

        type_cond = ""
        if type != "":
            type_cond = f"&type={type}"

        endpoint = f"/v1/audiences?pageSize=500{type_cond}{currency_record_cond}"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_datasource_groups_by_record(self, currency_of_record, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        currency_record_cond = ""
        if currency_of_record > 0:
            currency_record_cond = f"&currencyOfRecord={currency_of_record}&dataLatency=FINAL"

        endpoint = f"/v1/library/datasourceGroups?&pageSize=500{currency_record_cond}"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_admeasurements(self, report_id, request_type, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        report_id_cond = ""
        if report_id:
            report_id_cond = f"&id={report_id}"

        request_type_cond = ""
        if request_type:
            request_type_cond = f"&type={request_type}"

        endpoint = f"/v2beta/adMeasurements?pageSize=500{report_id_cond}{request_type_cond}"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_admeasurement(self, report_id, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v2beta/adMeasurements/{report_id}"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_datasource_group(self, id, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v1/library/datasourceGroups/{id}"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_audience(self, id, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v1/audiences/{id}"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_campaign(self, id, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v1beta/campaigns/{id}"
        print(f"endpoint: {endpoint}")
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def delete_admeasurement(self, report_id, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v2beta/adMeasurements/{report_id}"
        conn.request("DELETE", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def delete_plan(self, id, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v1beta/plans/{id}"
        conn.request("DELETE", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def delete_campaign(self, id, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v1beta/campaigns/{id}"
        conn.request("DELETE", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def delete_datasource_group(self, id, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v1/library/datasourceGroups/{id}"
        conn.request("DELETE", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_campaigns(self, audience_id, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        audience_cond = ""
        if audience_id:
            audience_cond = f"&audience_ids={audience_id}"

        endpoint = f"/v1beta/campaigns?pageSize=500{audience_cond}"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_datasource_groups(self, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v1/library/datasourceGroups?pageSize=500"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_rate_cards(self, inventory_id, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v1beta/inventories/{inventory_id}"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_plans(self, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v1beta/plans"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def get_campaign_plans(self, access_token, campaign_id):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v1beta/plans?campaignIds={campaign_id}"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")
        
    def get_plan(self, plan_id, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = f"/v1beta/plans/{plan_id}"
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def save_plan(self, data, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        payload = json.dumps(data)
        conn.request("POST", "/v1beta/plans", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def save_campaign(self, data, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        payload = json.dumps(data)
        conn.request("POST", "/v1beta/campaigns", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def save_report(self, data, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        payload = json.dumps(data)
        conn.request("POST", "/v2beta/adMeasurements", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def save_datasource_group(self, data, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        payload = json.dumps(data)
        conn.request("POST", "/v1/library/datasourceGroups", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def datasource_filter_values(self, data, access_token):
        conn = http.client.HTTPSConnection(self.api_host)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        payload = json.dumps(data)
        conn.request("POST", "/v1/library/datasourceFilterValueOptionsSearch", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")
        
    def download_file_from_url(self, url, folder="downloads"):
        os.makedirs(folder, exist_ok=True)
        
        parsed_url = urlparse(url)
        filename = os.path.basename(unquote(parsed_url.path))
        print(f"File Name: '{filename}'")
        
        filepath = os.path.join(folder, filename)
        print(f"Downloading file to: '{filepath}'")

        response = requests.get(url)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"File downloaded and saved as '{filepath}'")
            return filepath
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            return ""
            
            
    def read_excel_sheet(self, filepath, sheetname):
        df = pd.read_excel(filepath, sheet_name=sheetname, header=1)
        df = df.dropna(axis=1, how='all')
        
        return df
        
    def read_campaign_details(self, filepath, sheetname="Objectives"):
        try:
            df = pd.read_excel(filepath, sheet_name=sheetname, header=1)
            df.columns = [col.strip().lower() for col in df.columns]

            term_col = next((col for col in df.columns if "term" in col), None)
            value_col = next((col for col in df.columns if "value" in col), None)

            if not term_col or not value_col:
                print("Could not find 'Term' and 'Value' columns in sheet.")
                return "", ""

            df = df[[term_col, value_col]].dropna()
            terms_dict = dict(zip(df[term_col].str.strip(), df[value_col].astype(str).str.strip()))

            campaign_name = terms_dict.get("Campaign name", "")
            campaign_id = terms_dict.get("Campaign id", "")

            print(f"Campaign name: {campaign_name}")
            print(f"Campaign id: {campaign_id}")

            return campaign_name, campaign_id

        except Exception as e:
            print(f"Error reading campaign details: {e}")
            return "", ""

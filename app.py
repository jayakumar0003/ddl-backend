
from flask import Flask, render_template_string, request, render_template, jsonify, session, make_response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from google.cloud import bigquery
from dotenv import load_dotenv
from flask.wrappers import *
from bq.sqls import *
from ranker import *
import pandas as pd
import os, sys, io
from datetime import datetime
import openpyxl
from io import BytesIO
from video_amp_client import VideoAmpClient
import smtplib
import requests
import tempfile
from email.message import EmailMessage
from flask import request, jsonify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
import requests
import tempfile


##changes
load_dotenv()


# load SQL modules, secrets
with open("module/config_prod.json", "r") as file:
    config = json.load(file)

# Add BQ directory
current_dir = os.path.dirname(os.path.abspath(__file__))
bq_dir = os.path.join(current_dir, 'bq')
sys.path.append(bq_dir)

#SMTP_CONFIG = config.get("SMTP", {})

# Instantiate app, sockets, env vars, and BQ client
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)
app.secret_key = config["SESSION_SALT"]
try:
    from google.cloud import bigquery
    client = bigquery.Client(project=config['PROJECT_ID'])
except Exception:
    print("BigQuery not configured. Running without BigQuery.")
    client = None 

videoamp_client = VideoAmpClient("radhika.ayyapusetty@groupm.com", "Welcome@123", env.pass)
videoamp_client_token = videoamp_client.get_access_token()


# def get_iap_user_email(request):
#     email = request.headers.get("X-Goog-Authenticated-User-Email")
#     if email:
#         return email.split(":")[-1]
#     return ""


# @app.route('/', methods=['GET'])
# def home():
#     user_email = get_iap_user_email(request)
#     session['user_email'] = user_email
#     return render_template('index.html')

@app.route("/")
def home():
    return "Hello World"

@app.route('/send-spot-export-email', methods=['POST'])
def send_spot_export_email():
    try:
        payload = request.get_json()

        to_email = payload.get("toEmail")
        attachment_url = payload.get("attachmentUrl")
        report_id = payload.get("reportId")
        report_name = payload.get("reportName")

        if not to_email:
            return jsonify({"error": "Recipient email is required"}), 400
        if not attachment_url:
            return jsonify({"error": "Attachment URL is required"}), 400

        # -----------------------------
        # Download Excel file
        # -----------------------------
        response = requests.get(attachment_url, timeout=60)
        response.raise_for_status()

        # -----------------------------
        # Encode attachment (NO temp file needed)
        # -----------------------------
        encoded_file = base64.b64encode(response.content).decode("utf-8")

        attachment = Attachment(
            FileContent(encoded_file),
            FileName("Spot_Level_Export.csv"),
            FileType("text/csv"),
            Disposition("attachment")
        )

        # -----------------------------
        # Build SendGrid email
        # -----------------------------
        message = Mail(
            from_email="no-reply@groupm.com",
            to_emails=to_email,
            subject=f"Spot Level Report CSV – Report ID {report_id}",
            html_content=f"""                
                <p>Please find attached the Spot Level Report CSV file.</p>
                <p><b>Report ID:</b> {report_id}</p>
                <p><b>Report Name:</b> {report_name}</p>
                <p>Regards,<br/>DDL Team</p>
            """
        )

        message.add_attachment(attachment)

        # -----------------------------
        # Send email via SendGrid
        # -----------------------------
        sg = SendGridAPIClient(config["SENDGRID_API_KEY"])
        print("SENDGRID_API_KEY", config["SENDGRID_API_KEY"])
        response = sg.send(message)

        return jsonify({
            "message": "Email sent successfully",
            "sendgrid_status": response.status_code
        }), 200

    except requests.exceptions.RequestException as e:
        print("Download error:", str(e))
        return jsonify({"error": "Failed to download attachment"}), 500

    except Exception as e:
        # THIS WILL SHOW THE REAL SENDGRID ERROR
        print("SendGrid error:", str(e))
        if hasattr(e, "body"):
            print("SendGrid response body:", e.body)
        return jsonify({"error": "Failed to send email"}), 500



# @app.route('/plan', methods=['GET'])
# def plan():
#     return render_template("plan.html")

@app.route('/api/plan', methods=['GET'])
def api_plan():
    plan_id = request.args.get('planId') or request.args.get('ID')
    if not plan_id:
        return jsonify({"error": "Missing planId parameter"}), 400
    if videoamp_client_token:
        response = videoamp_client.get_plan(plan_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500


# @app.route('/plans', methods=['GET'])
# def plans():
#     return render_template("plans.html")

@app.route('/api/plans', methods=['GET'])
def api_plans():
    if videoamp_client_token:
        response = videoamp_client.get_plans(videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500


@app.route('/get-plans', methods=['GET'])
def get_plans():
    if videoamp_client_token:
      plans_response = videoamp_client.get_plans(videoamp_client_token)
      # print(f"plans_response: {plans_response}")

    return jsonify(plans_response)

@app.route('/api/get-plans', methods=['GET'])
def api_get_plans():
    if videoamp_client_token:
        response = videoamp_client.get_plans(videoamp_client_token)
        response_json = json.loads(response)
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/get-campaign-plans', methods=['GET'])
def get_campaign_plans():
    campaign_id = request.args.get('campaignId')
    print(f"campaign_id: {campaign_id}")

    if videoamp_client_token:
      plans_response = videoamp_client.get_campaign_plans(videoamp_client_token, campaign_id)
      # print(f"plans_response: {plans_response}")

    return jsonify(plans_response)

@app.route('/api/get-campaign-plans', methods=['GET'])
def api_get_campaign_plans():
    campaign_id = request.args.get('campaignId') or request.args.get('ID')
    if not campaign_id:
        return jsonify({"error": "Missing campaignId parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.get_campaign_plans(videoamp_client_token, campaign_id)
        response_json = json.loads(response)
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

# @app.route('/create-plan', methods=['GET'])
# def create_plan():
#     return render_template("create_plan.html")

@app.route('/api/create-plan', methods=['GET'])
def api_create_plan():
    return jsonify({"message": "Create plan page data", "endpoint": "/api/create-plan"})


# @app.route('/view-report', methods=['GET'])
# def view_report():
#     return render_template("view_report.html")

@app.route('/api/view-report', methods=['GET'])
def api_view_report():
    report_id = request.args.get('reportID') or request.args.get('ID')
    if not report_id:
        return jsonify({"error": "Missing reportID parameter"}), 400
    if videoamp_client_token:
        response = videoamp_client.get_admeasurement(report_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500


# @app.route('/view-demographic-audience', methods=['GET'])
# def view_demographic_audience():
#     return render_template("view_demographic_audience.html")

@app.route('/api/view-demographic-audience', methods=['GET'])
def api_view_demographic_audience():
    audience_id = request.args.get('audienceId') or request.args.get('ID')
    if not audience_id:
        return jsonify({"error": "Missing audienceId parameter"}), 400
    if videoamp_client_token:
        response = videoamp_client.get_audience(audience_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500


# @app.route('/view-audience', methods=['GET'])
# def view_audience():
#     return render_template("view_audience.html")

@app.route('/api/view-audience', methods=['GET'])
def api_view_audience():
    audience_id = request.args.get('audienceId') or request.args.get('ID')
    if not audience_id:
        return jsonify({"error": "Missing audienceId parameter"}), 400
    if videoamp_client_token:
        response = videoamp_client.get_audience(audience_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500


# @app.route('/view-campaign', methods=['GET'])
# def view_campaign():
#     return render_template("view_campaign.html")

@app.route('/api/view-campaign', methods=['GET'])
def api_view_view_campaign():
    campaign_id = request.args.get('campaignId') or request.args.get('ID')
    if not campaign_id:
        return jsonify({"error": "Missing campaignId parameter"}), 400
    if videoamp_client_token:
        response = videoamp_client.get_campaign(campaign_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500


# @app.route('/create-datasource-group', methods=['GET'])
# def create_datasource_group():
#     return render_template("create_datasource_group.html")

@app.route('/api/create-datasource-group', methods=['GET'])
def api_create_datasource_group():
    return jsonify({"message": "Create datasource group page data", "endpoint": "/api/create-datasource-group"})


# @app.route('/view-datasource-group', methods=['GET'])
# def view_datasource_group():
#     return render_template("view_datasource_group.html")

@app.route('/api/view-datasource-group', methods=['GET'])
def api_view_datasource_group():
    datasource_group_id = request.args.get('datasourceGroupID') or request.args.get('ID')
    if not datasource_group_id:
        return jsonify({"error": "Missing datasourceGroupID parameter"}), 400
    if videoamp_client_token:
        response = videoamp_client.get_datasource_group(datasource_group_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500


# @app.route('/datasource-groups', methods=['GET'])
# def datasource_groups():
#     return render_template("datasource_groups.html")

@app.route('/api/datasource-groups', methods=['GET'])
def api_datasource_groups():
    if videoamp_client_token:
        response = videoamp_client.get_datasource_groups(videoamp_client_token)
        if isinstance(response, str):
            try: response = json.loads(response)
            except: pass
        return jsonify(response)
    return jsonify({"error": "Token not available"}), 500

# @app.route('/campaigns', methods=['GET'])
# def campaigns():
#     return render_template("campaigns.html")

@app.route('/api/campaigns', methods=['GET'])
def api_campaigns():
    audience_id = request.args.get('audienceId') or ""
    if videoamp_client_token:
        response = videoamp_client.get_campaigns(audience_id, videoamp_client_token)
        if isinstance(response, str):
            try: response = json.loads(response)
            except: pass
        return jsonify(response)
    return jsonify({"error": "Token not available"}), 500


# @app.route('/create-campaign', methods=['GET'])
# def create_campaign():
#     return render_template("create_campaign.html")


# @app.route('/audiences', methods=['GET'])
# def audiences():
#     return render_template("audiences.html")

#Using
@app.route('/api/audiences', methods=['GET'])
def api_audiences():

    type = request.args.get("type", "")
    currency = request.args.get("currencyOfRecord", "")

    # convert currency safely
    if currency:
        try:
            currency = int(currency)
        except:
            currency = 0
    else:
        currency = 0

    if videoamp_client_token:
        response = videoamp_client.get_audiences(type, currency, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)
        # print(f"response_json: {response_json}")
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

# @app.route('/demographic-audiences', methods=['GET'])
# def demographic_audiences():
#     return render_template("demographic_audiences.html")

@app.route('/api/demographic-audiences', methods=['GET'])
def api_demographic_audiences():
    if videoamp_client_token:
        response = videoamp_client.get_audiences("demo", 0, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)
        print(f"response_json: {response_json}")
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500


# @app.route('/measurement-reports', methods=['GET'])
# def measurement_reports():
#     return render_template("measurement_reports.html")

@app.route('/api/measurement-reports', methods=['GET'])
def api_measurement_reports():
    report_id = request.args.get('reportID') or ""
    request_type = request.args.get('requestType') or ""
    print(f"report_id: {report_id}")
    
    if videoamp_client_token:
        response = videoamp_client.get_admeasurements(report_id, request_type, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)
        print(f"response_json: {response_json}")
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500


@app.route('/get-admeasurements', methods=['GET'])
def get_admeasurements():
    report_id = request.args.get('reportID')
    request_type = request.args.get('requestType')

    print(f"report_id: {report_id}")
    print(f"request_type: {request_type}")

    if videoamp_client_token:
      response = videoamp_client.get_admeasurements(report_id, request_type, videoamp_client_token)
      # print(f"admeasurements response: {response}")

    return jsonify(response)

@app.route('/api/get-admeasurements', methods=['GET'])
def api_get_admeasurements():
    report_id = request.args.get('reportID') or request.args.get('ID')
    request_type = request.args.get('requestType') or ""

    if videoamp_client_token:
        response = videoamp_client.get_admeasurements(report_id, request_type, videoamp_client_token)
        response_json = json.loads(response)
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/get-admeasurement', methods=['GET'])
def get_admeasurement():
    report_id = request.args.get('reportID')

    if videoamp_client_token:
      response = videoamp_client.get_admeasurement(report_id, videoamp_client_token)
      # print(f"get_admeasurement response: {response}")

    return jsonify(response)

@app.route('/api/get-admeasurement', methods=['GET'])
def api_get_admeasurement():
    report_id = request.args.get('reportID') or request.args.get('ID')
    print(f"Id: {report_id}")
    if not report_id:
        return jsonify({"error": "Missing reportID parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.get_admeasurement(report_id, videoamp_client_token)
        response_json = json.loads(response)
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/get-audience', methods=['GET'])
def get_audience():
    audience_id = request.args.get('ID')
    print(f"audience_id: {audience_id}")

    if videoamp_client_token:
      response = videoamp_client.get_audience(audience_id, videoamp_client_token)

    return jsonify(response)

@app.route('/api/get-audience', methods=['GET'])
def api_get_audience():
    audience_id = request.args.get('audienceId') or request.args.get('ID')
    if not audience_id:
        return jsonify({"error": "Missing audienceId parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.get_audience(audience_id, videoamp_client_token)
        response_json = json.loads(response)
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/get-campaign', methods=['GET'])
def get_campaign():
    campaign_id = request.args.get('ID')
    print(f"campaign_id: {campaign_id}")

    if videoamp_client_token:
      response = videoamp_client.get_campaign(campaign_id, videoamp_client_token)

    return jsonify(response)

@app.route('/api/get-campaign', methods=['GET'])
def api_get_campaign():
    campaign_id = request.args.get('campaignId') or request.args.get('ID')
    if not campaign_id:
        return jsonify({"error": "Missing campaignId parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.get_campaign(campaign_id, videoamp_client_token)
        response_json = json.loads(response)
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/get-plan', methods=['GET'])
def get_plan():
    plan_id = request.args.get('planId')
    print(f"plan_id: {plan_id}")

    if videoamp_client_token:
      response = videoamp_client.get_plan(plan_id, videoamp_client_token)

    return jsonify(response)

@app.route('/api/get-plan', methods=['GET'])
def api_get_plan():
    plan_id = request.args.get('planId') or request.args.get('ID')
    if not plan_id:
        return jsonify({"error": "Missing planId parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.get_plan(plan_id, videoamp_client_token)
        response_json = json.loads(response)
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500


@app.route('/get-datasource-group', methods=['GET'])
def get_datasource_group():
    datasource_group_id = request.args.get('ID')
    print(f"datasource_group_id: {datasource_group_id}")

    if videoamp_client_token:
      response = videoamp_client.get_datasource_group(datasource_group_id, videoamp_client_token)
      # print(f"datasource group response: {response}")

    return jsonify(response)

@app.route('/api/get-datasource-group', methods=['GET'])
def api_get_datasource_group():
    datasource_group_id = request.args.get('datasourceGroupID') or request.args.get('ID')
    if not datasource_group_id:
        return jsonify({"error": "Missing datasourceGroupID parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.get_datasource_group(datasource_group_id, videoamp_client_token)
        response_json = json.loads(response)
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/delete-admeasurement', methods=['GET'])
def delete_admeasurement():
    report_id = request.args.get('reportID')
    print(f"report_id: {report_id}")

    if videoamp_client_token:
      response = videoamp_client.delete_admeasurement(report_id, videoamp_client_token)
      # print(f"delete_admeasurement response: {response}")

    return jsonify(response)

@app.route('/api/delete-admeasurement', methods=['GET', 'DELETE'])
def api_delete_admeasurement():
    report_id = request.args.get('reportID') or request.args.get('ID')
    if not report_id:
        return jsonify({"error": "Missing reportID parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.delete_admeasurement(report_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/delete-plan', methods=['GET'])
def delete_plan():
    plan_id = request.args.get('planID')
    print(f"plan_id: {plan_id}")

    if videoamp_client_token:
      response = videoamp_client.delete_plan(plan_id, videoamp_client_token)

    return jsonify(response)

@app.route('/api/delete-plan', methods=['GET', 'DELETE'])
def api_delete_plan():
    plan_id = request.args.get('planID') or request.args.get('ID')
    if not plan_id:
        return jsonify({"error": "Missing planID parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.delete_plan(plan_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/delete-campaign', methods=['GET'])
def delete_campaign():
    campaign_id = request.args.get('campaignID')
    print(f"campaign_id: {campaign_id}")

    if videoamp_client_token:
      response = videoamp_client.delete_campaign(campaign_id, videoamp_client_token)

    return jsonify(response)

@app.route('/api/delete-campaign', methods=['GET', 'DELETE'])
def api_delete_campaign():
    campaign_id = request.args.get('campaignID') or request.args.get('ID')
    if not campaign_id:
        return jsonify({"error": "Missing campaignID parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.delete_campaign(campaign_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/delete-datasource-group', methods=['GET'])
def delete_datasource_group():
    datasource_group_id = request.args.get('datasourceGroupID')
    print(f"datasource_group_id: {datasource_group_id}")

    if videoamp_client_token:
      response = videoamp_client.delete_datasource_group(datasource_group_id, videoamp_client_token)
      # print(f"delete datasource group response: {response}")

    return jsonify(response)

@app.route('/api/delete-datasource-group', methods=['GET', 'DELETE'])
def api_delete_datasource_group():
    datasource_group_id = request.args.get('datasourceGroupID') or request.args.get('ID')
    if not datasource_group_id:
        return jsonify({"error": "Missing datasourceGroupID parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.delete_datasource_group(datasource_group_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

# @app.route('/create-report', methods=['GET'])
# def create_report():
#     return render_template("create_report.html")

@app.route('/api/create-report', methods=['GET'])
def api_create_report():
    return jsonify({"message": "Create report page data", "endpoint": "/api/create-report"})


@app.route('/get-audiences-list', methods=['GET'])
def get_audiences_list():
    if videoamp_client_token:
        audiences_response = videoamp_client.get_audiences("advanced", 26, videoamp_client_token)
        print(f"audiences_response: {audiences_response}")

    return jsonify(audiences_response)

@app.route('/api/get-audiences-list', methods=['GET'])
def api_get_audiences_list():
    if videoamp_client_token:
        response = videoamp_client.get_audiences("advanced", 26, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500


@app.route('/get-audiences-by-year', methods=['GET'])
def get_audiences_by_year():
    currency_of_record = request.args.get('currencyOfRecord')
    if not currency_of_record:
        return jsonify({"error": "Missing currencyOfRecord parameter"}), 400

    currency_of_record = int(currency_of_record)
    print(f"currency_of_record: {currency_of_record}")

    if videoamp_client_token:
        audiences_response = videoamp_client.get_audiences("", currency_of_record, videoamp_client_token)

    return jsonify(audiences_response)

@app.route('/api/get-audiences-by-year', methods=['GET'])
def api_get_audiences_by_year():
    currency = request.args.get('currencyOfRecord')

    # convert currency safely
    if currency:
        try:
            currency = int(currency)
        except:
            currency = 0
    else:
        currency = 0

    if videoamp_client_token:
        response = videoamp_client.get_audiences("", currency, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/get-datasource-filters', methods=['POST'])
def get_datasource_filters():
    data = request.get_json()
    print("datasource-filters data:", data)

    response = videoamp_client.datasource_filter_values(data, videoamp_client_token)
    #print(f"datasource filters response: {response}")

    return jsonify(response)

@app.route('/api/get-datasource-filters', methods=['POST'])
def api_get_datasource_filters():
    data = request.get_json()
    if videoamp_client_token:
        response = videoamp_client.datasource_filter_values(data, videoamp_client_token)
        response_json = json.loads(response)
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/get-datasource-groups-by-year', methods=['GET'])
def get_datasource_groups_by_year():
    currency_of_record = request.args.get('currencyOfRecord')
    if not currency_of_record:
        return jsonify({"error": "Missing currencyOfRecord parameter"}), 400

    currency_of_record = int(currency_of_record)
    print(f"currency_of_record: {currency_of_record}")

    if videoamp_client_token:
        response = videoamp_client.get_datasource_groups_by_record(currency_of_record, videoamp_client_token)
        #print(f"datasource_groups_response: {response}")

    return jsonify(response)

@app.route('/api/get-datasource-groups-by-year', methods=['GET'])
def api_get_datasource_groups_by_year():
    currency = request.args.get('currencyOfRecord')

    # convert currency safely
    if currency:
        try:
            currency = int(currency)
        except:
            currency = 0
    else:
        currency = 0

    if videoamp_client_token:
        response = videoamp_client.get_datasource_groups_by_record(currency, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/get-reach', methods=['GET'])
def get_reach():
    plan_id = request.args.get('planId')
    if not plan_id:
        return jsonify({"error": "Missing plan_id parameter"}), 400

    reach_json = []
    if videoamp_client_token:
        response = videoamp_client.get_plan(plan_id, videoamp_client_token)
        if isinstance(response, str):
            plan_response = json.loads(response)

        for url in plan_response["output"]["values"]:
            download_folder = "/tmp"
            filepath = videoamp_client.download_file_from_url(url, download_folder)

            if filepath:
                summary_df = videoamp_client.read_excel_sheet(filepath, "Summary")
                summary_df['Metric'] = summary_df['Metric'].astype(str)
                #reach_data = summary_df[summary_df['Metric'].str.endswith('Reach')].copy()
                filtered_df = summary_df[
                    summary_df['Metric'].str.endswith('Reach') |
                    summary_df['Metric'].str.endswith('Avg Frequency')
                    ].copy()
                output_json = filtered_df.to_dict(orient='records')

    return jsonify(output_json)

@app.route('/api/get-reach', methods=['GET'])
def api_get_reach():
    plan_id = request.args.get('planId') or request.args.get('ID')
    if not plan_id:
        return jsonify({"error": "Missing plan_id parameter"}), 400

    output_json = []
    if videoamp_client_token:
        response = videoamp_client.get_plan(plan_id, videoamp_client_token)
        if isinstance(response, str):
            plan_response = json.loads(response)

        for url in plan_response.get("output", {}).get("values", []):
            download_folder = "/tmp"
            filepath = videoamp_client.download_file_from_url(url, download_folder)

            if filepath:
                summary_df = videoamp_client.read_excel_sheet(filepath, "Summary")
                summary_df['Metric'] = summary_df['Metric'].astype(str)
                filtered_df = summary_df[
                    summary_df['Metric'].str.endswith('Reach') |
                    summary_df['Metric'].str.endswith('Avg Frequency')
                    ].copy()
                output_json = filtered_df.to_dict(orient='records')

    return jsonify(output_json)

@app.route('/get-campaigns', methods=['GET'])
def get_campaigns():
    if videoamp_client_token:
      campaigns_response = videoamp_client.get_campaigns("", videoamp_client_token)
      # print(f"campaigns_response: {campaigns_response}")

    return jsonify(campaigns_response)

@app.route('/get-campaign-list', methods=['GET'])
def get_campaign_list():
    audience_id = request.args.get('audienceId')
    if not audience_id:
        return jsonify({"error": "Missing audienceId parameter"}), 400

    if videoamp_client_token:
        campaign_response = videoamp_client.get_campaigns(audience_id, videoamp_client_token)
        # print(f"campaign_response: {campaign_response}")

    return jsonify(campaign_response)

@app.route('/api/get-campaign-list', methods=['GET'])
def api_get_campaign_list():
    audience_id = request.args.get('audienceId') or request.args.get('ID')
    if not audience_id:
        return jsonify({"error": "Missing audienceId parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.get_campaigns(audience_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/get-rate-card-list', methods=['GET'])
def get_rate_card_list():
    inventory_id = request.args.get('inventoryId')
    if not inventory_id:
        return jsonify({"error": "Missing inventoryId parameter"}), 400

    if videoamp_client_token:
        rate_card_response = videoamp_client.get_rate_cards(inventory_id, videoamp_client_token)
        # print(f"rate_card_response: {rate_card_response}")

    return jsonify(rate_card_response)

@app.route('/api/get-rate-card-list', methods=['GET'])
def api_get_rate_card_list():
    inventory_id = request.args.get('inventoryId') or request.args.get('ID')
    if not inventory_id:
        return jsonify({"error": "Missing inventoryId parameter"}), 400

    if videoamp_client_token:
        response = videoamp_client.get_rate_cards(inventory_id, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500
@app.route('/get-audiences', methods=['GET'])
def get_audiences():
    if videoamp_client_token:
      audiences_response = videoamp_client.search_audiences(request.args.get('type'), request.args.get('audienceName'), request.args.get('currencyOfRecord'), request.args.get('status'), videoamp_client_token)
      # print(f"audiences_response: {audiences_response}")

    return jsonify(audiences_response)

@app.route('/api/get-audiences', methods=['GET'])
def api_get_audiences():
    audience_type = request.args.get('type') or ""
    audience_name = request.args.get('audienceName') or ""
    currency_of_record = request.args.get('currencyOfRecord') or ""
    status = request.args.get('status') or ""

    if videoamp_client_token:
        response = videoamp_client.search_audiences(audience_type, audience_name, currency_of_record, status, videoamp_client_token)

        # convert string → json
        response_json = json.loads(response)

        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/get-datasource-groups', methods=['GET'])
def get_datasource_groups():
    if videoamp_client_token:
      response = videoamp_client.get_datasource_groups(videoamp_client_token)
      # print(f"response: {response}")

    return jsonify(response)

@app.route('/api/get-datasource-groups', methods=['GET'])
def api_get_datasource_groups():
    if videoamp_client_token:
        response = videoamp_client.get_datasource_groups(videoamp_client_token)
        response_json = json.loads(response)
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/get-demographic-audiences', methods=['GET'])
def get_demographic_audiences():
  if videoamp_client_token:
    audiences_response = videoamp_client.get_audiences("demo", 0, videoamp_client_token)
    # print(f"audiences_response: {audiences_response}")

  return jsonify(audiences_response)

@app.route('/api/get-demographic-audiences', methods=['GET'])
def api_get_demographic_audiences():
    if videoamp_client_token:
        response = videoamp_client.get_audiences("demo", 0, videoamp_client_token)
        response_json = json.loads(response)
        return jsonify(response_json)

    return jsonify({"error": "Token not available"}), 500

@app.route('/submit-campaign', methods=['POST'])
def submit_campaign():
    try:
        data = request.get_json()
        print("campaign data:", data)

        save_campaign_response = videoamp_client.save_campaign(data, videoamp_client_token)
        print(f"save_campaign_response: {save_campaign_response}")

        save_campaign_data = json.loads(save_campaign_response)

        if isinstance(save_campaign_data, dict) and "error" in save_campaign_data:
            error_info = save_campaign_data["error"]
            if error_info.get("code") == 400:
                print(f"error_info: {error_info}")
                return jsonify({
                    "status": "error",
                    "message": "Plan save failed",
                    "details": error_info
                }), 400

        return jsonify({"message": "Campaign submitted successfully!"}), 200
    except Exception as e:
        print("Error in /submit-campaign:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/submit-report', methods=['POST'])
def submit_report():
    try:
        data = request.get_json()
        print("report data:", data)

        save_response = videoamp_client.save_report(data, videoamp_client_token)
        print(f"save_report_response: {save_response}")

        save_data = json.loads(save_response)

        if isinstance(save_data, dict) and "error" in save_data:
            error_info = save_data["error"]
            if error_info.get("code") == 400:
                print(f"error_info: {error_info}")
                return jsonify({
                    "status": "error",
                    "message": "Report save failed",
                    "details": error_info
                }), 400

        return jsonify({"message": "Report submitted successfully!"}), 200
    except Exception as e:
        print("Error in /submit-report:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route('/submit-datasource-group', methods=['POST'])
def submit_datasource_group():
    try:
        data = request.get_json()
        print("report data:", data)

        response = videoamp_client.save_datasource_group(data, videoamp_client_token)
        print(f"save_datasource_group: {response}")

        save_data = json.loads(response)

        if isinstance(save_data, dict) and "error" in save_data:
            error_info = save_data["error"]
            if error_info.get("code") == 400:
                print(f"error_info: {error_info}")
                return jsonify({
                    "status": "error",
                    "message": "Report save failed",
                    "details": error_info
                }), 400

        return jsonify({"message": "Report submitted successfully!"}), 200
    except Exception as e:
        print("Error in /submit-report:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/submit-plan', methods=['POST'])
def submit_plan():
    try:
        display_name = request.form.get('display_name')
        audience_id = request.form.get('audience_id')
        campaign_ids = request.form.getlist('campaign_ids[]')
        budget = request.form.get('budget')
        creative_duration = request.form.get('creative_duration')
        import_file = request.files.get('import_file')

        print("Display Name:", display_name)
        print("Audience ID:", audience_id)
        print("Campaign IDs:", campaign_ids)
        print("Budget:", budget)
        print("Creative Duration", creative_duration)

        df_titles = []
        inventory_id = 'c37249ab-d711-4a18-83d5-027306670cb5'
        if videoamp_client_token:
            rate_card_response = json.loads(videoamp_client.get_rate_cards(inventory_id, videoamp_client_token))
            df_titles = pd.DataFrame(rate_card_response["titles"])

            #df_titles = pd.DataFrame(rate_card_response["titles"])
            print(df_titles)

        if import_file:
            filename = import_file.filename
            # content = import_file.read().decode('utf-8')
            print(f"File Name: {filename}")
            csv_df = pd.read_csv(import_file, skiprows=0)
            print(csv_df.head(1))

            csv_df["Number of spots"] = csv_df["Number of spots"].fillna(0).astype(int)
            csv_df['Number of spots'] = pd.to_numeric(csv_df['Number of spots'], errors='coerce')
            csv_df["Network_lower"] = csv_df["Network"].str.lower()
            csv_df["Daypart_lower"] = csv_df["Daypart"].str.lower()
            grouped_df = (
                csv_df.groupby(['Network_lower', 'Daypart_lower'], as_index=False)['Number of spots']
                .sum()
            )
            print(grouped_df)

            df_titles["custom_param_1_lower"] = df_titles["custom_param_1"].str.lower()
            df_titles["custom_param_2_lower"] = df_titles["custom_param_2"].str.lower()

            merged_df = pd.merge(
                grouped_df,
                df_titles,
                left_on=["Network_lower", "Daypart_lower"],
                right_on=["custom_param_1_lower", "custom_param_2_lower"],
                how="inner"
            )

            print(merged_df.head(1))
            merged_df["Number of spots"] = merged_df["Number of spots"].fillna(0).astype(int)

            rate_card_overrides = []
            constraints = []
            for _, row in merged_df.iterrows():
                title_id = row['id']
                goal = row['Number of spots']
                print(f"goal: {goal}, title_id: {title_id}")
                rate_card_overrides.append({
                    "title_id": int(title_id),
                    "rate_type": "COST_PER_SPOT",
                    "rate": "500"
                })

                constraints.append({
                    "campaign_ids": campaign_ids,
                    "audience_id": audience_id,
                    "priority": 1,
                    "creative_duration_seconds": int(creative_duration),
                    "constraint_type": "FIXED_INVESTMENT_UNITS",
                    "operator": "EQUAL",
                    "goal": str(goal),
                    "title_filters": [
                        {"title_filter_type": "ID", "values": [str(title_id)]}
                    ]
                })

            # "rate_card_overrides": rate_card_overrides,
            payload = {
                "display_name": display_name,
                "campaign_ids": campaign_ids,
                "rate_card_id": "4ab51941-8cdd-11f0-972d-965cc6811429",
                "budget": str(budget),
                "constraints": constraints,
                "primary_objective": {
                    "objective_type": "OBJECTIVE_MAXIMIZE_REACH",
                    "audience_id": audience_id
                },
                "secondary_objective": {
                    "objective_type": "OBJECTIVE_MAXIMIZE_IMPRESSIONS",
                    "audience_id": audience_id
                }
            }

            print("Payload:", json.dumps(payload, indent=2))
            # return jsonify({"status": "success", "message": "tmp Plan submitted with file!"})

            save_plan_response = videoamp_client.save_plan(payload, videoamp_client_token)
            print(f"save_plan_response: {save_plan_response}")
            save_plan_data = json.loads(save_plan_response)

            if isinstance(save_plan_data, dict) and "error" in save_plan_data:
                error_info = save_plan_data["error"]
                if error_info.get("code") == 400:
                    print(f"error_info: {error_info}")
                    return jsonify({
                        "status": "error",
                        "message": "Plan save failed",
                        "details": error_info
                    }), 400

        return jsonify({"status": "success", "message": "Plan submitted with file!"})

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

# @app.route('/ap/submit-plan', methods=['POST'])
# def submit_plan():
#     try:
#         display_name = request.form.get('display_name')
#         audience_id = request.form.get('audience_id')
#         campaign_ids = request.form.getlist('campaign_ids[]')
#         budget = request.form.get('budget')
#         creative_duration = request.form.get('creative_duration')
#         import_file = request.files.get('import_file')
#         print("Display Name:", display_name)
#         print("Audience ID:", audience_id)
#         print("Campaign IDs:", campaign_ids)
#         print("Budget:", budget)
#         print("Creative Duration:", creative_duration)
#         df_titles = []
#         inventory_id = 'c37249ab-d711-4a18-83d5-027306670cb5'
#         if videoamp_client_token:
#             rate_card_response = json.loads(videoamp_client.get_rate_cards(inventory_id, videoamp_client_token))
#             df_titles = pd.DataFrame(rate_card_response["titles"])
#             print(df_titles)
#         # Baseline constraints (used if you do not attach an override csv)
#         constraints = []
        
#         if import_file:
#             filename = import_file.filename
#             print(f"File Name: {filename}")
#             csv_df = pd.read_csv(import_file, skiprows=0)
#             print(csv_df.head(1))
#             csv_df["Number of spots"] = csv_df["Number of spots"].fillna(0).astype(int)
#             csv_df['Number of spots'] = pd.to_numeric(csv_df['Number of spots'], errors='coerce')
#             csv_df["Network_lower"] = csv_df["Network"].str.lower()
#             csv_df["Daypart_lower"] = csv_df["Daypart"].str.lower()
#             grouped_df = (
#                 csv_df.groupby(['Network_lower', 'Daypart_lower'], as_index=False)['Number of spots']
#                 .sum()
#             )
#             print(grouped_df)
#             df_titles["custom_param_1_lower"] = df_titles["custom_param_1"].str.lower()
#             df_titles["custom_param_2_lower"] = df_titles["custom_param_2"].str.lower()
#             merged_df = pd.merge(
#                 grouped_df,
#                 df_titles,
#                 left_on=["Network_lower", "Daypart_lower"],
#                 right_on=["custom_param_1_lower", "custom_param_2_lower"],
#                 how="inner"
#             )
#             print(merged_df.head(1))
#             merged_df["Number of spots"] = merged_df["Number of spots"].fillna(0).astype(int)
#             rate_card_overrides = []
            
#             for _, row in merged_df.iterrows():
#                 title_id = row['id']
#                 goal = row['Number of spots']
#                 print(f"goal: {goal}, title_id: {title_id}")
#                 rate_card_overrides.append({
#                     "title_id": int(title_id),
#                     "rate_type": "COST_PER_SPOT",
#                     "rate": "500"
#                 })
#                 constraints.append({
#                     "campaign_ids": campaign_ids,
#                     "audience_id": audience_id,
#                     "priority": 1,
#                     "creative_duration_seconds": int(creative_duration),
#                     "constraint_type": "FIXED_INVESTMENT_UNITS",
#                     "operator": "EQUAL",
#                     "goal": str(goal),
#                     "title_filters": [
#                         {"title_filter_type": "ID", "values": [str(title_id)]}
#                     ]
#                 })
#         payload = {
#             "display_name": display_name,
#             "campaign_ids": campaign_ids,
#             "rate_card_id": "4ab51941-8cdd-11f0-972d-965cc6811429",
#             "budget": str(budget),
#             "constraints": constraints,
#             "primary_objective": {
#                 "objective_type": "OBJECTIVE_MAXIMIZE_REACH",
#                 "audience_id": audience_id
#             },
#             "secondary_objective": {
#                 "objective_type": "OBJECTIVE_MAXIMIZE_IMPRESSIONS",
#                 "audience_id": audience_id
#             }
#         }
#         print("Payload:", json.dumps(payload, indent=2))
#         save_plan_response = videoamp_client.save_plan(payload, videoamp_client_token)
#         print(f"save_plan_response: {save_plan_response}")
#         save_plan_data = json.loads(save_plan_response)
#         if isinstance(save_plan_data, dict) and "error" in save_plan_data:
#             error_info = save_plan_data["error"]
#             if error_info.get("code") == 400:
#                 print(f"error_info: {error_info}")
#                 return jsonify({
#                     "status": "error",
#                     "message": "Plan save failed",
#                     "details": error_info
#                 }), 400
#         return jsonify({"status": "success", "message": "Plan submitted successfully!"})
#     except Exception as e:
#         print("Error:", e)
#         return jsonify({"status": "error", "message": str(e)}), 500

# @app.route('/upload-csv', methods=['GET', 'POST'])
# def upload_csv():
#     if request.method == 'GET':
#         return render_template('upload.html')
#     else:

@app.route('/api/upload-csv', methods=['POST'])
def api_upload_csv_real():
    if True:
        files = request.files.getlist('files[]')
        if not files or any(file.filename == '' for file in files):
            return jsonify({'error': 'No file selected'})

        # Validate, then upload each CSV file to the server
        for index, file in enumerate(files):
            try: 
                va_df = pd.read_csv(file)

                # Clean & rename columns given raw VA UI export
                try:
                    va_df = va_df.rename(columns={"custom_param_1": "platform", "custom_param_2":"daypart"}).drop(["Unnamed: 0", "custom_param_3", "metric_configuration_id", "start_datetime"], axis=1)
                except:
                    print("Sheet already cleaned")
                    pass

            except Exception as e:
                print(f'Unable to read {file} as a DF -- {e}')
                return jsonify({'error': f'Unable to read {file} as a CSV. Ensure you\'re uploading a CSV and the appropriate columns are attached.'})
            socketio.emit('update', {'file': file.filename, 'status': 'uploaded to server..', 'index': float(index-.5 + 1), 'total': len(files)})
        
            # upload to BQ
            from bq.sqls import save_videoamp_as_table
            result = save_videoamp_as_table(client, os.getcwd(), file)
            response = json.loads(result.data.decode('utf-8'))
            if 'error' in response.keys():
                socketio.emit('update', {'file': file.filename, 'status': 'Failed to read the CSV', 'index': float(0), 'total': len(files)})
                return jsonify({"error": f"Error uploading to BQ. Please confirm you are uploading the direct raw export from VA -- {response['error'][750:]}..."})

            socketio.emit('update', {'file': file.filename, 'status': 'uploaded to bigquery..', 'index': index + 1, 'total': len(files)})

        return jsonify({'success': 'All files processed successfully'})




# This function is written entirely for the equivalized_spots logic
def apply_equivalized_spots(df, form_data):
    """
    Multiply each row into multiple rows based on spot length distribution
    30s = baseline, 15s = impressions x2, 60s = impressions x0.5, 90s = impressions x0.33
    """
    import pandas as pd
    
    # Get user percentages (default to 30/70/0/0 if not provided)
    spots_15s_pct = float(form_data.get('spots_15s', 30)) / 100
    spots_30s_pct = float(form_data.get('spots_30s', 70)) / 100  
    spots_60s_pct = float(form_data.get('spots_60s', 0)) / 100
    spots_75s_pct = float(form_data.get('spots_75s', 0)) / 100
    spots_90s_pct = float(form_data.get('spots_90s', 0)) / 100
    
    multiplied_rows = []
    
    for _, row in df.iterrows():
        original_spots = row['num_buys']
        
        # Skip rows with no spots
        if pd.isna(original_spots) or original_spots == 0:
            continue
            
        # Calculate spots for each length
        spots_15s = round(original_spots * spots_15s_pct)
        spots_30s = round(original_spots * spots_30s_pct)
        spots_60s = round(original_spots * spots_60s_pct)
        spots_75s = round(original_spots * spots_75s_pct)
        spots_90s = round(original_spots * spots_90s_pct)
        
        # Create 15s row (impressions x2)
        if spots_15s > 0:
            row_15s = row.copy()
            row_15s['num_buys'] = spots_15s
            row_15s['length'] = ':15'
            # Original impressions stay same, equivalized are doubled
            row_15s['equiv_va_imps'] = row['videoamp_imps'] * 0.5
            row_15s['equiv_nielsen_imps'] = row['nielsen_imps'] * 0.5
            row_15s['Age-Gender Imps'] = row['nielsen_imps']  
            row_15s['Equiv Age-Gender Imps'] = row['nielsen_imps'] * 0.5
            row_15s['midas_cost_row'] = row['midas_cost_row'] * 0.5
            # Calculate equiv eCPM: (spots * cost_per_spot) / (spots * equiv_imps) * 1000
            row_15s['equiv_ecpm'] = round((spots_15s * row_15s['midas_cost_row'] / (spots_15s * row_15s['equiv_va_imps'])) * 1000, 2) if row_15s['equiv_va_imps'] > 0 else 0
            multiplied_rows.append(row_15s)
        
        # Create 30s row (baseline - no changes to impressions)
        if spots_30s > 0:
            row_30s = row.copy()
            row_30s['num_buys'] = spots_30s
            row_30s['length'] = ':30'
            # Equivalized values same as original for 30s baseline
            row_30s['equiv_va_imps'] = row['videoamp_imps']
            row_30s['equiv_nielsen_imps'] = row['nielsen_imps']
            row_30s['Age-Gender Imps'] = row['nielsen_imps']  
            row_30s['Equiv Age-Gender Imps'] = row['nielsen_imps']
            row_30s['midas_cost_row'] = row['midas_cost_row'] * 1.0
            row_30s['equiv_ecpm'] = round((spots_30s * row_30s['midas_cost_row'] / (spots_30s * row_30s['equiv_va_imps'])) * 1000, 2) if row_30s['equiv_va_imps'] > 0 else 0
            multiplied_rows.append(row_30s)
            
        # Create 60s row (impressions x0.5)
        if spots_60s > 0:
            row_60s = row.copy()
            row_60s['num_buys'] = spots_60s
            row_60s['length'] = ':60'
            # Original impressions stay same, equivalized are halved
            row_60s['equiv_va_imps'] = row['videoamp_imps'] * 2.0
            row_60s['equiv_nielsen_imps'] = row['nielsen_imps'] * 2.0
            row_60s['Age-Gender Imps'] = row['nielsen_imps']  
            row_60s['Equiv Age-Gender Imps'] = row['nielsen_imps'] * 2.0
            row_60s['midas_cost_row'] = row['midas_cost_row'] * 2.0
            row_60s['equiv_ecpm'] = round((spots_60s * row_60s['midas_cost_row'] / (spots_60s * row_60s['equiv_va_imps'])) * 1000, 2) if row_60s['equiv_va_imps'] > 0 else 0
            multiplied_rows.append(row_60s)

         # Create 75s row (impressions x0.4)
        if spots_75s > 0:
            row_75s = row.copy()
            row_75s['num_buys'] = spots_75s
            row_75s['length'] = ':75'
            # Original impressions stay same, equivalized are divided by 2.5
            row_75s['equiv_va_imps'] = row['videoamp_imps'] * 2.5
            row_75s['equiv_nielsen_imps'] = row['nielsen_imps'] * 2.5
            row_75s['Age-Gender Imps'] = row['nielsen_imps']
            row_75s['Equiv Age-Gender Imps'] = row['nielsen_imps'] * 2.5
            row_75s['midas_cost_row'] = row['midas_cost_row'] * 2.5
            row_75s['equiv_ecpm'] = round((spots_75s * row_75s['midas_cost_row'] / (spots_75s * row_75s['equiv_va_imps'])) * 1000, 2) if row_75s['equiv_va_imps'] > 0 else 0
            multiplied_rows.append(row_75s)   
            
        # Create 90s row (impressions x0.33)
        if spots_90s > 0:
            row_90s = row.copy()
            row_90s['num_buys'] = spots_90s
            row_90s['length'] = ':90'
            # Original impressions stay same, equivalized are divided by 3
            row_90s['equiv_va_imps'] = row['videoamp_imps'] * 3.0
            row_90s['equiv_nielsen_imps'] = row['nielsen_imps'] * 3.0
            row_90s['Age-Gender Imps'] = row['nielsen_imps']  
            row_90s['Equiv Age-Gender Imps'] = row['nielsen_imps'] * 3.0
            row_90s['midas_cost_row'] = row['midas_cost_row'] * 3.0
            row_90s['equiv_ecpm'] = round((spots_90s * row_90s['midas_cost_row'] / (spots_90s * row_90s['equiv_va_imps'])) * 1000, 2) if row_90s['equiv_va_imps'] > 0 else 0
            multiplied_rows.append(row_90s)
    
    result_df = pd.DataFrame(multiplied_rows)
    
    # Rename midas_cost_row to Total Cost for consistency with headers and CSV export
    if 'midas_cost_row' in result_df.columns:
        result_df = result_df.rename(columns={'midas_cost_row': 'Total Cost'})
    
    # Reset index to avoid duplicate index issues
    result_df = result_df.reset_index(drop=True)
    
    return result_df




# @app.route('/do_math', methods=['POST'])
# def return_ranker():
#     ranker = ranker_main(request.json, client, session)
#     if 'error' in ranker.keys():
#         return jsonify(ranker)
#     else:
        
#         # Organize df1 to show networks with buys first, and in alphabetical order  
#         used_cols = ['network', 'daypart', 'daypart_type', 'num_buys', 'length', 'midas_cpm', 'ecpm', 'videoamp_imps', 'unequiv_va_imps_total', 'equiv_va_imps', 'equiv_va_imps_total', 'equiv_ecpm', 'Age-Gender Imps', 'unequiv_age_gender_imps_total', 'Equiv Age-Gender Imps', 'equiv_age_gender_imps_total', 'Total Cost', 'total_cost']
#         df1 = ranker['success']
#         df_backup = ranker['backup']  # Add this line to extract backup data

#         # CHANGE 1: Apply 12% reduction to VideoAmp impressions
#         df1['videoamp_imps'] = df1['videoamp_imps'] * 0.88

#         # NEW: Apply equivalized spot logic - multiply rows by spot lengths
#         # NEW: Apply equivalized spot logic - multiply rows by spot lengths
#         df1 = apply_equivalized_spots(df1, request.json)

#         # Ensure clean index after spot transformation
#         df1 = df1.reset_index(drop=True)

#         # Create custom length sorting order
#         length_order = {':15': 1, ':30': 2, ':60': 3, ':75': 4, ':90': 5}

#         # Add temporary sorting column for custom length order
#         df1['length_sort_order'] = df1['length'].map(length_order).fillna(999)

#         # Multi-level sorting: Network → Daypart → Daypart Type → Length (custom order)
#         non_nan_df = df1[df1['num_buys'].notna()].sort_values(
#             by=['network', 'daypart', 'daypart_type', 'length_sort_order'], 
#             ascending=[True, True, True, True]
#         ).reset_index(drop=True)

#         nan_df = df1[df1['num_buys'].isna()].sort_values(
#             by=['network', 'daypart', 'daypart_type', 'length_sort_order'], 
#             ascending=[True, True, True, True]
#         ).reset_index(drop=True)

#         # Combine and drop the temporary sorting column
#         sorted_df1 = pd.concat([non_nan_df, nan_df], ignore_index=True)
#         sorted_df1 = sorted_df1.drop('length_sort_order', axis=1)

#         # Update df1 to use the sorted version
#         df1 = sorted_df1

#          # Calculate Unequiv VA Imps (Total) = videoamp_imps * num_buys
#         df1['unequiv_va_imps_total'] = df1['videoamp_imps'] * df1['num_buys']
#         df1['equiv_va_imps_total'] = df1['equiv_va_imps'] * df1['num_buys']
#         df1['unequiv_age_gender_imps_total'] = df1['Age-Gender Imps'] * df1['num_buys']
#         df1['equiv_age_gender_imps_total'] = df1['Equiv Age-Gender Imps'] * df1['num_buys']
#         df1['total_cost'] = df1['Total Cost'] * df1['num_buys']

#         # Select columns and reset index again to be safe
#         df1 = df1[used_cols].reset_index(drop=True)

#         # Recalculate non_nan_df after column selection to ensure alignment
#         non_nan_df = df1[df1['num_buys'].notna()].reset_index(drop=True)

#         # Extract values manually to avoid pandas alignment issues
#         total_cost_values = []
#         num_buys_values = []
#         va_imps_values = []
#         age_gender_imps_values = []
#         ecpm_values = []

#         # Manually extract and clean each row
#         for idx, row in non_nan_df.iterrows():
#             try:
#                 # Convert each value to float, default to 0 if conversion fails
#                 num_buys = float(str(row['num_buys']).replace(',', '')) if pd.notna(row['num_buys']) else 0
#                 total_cost = float(str(row['Total Cost']).replace(',', '').replace('$', '')) if pd.notna(row['Total Cost']) else 0
#                 va_imps = float(str(row['videoamp_imps']).replace(',', '')) if pd.notna(row['videoamp_imps']) else 0
#                 age_gender_imps = float(str(row['Age-Gender Imps']).replace(',', '')) if pd.notna(row['Age-Gender Imps']) else 0
#                 ecpm = float(str(row['ecpm']).replace(',', '')) if pd.notna(row['ecpm']) else 0
                
#                 num_buys_values.append(num_buys)
#                 total_cost_values.append(total_cost)
#                 va_imps_values.append(va_imps)
#                 age_gender_imps_values.append(age_gender_imps)
#                 ecpm_values.append(ecpm)
                
#             except Exception as e:
#                 print(f"Error processing row {idx}: {e}")
#                 # Default to 0 if there's any error
#                 num_buys_values.append(0)
#                 total_cost_values.append(0)
#                 va_imps_values.append(0)
#                 age_gender_imps_values.append(0)
#                 ecpm_values.append(0)

#         # Calculate aggregates 
#         agg_daypart_buys = int(round(sum(num_buys_values), 0))

#         agg_va_imps = '{:,}'.format(
#             int(round(sum(va * buys for va, buys in zip(va_imps_values, num_buys_values)), 0))
#         )

#         agg_nielsen_imps = '{:,}'.format(
#             int(round(sum(age * buys for age, buys in zip(age_gender_imps_values, num_buys_values)), 0))
#         )

#         agg_cost = '{:,}'.format(
#             int(round(sum(cost * buys for cost, buys in zip(total_cost_values, num_buys_values)), 0))
#         )

#         # Calculate Scheduler Output CPM and Client Facing CPM
#         total_cost_raw = sum(cost * buys for cost, buys in zip(total_cost_values, num_buys_values))
#         total_va_imps_raw = sum(va * buys for va, buys in zip(va_imps_values, num_buys_values))

#         # Scheduler Output CPM = (Total Cost / Total VideoAmp Impressions) * 1000
#         scheduler_output_cpm = (total_cost_raw / total_va_imps_raw * 1000) if total_va_imps_raw > 0 else 0

#         # Client Facing CPM = (Client Budget * Scheduler Output CPM) / Final Net Media Budget  
#         original_client_budget = float(request.json.get('original_client_budget', 0))
#         final_net_media_budget = float(request.json.get('final_net_media_budget', 0))
#         client_facing_cpm = (original_client_budget * scheduler_output_cpm / final_net_media_budget) if final_net_media_budget > 0 else 0

#         # Format for display
#         scheduler_output_cpm_formatted = f"{scheduler_output_cpm:.2f}"
#         client_facing_cpm_formatted = f"{client_facing_cpm:.2f}"

#         # Calculate relative eCPM sum
#         relative_ecpm_sum = sum(ecpm * buys for ecpm, buys in zip(ecpm_values, num_buys_values))

#         try:
#             agg_ecpm = round(relative_ecpm_sum / agg_daypart_buys, 2) if agg_daypart_buys > 0 else 0
#             agg_daypart_buys = '{:,}'.format(agg_daypart_buys)
#         except:
#             agg_ecpm = 0
#             agg_daypart_buys = '0'

#         # Programmatic data TBD
#         df2 = pd.DataFrame()
#         # Initialize backup table HTML
#     table_html_backup = ""
    
#     # Process backup networks if they exist
#     # Process backup networks if they exist
#     if not df_backup.empty:
#         # Apply same 12% VA reduction to backup networks
#         df_backup['videoamp_imps'] = df_backup['videoamp_imps'] * 0.88
        
#             # Add default columns for backup networks (they don't get equivalized spots)
#         # Add default columns for backup networks (they don't get equivalized spots)
#         df_backup['length'] = ':30'
#         df_backup['equiv_va_imps'] = df_backup['videoamp_imps']
#         df_backup['equiv_ecpm'] = df_backup['ecpm']
#         df_backup['Age-Gender Imps'] = df_backup['nielsen_imps']
#         df_backup['Equiv Age-Gender Imps'] = df_backup['nielsen_imps']
#         df_backup['Total Cost'] = df_backup['midas_cost_row']
        
#         # NOW calculate all totals (after all base columns exist)
#         df_backup['unequiv_va_imps_total'] = df_backup['videoamp_imps'] * df_backup['num_buys']
#         df_backup['equiv_va_imps_total'] = df_backup['equiv_va_imps'] * df_backup['num_buys']
#         df_backup['unequiv_age_gender_imps_total'] = df_backup['Age-Gender Imps'] * df_backup['num_buys']
#         df_backup['equiv_age_gender_imps_total'] = df_backup['Equiv Age-Gender Imps'] * df_backup['num_buys']
#         df_backup['total_cost'] = df_backup['Total Cost'] * df_backup['num_buys']

#         # Apply same sorting logic to backup networks
#         length_order = {':15': 1, ':30': 2, ':60': 3, ':75': 4, ':90': 5}
#         df_backup['length_sort_order'] = df_backup['length'].map(length_order).fillna(999)
        
#         # Sort backup networks
#         sorted_backup_df = df_backup.sort_values(
#             by=['network', 'daypart', 'daypart_type', 'length_sort_order'], 
#             ascending=[True, True, True, True]
#         ).reset_index(drop=True)
        
#         df_backup = sorted_backup_df.drop('length_sort_order', axis=1)[used_cols].reset_index(drop=True)
#         table_html_backup = create_table_html(df_backup)

#     # Generate backup section HTML separately  
#     backup_section_html = ""
#     if table_html_backup:
#         backup_section_html = f'''
#     <div id="backup-networks-section" class="mt-5">
#         <h3>Alternative Networks (If Primary Unavailable)</h3>
#         <p class="text-muted">These networks represent additional options if primary networks become unavailable. Quantities shown are for individual network reference.</p>
#         <div class="table-scroll-wrapper"  id="backup-table-container">
#             {table_html_backup}
#         </div>
#     </div>
#     '''
#     filter_values = 0
#     if filter_values != 0:
#         for key, val in filter_values.items():
#             df2 = df2.loc[df2[key] == val]
#             if len(df2) == 0:
#                 table_html2 = '<h4>No results found for the provided filters <h4>'
#     else:
#         table_html2 = create_table_html(df2)

#     table_html1 = create_table_html(df1)
#     table_html2 = create_table_html(df2)
    
#     headers = ["Network", "Daypart", "Daypart Type", "Number of spots", "Length", "CPM", "eCPM", "Unequiv VA Imps (Unit)", "Unequiv VA Imps (Total)", "Equiv VA Imps (Unit)", "Equiv VA Imps (Total)", "Equiv eCPM", "Unequiv Age-Gender Imps (Unit)", "Unequiv Age-Gender Imps (Total)", "Equiv Age-Gender Imps (Unit)", "Equiv Age-Gender Imps (Total)", "Unit Cost", "Total Cost"]
#     form_html = f'''
#         <form id="campaignForm" class="p-4 rounded">
#             <h2>Ranker Results</h2><br>
#             <p> Aggregate eCPM: <b>{agg_ecpm}</b> | Total Nielsen Imps <b>{agg_nielsen_imps}</b> | Total VA Imps: <b>{agg_va_imps}</b> | Total number of spots: <b>{agg_daypart_buys}</b> | Total Cost: <b>${agg_cost}</b> </p>
#             <p> Scheduler Output CPM: <b>${scheduler_output_cpm_formatted}</b> | Client Facing CPM: <b>${client_facing_cpm_formatted}</b> </p>
#                 <p>Please note that any changes made to the rows will NOT be saved when you click "Download Results". The ability to edit cells is provided for users to resubmit to the ranker with modified CPMs, impressions, etc.</p>
#                 <h6 class = "btn btn-outline-secondary rounded-pill px-3 py-2 right-align button-custom">Page <span class="currentPageCounter">nil</span> / <span class="totalPageCounter">nil</span></h6>
#             <div id="table-container">
#                 {table_html1}
#             </div>
#             <div id="table-container-tab2" style="display: none;">
#                 {table_html2}
#             </div>
#             <div id="pagination-controls" class="mb-3 d-flex justify-content-between">
#                 <button type="button" id="prev-page" class="btn btn-secondary btn-sm" onclick="prevPage()">Previous</button>
#                 <button type="button" id="next-page" class="btn btn-secondary btn-sm" onclick="nextPage()">Next</button>
#                 <button type="button" id="switch-tab" class="btn btn-secondary btn-sm" onclick="switchTab()">Switch Tab</button>
#                 <button type="button" id="download-results" class="btn btn-secondary btn-sm" onclick="downloadResults()">Download Results</button>
#             </div><br>

#             <!-- Backup Networks Button -->
#             <div class="mb-3">
#                 <button type="button" class="btn btn-info" onclick="viewBackupNetworks()">View Backup Networks</button>
#             </div><br>
#             {backup_section_html}
#             <div id="save" class = "mt-4">
#             <h3>Save Scheduler</h3>
#                 <p>Save any changes to the number of spots or changes to the Nielsen/VideoAmp/CPM.</p>
#                 <div class="form-group">
#                         <label for="scheduler_name"><b>Scheduler Name:</b></label>
#                         <input type="text" id="scheduler_name" name="scheduler_name" class="form-control">
#                 </div>
#                 <p class = 'save_results' id = 'save_results'></p>
#             <button type="button" class="btn btn-primary" onclick="saveScheduler()">Save scheduler</button>
#             </div>
#             <div id="filter" class="mt-4">
#                 <h3>Filter</h3>
#                 <p>Filter on program level data to find specific dayparts to add to the final ranker.</p>
#                 <table id="filter-table" class="table table-bordered">
#                     <thead>
#                         <tr>{''.join(f'<th>{col}</th>' for col in headers)}</tr>
#                         {''.join(f'<div class="autocomplete"><td class = "autocomplete-cell"><input class="autocomplete-input" type="text" placeholder="Filter here"></td></div>' for _ in range(0, len(headers)))}</thead>
#                     <tbody></tbody>
#                 </table>
#                 <button type="button" id="filter-rows" class="btn btn-secondary btn-sm" onclick="filterRows()">Filter</button>
#             </div>
#             <div id="toadd" class="mt-4">
#                 <h3>Add/Edit Dayparts</h3>
#                 <p> When adding a daypart, you can either specify the number of buys or leave as "auto", and the algorithm will add in the number of dayparts dynamically. It is only recommended to be adding Prime dayparts if it is the only daypart you seek to include from a network. If you want to add dayparts from another network and satisfy the minimum prime spend constraint, do not add a Prime daypart. The algorithm will satisfy this constraint automatically when you add a non-prime daypart. </p>
#                 <table id="add-table" class="table table-bordered">
#                     <thead>
#                         <tr>{''.join(f'<th>{col}</th>' for col in headers)}<th>Action</th></tr>
#                     </thead>
#                     <tbody></tbody>
#                 </table>
#                 <button type="button" class="btn btn-success mt-2" onclick="addNewRow()">Add New Row</button>
#             </div>
#             <div id="toremove" class="mt-4">
#                 <h3>Remove Dayparts</h3>
#                 <p> You can add dayparts to this group even if they are not already in the solution set. I.E., if you want to remove ALL CNN dayparts, please filter by network and remove ALL of the CNN dayparts. This way the algorithm will know to not include any CNN dayparts, even if they were not in the previous solution.
#                 <table id="remove-table" class="table table-bordered">
#                     <thead>
#                         <tr>{''.join(f'<th>{col}</th>' for col in headers)}<th>Action</th></tr>
#                     </thead>
#                     <tbody></tbody>
#                 </table>
#             </div>
#             <br>
#                 <button type="button" class="btn btn-primary" onclick="ingestFormData()">Resubmit</button>
#         </form>
#     '''
#     # Render the form as HTML and remove newlines
#     return render_template_string(form_html.replace('\n', ''))

@app.route('/do_math', methods=['POST'])
def return_ranker():

    result = ranker_main(request.json, client, session)

    if 'error' in result:
        return jsonify(result), 400

    success_df = result['success']
    backup_df = result['backup']

    response = {
        "success": success_df.to_dict(orient="records"),
        "backup": backup_df.to_dict(orient="records") if not backup_df.empty else []
    }

    return jsonify(response)

@app.route("/download_ranker", methods=['POST'])
def download_ranker():
    data, budget, start_date, end_date, dark_weeks, load_scheduler = json.loads(request.json).values()
    dark_weeks = 0 if dark_weeks == '' else dark_weeks
    
    # Pull data from GCP if building from a loaded session
    if load_scheduler != '':
        r = load_dataset_from_gcp(client, schedule_name=load_scheduler)
        _, _, _, budget, start_date, end_date, dark_weeks, _ = r
        print("[+] downloading scheduler thru load")
    # CHANGE 2: Format budget with commas
    budget_formatted = '{:,}'.format(float(budget))
    header = f"DDL Ranker: Total Budget ${budget_formatted} | Flight Dates: {start_date} --> {end_date} | Total Weeks: {get_weeks(start_date, end_date)} | Dark Weeks: {dark_weeks}"



    # Convert data, add/remove keys dataframes to CSV, dropping Action column and rearranging column layout
    desired_order = [
    'Network',
    'Daypart',
    'Daypart Type',
    'Number of spots',
    'Length',
    'CPM',
    'eCPM',
    'Unequiv VA Imps (Unit)',
    'Unequiv VA Imps (Total)',
    'Equiv VA Imps (Unit)',
    'Equiv VA Imps (Total)',
    'Equiv eCPM',
    'Unequiv Age-Gender Imps (Unit)',
    'Unequiv Age-Gender Imps (Total)',
    'Equiv Age-Gender Imps (Unit)',
    'Equiv Age-Gender Imps (Total)',
    'Unit Cost',
    'Total Cost'
    ]
        # CHANGE 2: Create copies of dataframes to avoid SettingWithCopyWarning
    df = pd.DataFrame(data).drop(['Action'], axis=1).copy()


    add_keys_df = pd.DataFrame.from_dict(session['add_keys']).transpose().copy() if 'add_keys' in session else pd.DataFrame()
    remove_keys_df = pd.DataFrame.from_dict(session['remove_keys']).transpose().copy() if 'remove_keys' in session else pd.DataFrame()

    # CHANGE 2: Format numeric columns with commas
    # CHANGE 2: Format numeric columns with commas
    for col in df.columns:
        if col in ['Unequiv Age-Gender Imps (Unit)', 'Unequiv VA Imps (Unit)', 'Unequiv VA Imps (Total)', 'Equiv VA Imps (Unit)', 'Equiv VA Imps (Total)', 'Unequiv Age-Gender Imps (Total)', 'Equiv Age-Gender Imps (Unit)', 'Equiv Age-Gender Imps (Total)']:
            # Convert to numeric first (handling potential existing commas)
            df[col] = df[col].astype(str).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # Then format with commas (integers)
            df[col] = df[col].apply(lambda x: '{:,}'.format(int(x)) if pd.notnull(x) else '')
        elif col in ['Unit Cost', 'Total Cost', 'Daypart Cost']:
            # Convert to numeric first (handling potential existing commas and dollar signs)
            df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.replace('$', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # Then format with commas but keep decimals
            df[col] = df[col].apply(lambda x: '{:,.2f}'.format(x) if pd.notnull(x) else '')
    # Write headers and data
    csv_buffer = io.StringIO()
    csv_buffer.write(header + '\n\n')  # give 2 linebreaks below header for spacing
    df.to_csv(csv_buffer, index=False)
    if len(add_keys_df) >= 1:
        csv_buffer.write("\n\nAdd Keys: \n")
        add_keys_df[desired_order].to_csv(csv_buffer, index=False)
    if len(remove_keys_df) >= 1:
        csv_buffer.write("\n\nRemove Keys: \n")
        remove_keys_df[desired_order].to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    # Create a response
    response = make_response(csv_buffer.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=ranker_{start_date}_to_{end_date}.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@app.route('/save_scheduler', methods=['POST'])
def save_scheduler():
    bundle = validate_form_params(request.json)
    # Extract budget calculator inputs if present
    calculator_inputs = {}
    if 'client_budget' in request.json:
        calculator_inputs = {
            'client_budget': request.json.get('client_budget', 0),
            'cmp_data_costs': request.json.get('cpm_data_costs', 0),
            'flat_data_costs': request.json.get('flat_data_costs', 0)
        }
        # Store in session for scheduler saving
        session['calculator_inputs'] = calculator_inputs
        session.modified = True
    if 'error' in bundle.keys():
        return bundle
    print("[+] saving scheduler...")
    try:
        table1_vals, _, _, budget, start_date, end_date, dark_weeks, selected_dataset, scheduler_name = bundle.values()
    except ValueError as e:
        # means we're using a scheduler already and want to update
        _, _, _, _, _, _, _, _, scheduler_name, old_scheduler_name = bundle.values()
        
        # load in scheduler vals (inefficient, can save to session keys eventually)
        r = load_dataset_from_gcp(client, schedule_name=old_scheduler_name)
        table1_vals, _, _, budget, start_date, end_date, dark_weeks, selected_dataset = r
    except Exception as e:
        return {"error": f"failed to save scheduler -- {str(e)}"}
    response = upload_scheduler(client, table1_vals, float(budget), start_date, end_date, dark_weeks, selected_dataset, scheduler_name, session)    
    return response

# @app.route('/display-csvs', methods=['POST'])
# def display_csvs():
#     tables = client.list_tables(f'{config["PROJECT_ID"]}.{config["DATASET_ID"]}')
#     return [table.table_id for table in tables if 'videoamp' in table.table_id]

@app.route('/api/display-csvs', methods=['POST'])
def api_display_csvs():
    if client is None:
        return jsonify({"error": "BigQuery client not configured locally"}), 500
    try:
        tables = client.list_tables(f'{config["PROJECT_ID"]}.{config["DATASET_ID"]}')
        result = [table.table_id for table in tables if 'videoamp' in table.table_id]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/actualize-plan', methods=['GET'])
# def actualize_plan():
#     return render_template('actualize.html')

@app.route('/api/actualize-plan', methods=['GET'])
def api_actualize_plan():
    return jsonify({'message': 'Actualize plan page data'})


@app.route('/process-two-step-actuals', methods=['POST'])
def process_two_step_actuals():
    try:
        print("Two-step actuals processing started")
        
        # Check if both files were uploaded
        if 'originalFile' not in request.files or 'modifiedFile' not in request.files:
            return jsonify({'error': 'Both original and modified files are required'}), 400
        
        original_file = request.files['originalFile']
        modified_file = request.files['modifiedFile']
        
        if original_file.filename == '' or modified_file.filename == '':
            return jsonify({'error': 'Both files must be selected'}), 400

        # Read both files with better error handling
        print("Reading original file...")
        try:
            if original_file.filename.endswith('.csv'):
                original_df = pd.read_csv(original_file, skiprows=3, header=None)
            elif original_file.filename.endswith(('.xlsx', '.xls')):
                original_df = pd.read_excel(original_file, skiprows=3, header=None)
            else:
                return jsonify({'error': 'Original file must be Excel or CSV format'}), 400
        except Exception as e:
            print(f"Error reading original file: {str(e)}")
            return jsonify({'error': f'Error reading original file: {str(e)}'}), 400

        print("Reading modified file...")
        try:
            if modified_file.filename.endswith('.csv'):
                modified_df = pd.read_csv(modified_file, skiprows=3, header=None)
            elif modified_file.filename.endswith(('.xlsx', '.xls')):
                modified_df = pd.read_excel(modified_file, skiprows=3, header=None)
            else:
                return jsonify({'error': 'Modified file must be Excel or CSV format'}), 400
        except Exception as e:
            print(f"Error reading modified file: {str(e)}")
            return jsonify({'error': f'Error reading modified file: {str(e)}'}), 400

        print(f"Raw file shapes - Original: {original_df.shape}, Modified: {modified_df.shape}")

        # Clean both dataframes
        original_df = clean_dataframe(original_df)
        modified_df = clean_dataframe(modified_df)

        print(f"After cleaning - Original: {original_df.shape}, Modified: {modified_df.shape}")

        # Process using comparison logic
        actualized_df = compare_and_recalculate(original_df, modified_df)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            actualized_df.to_excel(writer, index=False, sheet_name='Actualized Results')
            
        output.seek(0)
        
        # Return the Excel file
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=actualized_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response

    except Exception as e:
        print(f"Error in two-step actuals processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error processing files: {str(e)}'}), 500

def clean_dataframe(df):
    """Clean and filter dataframe to remove empty rows"""
    print(f"Before cleaning: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"First few rows:\n{df.head(3).to_string()}")
    
    # Set expected column headers manually (since skiprows=3 might not have headers)
    expected_columns = [
        'Network', 'Daypart', 'Daypart Type', 'Number of spots', 'Length', 
        'CPM', 'eCPM', 'Unequiv VA Imps (Unit)', 'Equiv VA Imps (Unit)', 'Equiv eCPM', 
        'Unequiv Age-Gender Imps (Unit)', 'Equiv Age-Gender Imps (Unit)', 'Total Cost'
    ]
    
    # If we have the right number of columns but wrong names, fix them
    if len(df.columns) == len(expected_columns):
        print("Setting column names manually")
        df.columns = expected_columns
    
    print(f"After column fix: {list(df.columns)}")
    
    # Remove rows where Network is truly empty/invalid
    print(f"Network column sample values: {df['Network'].head().tolist()}")
    
    original_count = len(df)
    
    # More lenient filtering - only remove truly empty rows
    df = df.dropna(subset=['Network'])  # Remove NaN
    df = df[df['Network'].astype(str).str.strip() != '']  # Remove empty strings
    df = df[df['Network'].astype(str).str.strip() != 'nan']  # Remove 'nan' strings
    df = df[~df['Network'].astype(str).str.strip().str.match(r'^0+$')]  # Remove '0', '00', etc.
    
    # Reset index
    df = df.reset_index(drop=True)
    
    print(f"Rows removed: {original_count - len(df)}")
    print(f"After cleaning: {df.shape}")
    
    if len(df) > 0:
        print(f"Sample data after cleaning:\n{df.head(2).to_string()}")
    else:
        print("WARNING: All rows were removed during cleaning!")
    
    return df

def compare_and_recalculate(original_df, modified_df):
    """Compare original vs modified files and recalculate based on changes using Prime logic"""
    try:
        print("Starting comparison and recalculation with Prime daypart logic")
        
        # Convert numeric columns first
        numeric_columns = ['Number of spots', 'CPM', 'eCPM', 'Unequiv VA Imps (Unit)', 'Equiv VA Imps (Unit)', 'Unequiv Age-Gender Imps (Unit)', 'Equiv Age-Gender Imps (Unit)', 'Total Cost']
        
        for col in numeric_columns:
            if col in original_df.columns:
                original_df[col] = pd.to_numeric(original_df[col].astype(str).str.replace(',', '').str.replace('$', ''), errors='coerce').fillna(0)
            if col in modified_df.columns:
                modified_df[col] = pd.to_numeric(modified_df[col].astype(str).str.replace(',', '').str.replace('$', ''), errors='coerce').fillna(0)

        # Create matching keys for both dataframes
        original_df['match_key'] = (original_df['Network'].astype(str) + '|' + 
                                   original_df['Daypart'].astype(str) + '|' + 
                                   original_df['Daypart Type'].astype(str) + '|' + 
                                   original_df['Length'].astype(str))
        
        modified_df['match_key'] = (modified_df['Network'].astype(str) + '|' + 
                                   modified_df['Daypart'].astype(str) + '|' + 
                                   modified_df['Daypart Type'].astype(str) + '|' + 
                                   modified_df['Length'].astype(str))
        
        print(f"Original matches: {len(original_df)}, Modified matches: {len(modified_df)}")

        # Length multipliers
        length_multipliers = {
            ':15': 0.5,
            ':30': 1.0,
            ':60': 2.0,
            ':75': 2.5,
            ':90': 3.0
        }

        # First pass: Build prime_daypart_vals dictionary (identify prime dayparts per network)
        prime_daypart_vals = {}
        
        for idx, row in original_df.iterrows():
            daypart_type = str(row['Daypart Type']).lower()
            if 'prime' in daypart_type:
                network = row['Network']
                cpm = float(row['CPM'])
                original_age_gender = float(row['Unequiv Age-Gender Imps (Unit)'])
                original_va_imps = float(row['Unequiv VA Imps (Unit)'])
                
                # Prime daypart cost calculation (doubled as per ranker.py)
                midas_cost = (original_age_gender * cpm / 1000) * 2
                
                # Store prime values per network
                prime_daypart_vals[network] = {
                    'midas_cost': midas_cost,
                    'prime_impressions': original_va_imps,
                    'daypart': row['Daypart']
                }
                
                print(f"Prime daypart found: {network} - {row['Daypart']}, midas_cost: {midas_cost:.2f}")

        result_rows = []
        matches_found = 0
        
        # Second pass: Process each modified row
        for idx, modified_row in modified_df.iterrows():
            try:
                match_key = modified_row['match_key']
                original_match = original_df[original_df['match_key'] == match_key]
                
                if original_match.empty:
                    print(f"Warning: No match found for {match_key}")
                    continue
                    
                original_row = original_match.iloc[0]
                matches_found += 1
                
                # Get values
                original_age_gender = float(original_row['Unequiv Age-Gender Imps (Unit)'])
                modified_age_gender = float(modified_row['Unequiv Age-Gender Imps (Unit)'])
                original_va_imps = float(original_row['Unequiv VA Imps (Unit)'])
                original_num_spots = float(original_row['Number of spots'])
                modified_num_spots = float(modified_row['Number of spots'])
                cpm = float(original_row['CPM'])
                network = original_row['Network']
                daypart_type = str(original_row['Daypart Type']).lower()
                
                # Calculate Nielsen change ratio
                nielsen_ratio = (modified_age_gender / original_age_gender) if original_age_gender > 0 else 1.0
                
                # Recalculate VA Imps proportionally
                new_va_imps = original_va_imps * nielsen_ratio
                
                # Apply 75% cap
                if new_va_imps > modified_age_gender * 0.75:
                    new_va_imps = modified_age_gender * 0.75
                
                # Create result row (copy original and update specific fields)
                result_row = original_row.copy()
                
                # Update user inputs
                result_row['Number of spots'] = modified_num_spots
                result_row['Unequiv Age-Gender Imps (Unit)'] = modified_age_gender
                result_row['Unequiv VA Imps (Unit)'] = round(new_va_imps, 0)
                
                # Get length and multiplier
                length = str(result_row['Length'])
                multiplier = length_multipliers.get(length, 1.0)
                
                # Calculate equivalized values
                equiv_va_imps = round(new_va_imps * multiplier, 0)
                equiv_age_gender = round(modified_age_gender * multiplier, 0)
                
                result_row['Equiv VA Imps (Unit)'] = equiv_va_imps
                result_row['Equiv Age-Gender Imps (Unit)'] = equiv_age_gender
                
                # Determine if this daypart requires prime logic
                is_prime = 'prime' in daypart_type
                network_has_prime = network in prime_daypart_vals
                
                # COST CALCULATION using Equiv Age-Gender Imps
                if is_prime and network_has_prime:
                    # Prime daypart cost calculation (from ranker.py lines 389-424)
                    midas_cost = (equiv_age_gender * cpm / 1000)
                    
                    # Get prime daypart values
                    prime_value = prime_daypart_vals[network]['midas_cost']
                    prime_impressions = prime_daypart_vals[network]['prime_impressions']
                    
                    # Calculate num_buys_relative_to_prime_daypart
                    num_buys_relative = round(prime_value / midas_cost) if midas_cost > 0 else 1
                    if num_buys_relative == 0:
                        num_buys_relative = 1
                    
                    # Calculate final costs
                    va_imps_calc = new_va_imps * num_buys_relative
                    prime_cost = prime_value / 2
                    midas_cost_final = midas_cost * num_buys_relative
                    total_cost = midas_cost_final + prime_cost
                    total_va_imps = va_imps_calc + prime_impressions
                    
                    # Calculate Equiv eCPM for Prime
                    equiv_ecpm = round(((total_cost / total_va_imps) * 1000), 2) if total_va_imps > 0 else 0
                    
                    result_row['Total Cost'] = round(total_cost, 2)
                    result_row['Equiv eCPM'] = equiv_ecpm
                    
                    print(f"Prime calc: {network} - Cost: {total_cost:.2f}, Equiv eCPM: {equiv_ecpm:.2f}")
                    
                elif network_has_prime and not is_prime:
                    # Non-prime daypart on network with prime requirements
                    midas_cost = (equiv_age_gender * cpm / 1000)
                    
                    prime_value = prime_daypart_vals[network]['midas_cost']
                    prime_impressions = prime_daypart_vals[network]['prime_impressions']
                    
                    num_buys_relative = round(prime_value / midas_cost) if midas_cost > 0 else 1
                    if num_buys_relative == 0:
                        num_buys_relative = 1
                    
                    # Calculate costs
                    va_imps_calc = new_va_imps * num_buys_relative
                    prime_cost = prime_value / 2
                    midas_cost_final = midas_cost * num_buys_relative
                    total_cost = midas_cost_final + prime_cost
                    total_va_imps = va_imps_calc + prime_impressions
                    
                    # Calculate Equiv eCPM
                    equiv_ecpm = round(((total_cost / total_va_imps) * 1000), 2) if total_va_imps > 0 else 0
                    
                    result_row['Total Cost'] = round(total_cost, 2)
                    result_row['Equiv eCPM'] = equiv_ecpm
                    
                    print(f"Non-prime with prime network: {network} - Cost: {total_cost:.2f}, Equiv eCPM: {equiv_ecpm:.2f}")
                    
                else:
                    # Simple calculation for networks without prime requirements
                    # Cost based on Equiv Age-Gender Imps
                    total_cost = (equiv_age_gender * cpm / 1000)
                    
                    # Simple Equiv eCPM calculation
                    equiv_ecpm = round((cpm * equiv_age_gender / equiv_va_imps), 2) if equiv_va_imps > 0 else 0
                    
                    result_row['Total Cost'] = round(total_cost, 2)
                    result_row['Equiv eCPM'] = equiv_ecpm
                    
                    print(f"Non-prime network: {network} - Cost: {total_cost:.2f}, Equiv eCPM: {equiv_ecpm:.2f}")
                
                result_rows.append(result_row)
                
            except Exception as e:
                print(f"Error processing row {idx}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"Matches found: {matches_found}")
        
        if not result_rows:
            raise Exception("No matching dayparts found between original and modified files")
        
        # Create result dataframe and remove match_key column
        result_df = pd.DataFrame(result_rows)
        if 'match_key' in result_df.columns:
            result_df = result_df.drop('match_key', axis=1)
        
        print(f"Recalculation completed. Result: {len(result_df)} rows")
        return result_df
        
    except Exception as e:
        print(f"Error in compare_and_recalculate: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e

# @app.route('/backup-networks', methods=['GET'])
# def backup_networks():
#     return render_template('backup.html')

@app.route('/api/backup-networks', methods=['GET'])
def api_backup_networks():
    return jsonify({'message': 'Backup networks page data'})

@app.route('/generate_backup_networks', methods=['POST'])
def generate_backup_networks():
    """Generate backup networks by excluding primary networks and re-running ranker"""
    try:
        # Run ranker with excluded networks
        backup_ranker = ranker_main(request.json, client, session)
        
        if 'error' in backup_ranker.keys():
            return render_template_string(f'''
                <div class="container mt-4">
                    <h2>Backup Networks</h2>
                    <div class="alert alert-danger">
                        <strong>Error:</strong> {backup_ranker['error']}
                    </div>
                    <a href="/plan" class="btn btn-secondary">Back to Primary Results</a>
                </div>
            ''')
        
        # Process backup results same as primary
        used_cols = ['network', 'daypart', 'daypart_type', 'num_buys', 'length', 
    'midas_cpm', 'ecpm',
    'Unequiv VA Imps', 'Equiv VA Imps', 'equiv_ecpm',
    'Unequiv Age-Gender Imps', 'Equiv Age-Gender Imps',
    'Total VA Imps', 'Total Equiv VA Imps',
    'Total Age-Gender Imps', 'Total Equiv Age-Gender Imps',
    'Unit Cost', 'Total Cost']
        df_backup = backup_ranker['success']
        exclude_networks_set = set(request.json.get('exclude_networks', []))
        print(f"DEBUG: Filtering out excluded networks: {exclude_networks_set}")

        # Filter out excluded networks and create clean copy
        df_backup = df_backup[~df_backup['network'].isin(exclude_networks_set)].copy()
        print(f"DEBUG: Networks after filtering: {df_backup['network'].unique().tolist()}")

        # Ensure required columns exist before processing
        required_columns = ['network', 'daypart', 'daypart_type', 'num_buys', 'midas_cpm', 'ecpm', 'videoamp_imps', 'nielsen_imps', 'midas_cost_row']
        missing_columns = [col for col in required_columns if col not in df_backup.columns]

        if missing_columns:
            return render_template_string(f'''
                <div class="container mt-4">
                    <h2>Backup Networks</h2>
                    <div class="alert alert-danger">
                        <strong>Error:</strong> Missing required columns: {missing_columns}
                        <br>Available columns: {list(df_backup.columns)}
                    </div>
                    <a href="/plan" class="btn btn-secondary">Back to Primary Results</a>
                </div>
            ''')

        # Add required columns for equivalized spots processing
        if 'length' not in df_backup.columns:
            df_backup['length'] = ':30'

        # Apply same processing as primary
        df_backup['videoamp_imps'] = df_backup['videoamp_imps'] * 0.88

        # Show networks that received some allocation in the backup optimization (even small amounts)
        # These represent true alternatives that passed all business constraints
        backup_with_any_allocation = df_backup[df_backup['num_buys'] > 0].copy()

        if len(backup_with_any_allocation) == 0:
            # If no allocations, show the most efficient networks but with proper warning
            df_backup_sorted = df_backup.sort_values(['ecpm'])
            num_backup_networks = max(5, int(len(df_backup_sorted) * 0.25))  
            df_backup = df_backup_sorted.head(num_backup_networks)
            df_backup = df_backup.copy()
            df_backup['num_buys'] = 0
            warning_message = "Note: These networks did not receive allocations in backup optimization due to constraints."
        else:
            df_backup = backup_with_any_allocation
            warning_message = ""

        if 'length' not in df_backup.columns:
            df_backup['length'] = ':30'

        # Apply equivalized spot logic 
        df_backup = apply_equivalized_spots(df_backup, request.json)

        # Apply same sorting logic
        length_order = {':15': 1, ':30': 2, ':60': 3, ':75': 4, ':90': 5}
        df_backup['length_sort_order'] = df_backup['length'].map(length_order).fillna(999)
        
        non_nan_backup = df_backup[df_backup['num_buys'].notna()].sort_values(
            by=['network', 'daypart', 'daypart_type', 'length_sort_order'], 
            ascending=[True, True, True, True]
        ).reset_index(drop=True)
        
        nan_backup = df_backup[df_backup['num_buys'].isna()].sort_values(
            by=['network', 'daypart', 'daypart_type', 'length_sort_order'], 
            ascending=[True, True, True, True]
        ).reset_index(drop=True)
        
        sorted_backup = pd.concat([non_nan_backup, nan_backup], ignore_index=True)
        sorted_backup = sorted_backup.drop('length_sort_order', axis=1)
        df_backup = sorted_backup[used_cols].reset_index(drop=True)
        
        # Calculate aggregates for backup networks
        backup_with_buys = df_backup[df_backup['num_buys'].notna()].reset_index(drop=True)
        
        total_backup_spots = backup_with_buys['num_buys'].sum() if len(backup_with_buys) > 0 else 0
        total_backup_cost = (backup_with_buys['num_buys'] * backup_with_buys['Total Cost']).sum() if len(backup_with_buys) > 0 else 0
        
        # Create table HTML
        table_html = create_table_html(df_backup)
        
        return render_template_string(f'''
            <div class="container mt-4">
                <h2>Backup Networks</h2>
                <div class="alert alert-info">
                    <strong>Alternative Networks:</strong> These networks are optimized with the same efficiency ranking as primary networks, 
                    excluding networks already selected in your primary results.
                </div>
                <p><strong>Total Backup Spots:</strong> {total_backup_spots:,.0f} | <strong>Total Backup Cost:</strong> ${total_backup_cost:,.0f}</p>
                
                <div id="table-container">
                    {table_html}
                </div>
                
                <div class="mt-3">
                    <a href="/plan" class="btn btn-primary">Back to Primary Results</a>
                    <button onclick="downloadBackupResults()" class="btn btn-secondary">Download Backup Results</button>
                </div>
            </div>

            <script>
                function downloadBackupResults() {{
                    const table = document.querySelector('.main-table');
                    const data = [];
                    const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
                    
                    table.querySelectorAll('tbody tr').forEach(row => {{
                        const rowData = {{}};
                        Array.from(row.querySelectorAll('td')).forEach((cell, index) => {{
                            rowData[headers[index]] = cell.querySelector('input') ? cell.querySelector('input').value : cell.textContent.trim();
                        }});
                        data.push(rowData);
                    }});
                    
                    const csvContent = [
                        headers.join(','),
                        ...data.map(row => headers.map(header => `"${{row[header] || ''}}"`).join(','))
                    ].join('\\n');
                    
                    const blob = new Blob([csvContent], {{ type: 'text/csv' }});
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'backup_networks.csv';
                    a.click();
                    window.URL.revokeObjectURL(url);
                }}
            </script>
        ''')
        
    except Exception as e:
        return render_template_string(f'''
            <div class="container mt-4">
                <h2>Backup Networks</h2>
                <div class="alert alert-danger">
                    <strong>Error:</strong> {str(e)}
                </div>
                <a href="/plan" class="btn btn-secondary">Back to Primary Results</a>
            </div>
        ''')    

@app.before_request
def initialize_session():
    if 'add_keys' not in session:
        session['add_keys'] = {}
    if 'remove_keys' not in session:
        session['remove_keys'] = {}

if __name__ == '__main__':
    app.run()
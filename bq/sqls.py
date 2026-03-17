from google.api_core.exceptions import *
from google.cloud import bigquery
from flask import jsonify
import os, json

# load SQL modules, secrets
with open("module/config_prod.json", "r") as file:
    config = json.load(file)


def save_videoamp_as_table(client, root_dir, csv_file):
    try:
        print('Starting CSV upload...')

        # define project / schema
        
        project_id = config['PROJECT_ID']
        dataset_id = config["DATASET_ID"]
        schema = [
            bigquery.SchemaField("title_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("title_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("va_network", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("display_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("platform", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("daypart", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("cost_per_unit", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("impressions_per_unit", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("cpm", "FLOAT", mode="REQUIRED"),
        ]
        filename = str(csv_file).replace("<FileStorage: '", '').replace("' ('text/csv')>", '') # strip weurkzeug naming conventions
        new_table_id = f"videoamp_{filename.replace('.csv', '').replace('-', '_')}" # create name for table
        full_table_id = f"{project_id}.{dataset_id}.{new_table_id}"
        table_ref = client.dataset(dataset_id, project=project_id).table(new_table_id)

        # create table, define config, load table
        table = bigquery.Table(table_ref, schema=schema)
        print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
        csv_path = os.path.join(root_dir, f"csv/{filename}")
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            skip_leading_rows=1  
        )

        with open(csv_path, "rb") as source_file:
            job = client.load_table_from_file(source_file, table_ref, job_config=job_config)

        try:
            job.result()
            if job.errors != None:
                print('job.errors returned not None... meaning there was an error uploading csv :(')
                return jsonify({'error':f"Error in uploading CSV {csv_file} to BQ-- {job.errors}"})
            else:
                print(f"Loaded {job.output_rows} rows to {full_table_id}")
                return jsonify({"success": "All files were successfully uploaded!"})
        except BadRequest as e:
            return jsonify({'error':f"Error in uploading CSV {csv_file} to BQ. Check CSV is named correctly and there are no explicit strings or empty cells. Error: {str(e)}"})
    except Exception as e:
        print(f'Error in the code for CSV upload --> BQ. Check CSV format -- {str(e)}')
        return jsonify({'error':f'Error in the code for CSV upload --> BQ. Check CSV format -- {str(e)}'})


def create_table_html(df):
    import pandas as pd  # Add import at top if needed
    
    table_rows = []
    for _, row in df.iterrows():
        formatted_row = []
        for col_index, cell in enumerate(row):
            # Format numbers with commas for display
            if isinstance(cell, (int, float)) and not pd.isna(cell):
                # Handle different numeric column types appropriately
                if col_index in [3, 7, 8, 9, 10, 12, 13, 14, 15]:  # Number of spots, VA Imps, Equiv VA Imps, Nielsen Imps, Equiv Nielsen Imps - large integers
                    formatted_cell = '{:,}'.format(int(cell))
                elif col_index in [5, 6, 11]:  # CPM, eCPM, Equiv eCPM - 2 decimal places
                    formatted_cell = '{:.2f}'.format(float(cell))
                elif col_index in [16, 17]:  # Total Cost - currency
                    formatted_cell = '${:,.2f}'.format(float(cell))    
            else:
                formatted_cell = str(cell) if not pd.isna(cell) else ""
            
            formatted_row.append(f'<td><input type="text" class="form-control cell-{col_index}" value="{formatted_cell}" required></td>')
        
        action_buttons = (
            '<td>'
            '<button type="button" class="btn btn-success btn-sm" onclick="addToChange(this)">+</button>'
            '<button type="button" class="btn btn-danger btn-sm" onclick="removeFromChange(this)">-</button>'
            '</td>'
        )
        table_rows.append(f'<tr>{"".join(formatted_row)}{action_buttons}</tr>')
    
    # Map internal column names to display-friendly names
    column_display_names = {
        'network': 'Network',
        'daypart': 'Daypart', 
        'daypart_type': 'Daypart Type',
        'num_buys': 'Spots',
        'length': 'Length',
        'midas_cpm': 'CPM',
        'ecpm': 'eCPM',
        'videoamp_imps': 'Unequiv VA Imps (Unit)',
        'unequiv_va_imps_total': 'Unequiv VA Imps (Total)',
        'equiv_va_imps': 'Equiv VA Imps (Unit)',
        'equiv_va_imps_total': 'Equiv VA Imps (Total)',
        'equiv_ecpm': 'Equiv eCPM',
        'Age-Gender Imps': 'Unequiv Age-Gender Imps (Unit)',
        'unequiv_age_gender_imps_total': 'Unequiv Age-Gender Imps (Total)',
        'Equiv Age-Gender Imps': 'Equiv Age-Gender Imps (Unit)',
        'equiv_age_gender_imps_total': 'Equiv Age-Gender Imps (Total)',
        'Total Cost': 'Unit Cost',
        'total_cost': 'Total Cost'
    }

    header_html = ''.join(
        f"<th>{column_display_names.get(col, col)}</th>" for col in df.columns
    )

    
    # Add the Action column
    header_html += '<th>Action</th>'
    
    return f'<table id="main-table" class="table table-bordered main-table">' \
           f'<thead><tr>{header_html}</tr></thead>' \
           f'<tbody>{" ".join(table_rows)}</tbody></table>'

# Grab data from VA/Nielsen/Rate tables 
def get_combined_data(client, quarter, dataset, include_hispanic=False):
    query = config["compile_ddl_data_fstring"].replace("QUARTER", quarter).replace("DATASET", dataset)
    
    # Configure query parameters for Hispanic filtering
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("include_hispanic", "BOOL", include_hispanic),
        ]
    )
    
    try:
        hispanic_status = "Included" if include_hispanic else "Excluded" 
        print(f"[-] using videoamp dataset {dataset}, Hispanic networks: {hispanic_status}")
        query_job = client.query(query, job_config=job_config)
        result = query_job.result() 
        df = result.to_dataframe()
        if len(df[df['videoamp_match_status'] == 'VideoAmp Matched']) != len(df[df['midas_match_status'] == 'Midas Matched']):
            return {"error": f"Unmatched data returned from this VideoAmp dataset. Please attach this message + the relevant VideoAmp dataset and forward to charles.fuss@groupm.com and amir.gabal@groupm.com."}
        return df
    except Exception as e:
        return {"error": f"Error grabbing data -- {str(e)}"}


def upload_scheduler(client, table1_vals, budget:float, start_date, end_date, dark_weeks, selected_dataset, scheduler_name, session):
    
    # Check duplicate name, throw error if found
    query = config["check_dup_scheduler_name"]


    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("id", "STRING", f"%{scheduler_name}%"),  # Add wildcard
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        result = query_job.result()
        if result.total_rows:  # Check if no rows were returned
            return {"error": f"There is already a scheduler named {scheduler_name}. Please use a different name."}
    except Exception as e:
        return {"error": f"Error grabbing data -- {str(e)}"}


    # Duplicate name not found, create new scheduler
    query = config['insert_new_scheduler']

    job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("id", "STRING", scheduler_name),
        bigquery.ScalarQueryParameter("add_keys", "JSON", json.dumps(session['add_keys'])),
        bigquery.ScalarQueryParameter("remove_keys", "JSON", json.dumps(session['remove_keys'])),
        bigquery.ScalarQueryParameter("table_data", "JSON", json.dumps(table1_vals)),
        bigquery.ScalarQueryParameter("budget", "FLOAT64", budget),
        bigquery.ScalarQueryParameter("start_date", "STRING", start_date),
        bigquery.ScalarQueryParameter("end_date", "STRING", end_date),
        bigquery.ScalarQueryParameter("selected_videoamp_dataset", "STRING", selected_dataset),
        bigquery.ScalarQueryParameter("dark_weeks", "INT64", int(dark_weeks)),
    ]
)
    try:
        query_job = client.query(query, job_config=job_config)
        if 'error' not in query_job.result():
            print(f"Sucessfully uploaded scheduler {scheduler_name}")
            return {'success': f"Sucessfully uploaded scheduler {scheduler_name}"}
    except Exception as e:
        return {"error": f"Error grabbing data -- {str(e)}"}
    

# Load schedule
def load_dataset_from_gcp(client, schedule_name):
    query = config['check_dup_scheduler_name']

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("id", "STRING", schedule_name),
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        if 'error' not in query_job.result():
            if query_job.result().total_rows == 0:
                return {"error": f"No results found for <b>{schedule_name} </b>. Please ensure the scheduler name is accurate."}
            
            results_df = query_job.result().to_dataframe()
            add_keys = json.loads(results_df['add_keys'].iloc[0]).values()
            remove_keys =  json.loads(results_df['remove_keys'].iloc[0]).values()
            table_data = results_df['table_data'].iloc[0]
            budget = results_df['budget'].iloc[0]
            start_date = results_df['start_date'].iloc[0]
            end_date = results_df['end_date'].iloc[0]
            dark_weeks = results_df['dark_weeks'].iloc[0]
            selected_dataset = results_df['selected_videoamp_dataset'].iloc[0]
            return table_data, add_keys, remove_keys, budget, start_date, end_date, dark_weeks, selected_dataset       
    except Exception as e:
        return {"error": f"Error grabbing data -- {str(e)}"}


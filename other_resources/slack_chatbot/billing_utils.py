from google.cloud import bigquery
import datetime
import json
import os
# -----------------------
def get_top_sku_details(project_id, dataset_id, table_id, start_date, end_date):
    """
    Retrieves the top 100 SKUs from your billing export table along with their cost details.
    
    The query returns:
      - sku_description: e.g. "Persistent Disk Storage" or "Cloud Storage"
      - total_cost: Raw cost incurred for that SKU
      - total_discount: Sum of credit amounts where type is 'DISCOUNT'
      - total_promotion: Sum of credit amounts where type is 'PROMOTION'
      - final_cost: Computed as total_cost + total_discount + total_promotion
      
    Parameters:
      project_id (str): Your GCP project ID where the BigQuery dataset resides.
      dataset_id (str): The BigQuery dataset ID containing your billing export table.
      table_id (str): The BigQuery table ID for the billing export.
      start_date (str): Start date/time in ISO format (e.g. "2023-01-01T00:00:00Z").
      end_date (str): End date/time in ISO format (e.g. "2023-02-01T00:00:00Z").
      
    Returns:
      List[dict]: A list of dictionaries (one per SKU) with keys:
          "sku_description", "total_cost", "total_discount", "total_promotion", "final_cost".
    """
    client = bigquery.Client(project=project_id)
    table_ref = f"`{project_id}.{dataset_id}.{table_id}`"
    
    query = f"""
    WITH sku_summary AS (
      SELECT
        sku.description AS sku_description,
        SUM(cost) AS total_cost,
        -- Sum discount amounts if available
        SUM(IFNULL(
          (SELECT SUM(c.amount)
           FROM UNNEST(credits) AS c
           WHERE c.type = 'DISCOUNT'), 0)) AS total_discount,
        -- Sum promotion amounts if available
        SUM(IFNULL(
          (SELECT SUM(c.amount)
           FROM UNNEST(credits) AS c
           WHERE c.type = 'PROMOTION'), 0)) AS total_promotion,
        -- Compute final cost as raw cost plus credits (which are expected to be negative values)
        SUM(cost) +
          SUM(IFNULL(
            (SELECT SUM(c.amount)
             FROM UNNEST(credits) AS c
             WHERE c.type = 'DISCOUNT'), 0)) +
          SUM(IFNULL(
            (SELECT SUM(c.amount)
             FROM UNNEST(credits) AS c
             WHERE c.type = 'PROMOTION'), 0)) AS final_cost
      FROM {table_ref}
      WHERE usage_start_time >= @start_date
        AND usage_start_time < @end_date
      GROUP BY sku_description
    )
    SELECT
      sku_description,
      total_cost,
      total_discount,
      total_promotion,
      final_cost
    FROM sku_summary
    ORDER BY total_cost DESC
    LIMIT 10
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
            bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()
    
    sku_list = []
    for row in results:
        sku_list.append({
            "sku_description": row.sku_description,
            "total_cost": row.total_cost,
            "total_discount": row.total_discount,
            "total_promotion": row.total_promotion,
            "final_cost": row.final_cost,
        })
    # (populate sku_list from the query results)
    
    # Compute overall total cost (computed per SKU as total_cost - total_discount)
    overall_total = sum(s["total_cost"] + s["total_discount"] for s in sku_list) # total_discount are negative values
    
    return sku_list, overall_total
  
def format_slack_message(sku_details, k):
    """
    Format the billing summary for Slack.
    
    Parameters:
      sku_details (List[dict]): List of SKU billing records, each with keys:
          - "sku_description": Name of the SKU.
          - "total_cost": Raw cost incurred.
          - "total_discount": Discount amount.
      k (int): Number of top SKUs to include (sorted by computed cost descending).
    
    Returns:
      str: A formatted string for Slack, containing:
          - The top-k SKU names and their computed cost (total_cost - total_discount)
          - The overall total cost (sum of computed cost for all SKUs not fully discounted)
    """
    # Filter out SKUs that are fully discounted (computed cost is zero)
    filtered = [s for s in sku_details if (s["total_cost"] + s["total_discount"]) != 0]
    
    # Sort the remaining SKUs by computed cost (descending)
    sorted_skus = sorted(filtered, key=lambda s: s["total_cost"] + s["total_discount"], reverse=True)
    
    # Select the top-k SKUs
    top_k = sorted_skus[:k]
    
    # Compute the overall total cost (using computed cost for each SKU)
    overall_total = sum(s["total_cost"] + s["total_discount"] for s in filtered)
    
    # Build the message string (using Slack markdown for clarity)
    lines = []
    lines.append(f"*Total Cost: ${overall_total:.2f}*")
    for idx, sku in enumerate(top_k, start=1):
        computed_cost = sku["total_cost"] + sku["total_discount"]
        lines.append(f"{idx}. {sku['sku_description']}: ${computed_cost:.2f}")
    
    return "\n".join(lines)
# -----------------------
# Local result storage
# -----------------------

def save_result_for_day(result, day_str, folder="results"):
    """
    Saves the given result dictionary to a JSON file named 'YYYY-MM-DD.json' in the specified folder.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_path = os.path.join(folder, f"{day_str}.json")
    with open(file_path, "w") as f:
        json.dump(result, f)

def read_result_for_day(day_str, folder="results"):
    """
    Reads and returns the JSON result saved for the given day (YYYY-MM-DD).
    Returns None if the file doesn't exist.
    """
    file_path = os.path.join(folder, f"{day_str}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return None

# -----------------------
# Last run tracking
# -----------------------

def get_last_run_date(filename="last_run.txt"):
    """
    Reads the last run date from a file. The date is expected in the format YYYY-MM-DD.
    Returns a date object or None if the file does not exist.
    """
    if os.path.exists(filename):
        with open(filename, "r") as f:
            date_str = f.read().strip()
            if date_str:
                return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return None

def update_last_run_date(date_obj, filename="last_run.txt"):
    """
    Writes the given date object to the last run file in YYYY-MM-DD format.
    """
    with open(filename, "w") as f:
        f.write(date_obj.strftime("%Y-%m-%d"))

# -----------------------
# Processing missing days
# -----------------------

def process_missing_days_results(get_result_for_day_func,
                                 project_id,
                                 dataset_id,
                                 table_id,
                                 last_run_file="last_run.txt",
                                 results_folder="results"):
    """
    Checks when the billing function was last run and, if there are missing days up to today,
    calls the provided get_result_for_day_func for each missing day.
    
    Parameters:
      - get_result_for_day_func: a function that accepts (start_date_str, end_date_str, project_id, dataset_id, table_id)
                                 and returns the billing result for that day.
      - project_id, dataset_id, table_id: parameters to pass to the billing query function.
    
    Behavior:
      - Reads the last run date from last_run_file.
      - If the last run date is today (or later), does nothing and returns an empty list.
      - Otherwise, for each missing day (from last_run_date+1 to today, inclusive), it:
           * Constructs the ISO date strings for the day (start_date = day 00:00:00Z, end_date = next day 00:00:00Z).
           * Calls get_result_for_day_func(...) to retrieve the day's billing result.
           * Saves the result locally.
      - Updates last_run_file to today's date.
      
    Returns:
      A list of results (one for each day processed). The length of the list equals the number of missing days.
    """
    today = datetime.date.today() + datetime.timedelta(days=-1)  # yesterday, we keep 1 day delay for the billing data to generate
    last_run_date = get_last_run_date(last_run_file)
    
    # If already processed today, do nothing.
    if last_run_date is not None and last_run_date >= today:
        return []  # or you can return a flag such as {"status": "already run for today"}
    
    # If no last run recorded, assume we want to process yesterday.
    if last_run_date is None:
        last_run_date = today - datetime.timedelta(days=1)
    
    # List missing days from last_run_date up to today(inclusive)
    missing_days = []
    day = last_run_date 
    while day < today: # do not include today
        missing_days.append(day)
        day += datetime.timedelta(days=1)
    
    results = []
    for day in missing_days:
        day_str = day.strftime("%Y-%m-%d")
        start_date_str = f"{day_str}T00:00:00Z"
        next_day = day + datetime.timedelta(days=1)
        end_date_str = f"{next_day.strftime('%Y-%m-%d')}T00:00:00Z"
        print(f"Querying for {day_str} from {start_date_str} to {end_date_str}")
        # Call the billing query function for this day.
        result = get_result_for_day_func(start_date_str, end_date_str, project_id, dataset_id, table_id)
        
        # Save the result locally.
        save_result_for_day(result, day_str, folder=results_folder)
        results.append(result)
    # 
    # Update the last run date to today if all days are processed.
    if len(results) == len(missing_days):
        # Update the last run date to today
        update_last_run_date(today, filename=last_run_file)
    return results
# Wrapper to match the signature required by process_missing_days_results
def get_result_for_day(start_date_str, end_date_str, project_id, dataset_id, table_id):
    return get_top_sku_details(project_id, dataset_id, table_id, start_date_str, end_date_str)

def update_billing_results(project_id, dataset_id, table_id, topk=6):
    """
    Updates the billing results by processing any missing days since the last run.
    """
    
    today = datetime.date.today() + datetime.timedelta(days=-1)  # yesterday
    last_run_date = get_last_run_date()
    #print(f"Last run date: {last_run_date}, today: {today}")
    if last_run_date is not None and last_run_date >= today:
        return []
    results = process_missing_days_results(
        get_result_for_day,
        project_id,
        dataset_id,
        table_id,
    )
    messages = []
    
    for i, result in enumerate(results):
        day_str = today - datetime.timedelta(days=len(results) - i)
        message = format_slack_message(result[0], topk)
        # append day_str to the message
        message = f"*Billing Summary*: {day_str} to {day_str + datetime.timedelta(days=1)} \n" + message
        tip_message = 'For tips on usage and cost-saving strategies, please visit the TPU Resource Hub: '
        message += f"\n\n{tip_message}"
        messages.append(message)
    return messages
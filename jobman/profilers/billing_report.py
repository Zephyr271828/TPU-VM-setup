from google.cloud import bigquery

def query_billing_costs(project, dataset, billing_table):
    client = bigquery.Client(project=project)
    table_ref = f"{project}.{dataset}.{billing_table}"
    sql = f"""
    SELECT
      project.name AS project_id,
      SUM(cost) AS total_cost
    FROM `{table_ref}`
    WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    GROUP BY project_id
    ORDER BY total_cost DESC
    """
    query_job = client.query(sql)
    return query_job.result()

def main():
    project = "vision-mix"
    dataset = "billing_export"
    billing_table = "gcp_billing_export_v1_012345-ABCDEF-678901"

    results = query_billing_costs(project, dataset, billing_table)
    print(f"{'Project':<30} {'Cost (USD)':>15}")
    print('=' * 50)
    for row in results:
        print(f"{row.project_id:<30} {row.total_cost:>15.2f}")

if __name__ == "__main__":
    main()
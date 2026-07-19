# Databricks SQL Dashboard Configuration

All queries live in `notebooks/05_data_analysis.sql`. This file maps each
query to its widget configuration for building the dashboard in the
Databricks SQL UI.

| # | Query name | Chart type | X-axis / Category | Y-axis / Value | Notes |
|---|---|---|---|---|---|
| 1 | `top_10_skills` | Horizontal bar | skill | demand_pct | Sort descending |
| 2 | `top_hiring_locations` | Bar | location | posting_count | Secondary metric: avg_salary_inr as tooltip |
| 3 | `top_job_roles` | Pie / Bar | job_role | posting_count | |
| 4 | `avg_salary_by_role` | Grouped bar | job_role | avg_salary_inr | Group by experience_level |
| 5 | `job_postings_over_time` | Line | posting_month | total_postings | Full-width widget |
| 5b | `job_postings_over_time_by_role` | Multi-series line | posting_month | posting_count | Series = job_role; optional drill-down |
| 6 | `skills_demand_by_role` | Heatmap | job_role | skill | Color = demand_pct_within_role |
| 7 | `experience_level_distribution` | Donut | experience_level | posting_count | |
| KPI | `kpi_total_postings` | Counter | - | total_job_postings | Header widget |
| KPI | `kpi_avg_salary` | Counter | - | avg_salary_inr_all_roles | Header widget |
| KPI | `kpi_unique_companies` | Counter | - | unique_companies | Header widget |

## Build steps

1. In Databricks, go to **SQL -> SQL Editor**, and run each query block
   from `05_data_analysis.sql` individually, saving each with the exact
   `Query name` shown in its comment.
2. For each saved query, click **+ Visualization** and configure using the
   table above.
3. Go to **SQL -> Dashboards -> Create Dashboard**, name it
   "Job Market Intelligence", and add each visualization as a widget.
4. Arrange using the suggested layout at the bottom of
   `05_data_analysis.sql`.
5. Set a refresh schedule (e.g. daily) matching your Workflow schedule so
   the dashboard reflects new Gold data automatically.
6. Take a screenshot once built and save it to `screenshots/dashboard.png`
   for your README/portfolio.

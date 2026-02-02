"""
BigQuery Loader utilities for uploading DataFrames to BigQuery tables.
"""

from google.cloud import bigquery
from google.cloud.bigquery import LoadJobConfig, WriteDisposition
import pandas as pd
from typing import Optional
from datetime import datetime


class BigQueryLoader:
    """Handle BigQuery loading operations."""
    
    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """
        Initialize BigQuery loader.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account JSON (optional)
        """
        if credentials_path:
            import os
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
    
    def load_dataframe(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        table_id: str,
        write_disposition: str = 'WRITE_APPEND'
    ) -> None:
        """
        Load a pandas DataFrame to BigQuery table.
        
        Args:
            df: DataFrame to load
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
            write_disposition: How to handle existing data ('WRITE_APPEND', 'WRITE_TRUNCATE', 'WRITE_EMPTY')
        """
        table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
        
        job_config = LoadJobConfig(
            write_disposition=write_disposition,
            autodetect=True,  # Auto-detect schema from DataFrame
        )
        
        job = self.client.load_table_from_dataframe(
            df, table_ref, job_config=job_config
        )
        
        job.result()  # Wait for the job to complete
        
        print(f"Loaded {len(df)} rows to {table_ref}")
    
    def create_dataset(self, dataset_id: str, location: str = 'US') -> None:
        """
        Create a BigQuery dataset if it doesn't exist.
        
        Args:
            dataset_id: Dataset ID to create
            location: Dataset location (default: US)
        """
        dataset_ref = f"{self.project_id}.{dataset_id}"
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        
        try:
            self.client.create_dataset(dataset, exists_ok=True)
            print(f"Dataset {dataset_id} created or already exists")
        except Exception as e:
            print(f"Error creating dataset: {e}")
    
    def table_exists(self, dataset_id: str, table_id: str) -> bool:
        """
        Check if a table exists.
        
        Args:
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
            
        Returns:
            True if table exists, False otherwise
        """
        table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
        try:
            self.client.get_table(table_ref)
            return True
        except Exception:
            return False
    
    def delete_table(self, dataset_id: str, table_id: str) -> None:
        """
        Delete a BigQuery table.
        
        Args:
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
        """
        table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
        self.client.delete_table(table_ref, not_found_ok=True)
        print(f"Deleted table {table_ref}")
    
    def query(self, sql: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as DataFrame.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Query results as pandas DataFrame
        """
        query_job = self.client.query(sql)
        return query_job.to_dataframe()


def add_metadata_columns(
    df: pd.DataFrame,
    source: str,
    file_name: str
) -> pd.DataFrame:
    """
    Add metadata columns to DataFrame before uploading to BigQuery.
    
    Args:
        df: Source DataFrame
        source: Source identifier (e.g., 'amex', 'scotia_credit')
        file_name: Original file name
        
    Returns:
        DataFrame with added metadata columns
    """
    df_copy = df.copy()
    df_copy['source'] = source
    df_copy['file_name'] = file_name
    df_copy['uploaded_at'] = datetime.now()
    df_copy['processing_date'] = datetime.now().date()
    
    return df_copy

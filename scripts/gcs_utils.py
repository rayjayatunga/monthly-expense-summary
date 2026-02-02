"""
GCS Utilities for downloading and uploading files from Google Cloud Storage.
"""

from google.cloud import storage
from pathlib import Path
from typing import List, Optional
import os


class GCSHandler:
    """Handle Google Cloud Storage operations."""
    
    def __init__(self, bucket_name: str, credentials_path: Optional[str] = None):
        """
        Initialize GCS handler.
        
        Args:
            bucket_name: Name of the GCS bucket
            credentials_path: Path to service account JSON (optional, uses env var if not provided)
        """
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
    
    def list_files(self, prefix: str = '') -> List[str]:
        """
        List all files in the bucket with the given prefix.
        
        Args:
            prefix: Prefix to filter files (e.g., 'raw/amex/')
            
        Returns:
            List of file paths
        """
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs if not blob.name.endswith('/')]
    
    def download_file(self, source_blob_name: str, destination_path: str) -> None:
        """
        Download a file from GCS to local filesystem.
        
        Args:
            source_blob_name: Path to file in GCS bucket
            destination_path: Local path to save the file
        """
        blob = self.bucket.blob(source_blob_name)
        
        # Create parent directories if they don't exist
        Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
        
        blob.download_to_filename(destination_path)
        print(f"Downloaded {source_blob_name} to {destination_path}")
    
    def upload_file(self, source_path: str, destination_blob_name: str) -> None:
        """
        Upload a file from local filesystem to GCS.
        
        Args:
            source_path: Local path to the file
            destination_blob_name: Path in GCS bucket
        """
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_path)
        print(f"Uploaded {source_path} to {destination_blob_name}")
    
    def move_file(self, source_blob_name: str, destination_blob_name: str) -> None:
        """
        Move/rename a file within GCS bucket (copy then delete).
        
        Args:
            source_blob_name: Current path in GCS
            destination_blob_name: New path in GCS
        """
        source_blob = self.bucket.blob(source_blob_name)
        self.bucket.copy_blob(source_blob, self.bucket, destination_blob_name)
        source_blob.delete()
        print(f"Moved {source_blob_name} to {destination_blob_name}")
    
    def delete_file(self, blob_name: str) -> None:
        """
        Delete a file from GCS bucket.
        
        Args:
            blob_name: Path to file in GCS bucket
        """
        blob = self.bucket.blob(blob_name)
        blob.delete()
        print(f"Deleted {blob_name}")


def get_unprocessed_files(gcs_handler: GCSHandler, raw_prefix: str = 'raw/') -> List[str]:
    """
    Get list of files that haven't been processed yet.
    
    Args:
        gcs_handler: GCSHandler instance
        raw_prefix: Prefix for raw files directory
        
    Returns:
        List of unprocessed file paths
    """
    all_files = gcs_handler.list_files(prefix=raw_prefix)
    
    # Filter out already processed files (files in 'processed/' subdirectories)
    unprocessed = [f for f in all_files if '/processed/' not in f]
    
    return unprocessed


def archive_processed_files(gcs_handler: GCSHandler, file_paths: List[str]) -> None:
    """
    Move processed files to 'processed/' subdirectory.
    
    Args:
        gcs_handler: GCSHandler instance
        file_paths: List of file paths to archive
    """
    for file_path in file_paths:
        # Insert 'processed/' before the filename
        parts = file_path.split('/')
        parts.insert(-1, 'processed')
        destination_path = '/'.join(parts)
        
        gcs_handler.move_file(file_path, destination_path)

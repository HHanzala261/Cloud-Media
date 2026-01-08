import os
import uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import AzureError, ResourceNotFoundError
import logging
from typing import Optional, Tuple
import mimetypes

class BlobStorageService:
    """Azure Blob Storage service for MediaCloud"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize blob storage service"""
        self.connection_string = connection_string or os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.blob_service_client = None
        
        if self.connection_string:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
                logging.info("Azure Blob Storage client initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize Azure Blob Storage client: {str(e)}")
        else:
            logging.warning("Azure Blob Storage connection string not provided - blob operations will be disabled")
    
    def is_available(self) -> bool:
        """Check if blob storage is available"""
        return self.blob_service_client is not None
    
    def get_user_container_name(self, user_id: str) -> str:
        """Generate user-specific container name"""
        return f"user-{str(user_id).lower()}"
    
    def generate_blob_name(self, original_filename: str) -> str:
        """Generate UUID-based blob name with original extension"""
        _, ext = os.path.splitext(original_filename)
        return f"{uuid.uuid4()}{ext.lower()}"
    
    def create_container_if_not_exists(self, container_name: str) -> bool:
        """Create container if it doesn't exist"""
        if not self.is_available():
            return False
        
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            container_client.create_container()
            logging.info(f"Created container: {container_name}")
            return True
        except Exception as e:
            if "ContainerAlreadyExists" in str(e):
                logging.debug(f"Container already exists: {container_name}")
                return True
            else:
                logging.error(f"Failed to create container {container_name}: {str(e)}")
                return False
    
    def upload_file(self, user_id: str, file_data: bytes, original_filename: str, content_type: str = None) -> Tuple[bool, Optional[dict]]:
        """
        Upload file to user's blob storage container
        
        Returns:
            Tuple[bool, Optional[dict]]: (success, blob_info)
            blob_info contains: containerName, blobName, url
        """
        if not self.is_available():
            logging.error("Blob storage not available")
            return False, None
        
        try:
            # Generate container and blob names
            container_name = self.get_user_container_name(user_id)
            blob_name = self.generate_blob_name(original_filename)
            
            # Create container if needed
            if not self.create_container_if_not_exists(container_name):
                return False, None
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(original_filename)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Upload blob
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            
            blob_client.upload_blob(
                file_data, 
                content_type=content_type,
                overwrite=True
            )
            
            # Generate blob URL
            blob_url = blob_client.url
            
            blob_info = {
                'containerName': container_name,
                'blobName': blob_name,
                'url': blob_url
            }
            
            logging.info(f"Successfully uploaded blob: {blob_name} to container: {container_name}")
            return True, blob_info
            
        except Exception as e:
            logging.error(f"Failed to upload file: {str(e)}")
            return False, None
    
    def delete_blob(self, container_name: str, blob_name: str) -> bool:
        """Delete blob from storage"""
        if not self.is_available():
            return False
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            blob_client.delete_blob()
            logging.info(f"Successfully deleted blob: {blob_name} from container: {container_name}")
            return True
            
        except ResourceNotFoundError:
            logging.warning(f"Blob not found: {blob_name} in container: {container_name}")
            return True  # Consider it successful if already deleted
        except Exception as e:
            logging.error(f"Failed to delete blob {blob_name}: {str(e)}")
            return False
    
    def blob_exists(self, container_name: str, blob_name: str) -> bool:
        """Check if blob exists"""
        if not self.is_available():
            return False
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            blob_client.get_blob_properties()
            return True
        except ResourceNotFoundError:
            return False
        except Exception as e:
            logging.error(f"Error checking blob existence: {str(e)}")
            return False
    
    def get_blob_url(self, container_name: str, blob_name: str) -> Optional[str]:
        """Get blob URL"""
        if not self.is_available():
            return None
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            return blob_client.url
        except Exception as e:
            logging.error(f"Error getting blob URL: {str(e)}")
            return None

# Global blob storage service instance
blob_storage_service = BlobStorageService()

def get_blob_service() -> BlobStorageService:
    """Get the global blob storage service instance"""
    return blob_storage_service
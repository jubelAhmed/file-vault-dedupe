"""
Celery tasks for file processing.

Contains async tasks for file indexing, content extraction, and search operations.
"""

import logging

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

from files.models import File
from files.services.content_extraction_service import ContentExtractionService
from files.services.search_service import SearchService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def index_file_content_task(self, file_id: str):
    """
    Celery task to extract content from a file and index it for search.

    This task:
    1. Retrieves the file from the database
    2. Extracts text content based on file type
    3. Extracts keywords from the content
    4. Updates FileSearchIndex with keywords and file references

    Args:
        file_id: UUID of the file to index

    Returns:
        dict: Result with status and details
    """
    try:
        logger.info(f"Starting indexing task for file: {file_id}")

        # Get file instance
        try:
            file_instance = File.objects.get(id=file_id)
        except ObjectDoesNotExist:
            logger.error(f"File not found: {file_id}")
            return {"status": "error", "message": f"File not found: {file_id}"}

        # Get the actual file path
        actual_file = file_instance.get_actual_file()

        if not actual_file:
            logger.warning(f"No physical file found for: {file_id}")
            return {
                "status": "skipped",
                "message": "No physical file to index",
                "file_id": str(file_id),
            }

        # Get file path
        file_path = actual_file.path
        mime_type = file_instance.file_type

        logger.info(f"Processing file: {file_instance.original_filename} (type: {mime_type})")

        # Check if file type is supported
        if not ContentExtractionService.is_supported_file_type(mime_type):
            logger.info(f"File type not supported for indexing: {mime_type}")
            return {
                "status": "skipped",
                "message": f"File type not supported: {mime_type}",
                "file_id": str(file_id),
            }

        # Extract text content
        logger.info(f"Extracting content from: {file_path}")
        text_content = ContentExtractionService.extract_text(file_path, mime_type)

        if not text_content:
            logger.warning(f"No text content extracted from file: {file_id}")
            return {
                "status": "completed",
                "message": "No text content extracted",
                "file_id": str(file_id),
                "keywords_indexed": 0,
            }

        # Index the content
        logger.info(f"Indexing content for file: {file_id}")
        keywords_indexed = SearchService.index_file_content(file_instance, text_content)

        logger.info(f"Successfully indexed {keywords_indexed} keywords for file: {file_id}")

        return {
            "status": "completed",
            "message": "File indexed successfully",
            "file_id": str(file_id),
            "filename": file_instance.original_filename,
            "keywords_indexed": keywords_indexed,
            "content_length": len(text_content),
        }

    except Exception as exc:
        logger.error(f"Error indexing file {file_id}: {str(exc)}", exc_info=True)

        # Retry the task
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for file {file_id}")
            return {
                "status": "failed",
                "message": f"Failed after {self.max_retries} retries: {str(exc)}",
                "file_id": str(file_id),
            }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def remove_file_from_index_task(self, file_id: str):
    """
    Celery task to remove a file from the search index.

    Called when a file is deleted to clean up search references.

    Args:
        file_id: UUID of the file to remove from index

    Returns:
        dict: Result with status and details
    """
    try:
        logger.info(f"Starting index removal task for file: {file_id}")

        # Get file instance
        try:
            file_instance = File.objects.get(id=file_id)
        except ObjectDoesNotExist:
            logger.warning(f"File not found during index removal: {file_id}")
            # File might already be deleted, which is okay
            return {
                "status": "completed",
                "message": "File already deleted",
                "file_id": str(file_id),
            }

        # Remove from index
        removed_count = SearchService.remove_file_from_index(file_instance)

        logger.info(f"Removed file {file_id} from {removed_count} search indexes")

        return {
            "status": "completed",
            "message": "File removed from index",
            "file_id": str(file_id),
            "keywords_removed": removed_count,
        }

    except Exception as exc:
        logger.error(f"Error removing file {file_id} from index: {str(exc)}", exc_info=True)

        # Retry the task
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for removing file {file_id} from index")
            return {
                "status": "failed",
                "message": f"Failed after {self.max_retries} retries: {str(exc)}",
                "file_id": str(file_id),
            }


@shared_task
def reindex_all_files():
    """
    Celery task to reindex all files in the system.

    This is a maintenance task that can be run periodically or manually
    to rebuild the entire search index.

    Returns:
        dict: Summary of reindexing operation
    """
    try:
        logger.info("Starting full reindex of all files")

        # Get all files
        all_files = File.objects.all()
        total_files = all_files.count()

        logger.info(f"Found {total_files} files to reindex")

        # Queue indexing tasks for all files
        queued = 0
        for file_instance in all_files:
            try:
                index_file_content_task.delay(str(file_instance.id))
                queued += 1
            except Exception as e:
                logger.error(f"Error queueing reindex for file {file_instance.id}: {str(e)}")

        logger.info(f"Queued {queued} files for reindexing")

        return {
            "status": "completed",
            "message": "Reindex tasks queued",
            "total_files": total_files,
            "queued": queued,
        }

    except Exception as e:
        logger.error(f"Error during full reindex: {str(e)}", exc_info=True)
        return {"status": "failed", "message": str(e)}

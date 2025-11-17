"""
Search Service

Manages the FileSearchIndex model, extracts keywords from text content,
and maintains file references for efficient file content search.
"""

import logging
import re

from django.conf import settings
from django.db import models, transaction

from files.models import File, FileSearchIndex

logger = logging.getLogger(__name__)


class SearchService:
    """Service for managing file content search and keyword extraction."""

    @staticmethod
    def extract_keywords(text: str) -> set[str]:
        """
        Extract keywords from text content.

        Performs:
        - Converts to lowercase
        - Removes special characters
        - Filters by word length
        - Removes stop words
        - Returns unique keywords

        Args:
            text: Text content to extract keywords from

        Returns:
            Set of unique keywords
        """
        if not text:
            return set()

        # Convert to lowercase
        text = text.lower()

        # Extract words (alphanumeric only)
        words = re.findall(r"\b[a-z0-9]+\b", text)

        # Get configuration
        min_length = getattr(settings, "SEARCH_INDEX_MIN_WORD_LENGTH", 3)
        max_length = getattr(settings, "SEARCH_INDEX_MAX_WORD_LENGTH", 50)
        stop_words: set[str] = getattr(settings, "SEARCH_INDEX_STOP_WORDS", set())

        # Filter words
        keywords = set()
        for word in words:
            # Check length constraints
            if len(word) < min_length or len(word) > max_length:
                continue

            # Skip stop words
            if word in stop_words:
                continue

            keywords.add(word)

        logger.info(f"Extracted {len(keywords)} unique keywords from text")
        return keywords

    @staticmethod
    @transaction.atomic
    def index_file_content(file_instance: File, text_content: str) -> int:
        """
        Index file content by extracting keywords and creating/updating
        FileSearchIndex entries.

        Args:
            file_instance: File instance to index
            text_content: Extracted text content

        Returns:
            Number of keywords indexed
        """
        if not text_content:
            logger.warning(f"No text content to index for file {file_instance.id}")
            return 0

        # Extract keywords
        keywords = SearchService.extract_keywords(text_content)

        if not keywords:
            logger.warning(f"No keywords extracted from file {file_instance.id}")
            return 0

        indexed_count = 0

        # Create or update FileSearchIndex entries
        for keyword in keywords:
            try:
                # Get or create the keyword entry
                search_index, created = FileSearchIndex.objects.get_or_create(keyword=keyword)

                # Add file reference if not already present
                if not search_index.files.filter(id=file_instance.id).exists():
                    search_index.files.add(file_instance)
                    indexed_count += 1

                    if created:
                        logger.debug(f"Created new search index for keyword: {keyword}")
                    else:
                        logger.debug(f"Added file to existing keyword: {keyword}")

            except Exception as e:
                logger.error(
                    f"Error indexing keyword '{keyword}' for file {file_instance.id}: {str(e)}"
                )
                continue

        logger.info(f"Indexed {indexed_count} keywords for file {file_instance.id}")
        return indexed_count

    @staticmethod
    @transaction.atomic
    def remove_file_from_index(file_instance: File) -> int:
        """
        Remove all file references from search indexes.
        Also removes orphaned keywords (keywords with no file references).

        Args:
            file_instance: File instance to remove from indexes

        Returns:
            Number of keywords removed/updated
        """
        removed_count = 0

        try:
            # Get all search indexes referencing this file
            search_indexes = FileSearchIndex.objects.filter(files=file_instance)

            for search_index in search_indexes:
                # Remove the file reference
                search_index.files.remove(file_instance)
                removed_count += 1

                # Check if keyword is now orphaned (no files)
                if search_index.files.count() == 0:
                    logger.debug(f"Deleting orphaned keyword: {search_index.keyword}")
                    search_index.delete()

            logger.info(f"Removed file {file_instance.id} from {removed_count} search indexes")

        except Exception as e:
            logger.error(f"Error removing file {file_instance.id} from search indexes: {str(e)}")

        return removed_count

    @staticmethod
    def search_files_by_keyword(keyword: str, user_id: str | None = None) -> list[File]:
        """
        Search files by keyword.

        Uses the FileSearchIndex model's find_files_by_keyword method.

        Args:
            keyword: Keyword to search for
            user_id: Optional user ID to filter results by user

        Returns:
            List of File instances matching the keyword
        """
        try:
            files = FileSearchIndex.find_files_by_keyword(keyword, user_id)
            file_list = list(files)
            logger.info(f"Found {len(file_list)} files for keyword: {keyword}")
            return file_list
        except Exception as e:
            logger.error(f"Error searching for keyword '{keyword}': {str(e)}")
            return []

    @staticmethod
    def search_files_by_keywords(keywords: list[str], user_id: str | None = None) -> list[File]:
        """
        Search files by multiple keywords (OR operation).

        Args:
            keywords: List of keywords to search for
            user_id: Optional user ID to filter results by user

        Returns:
            List of File instances matching any of the keywords
        """
        if not keywords:
            return []

        try:
            # Normalize keywords
            normalized_keywords = [k.lower().strip() for k in keywords if k.strip()]

            if not normalized_keywords:
                return []

            # Get all search indexes matching any keyword
            search_indexes = FileSearchIndex.objects.filter(keyword__in=normalized_keywords)

            # Collect all unique files
            file_ids = set()
            for search_index in search_indexes:
                file_ids.update(search_index.files.values_list("id", flat=True))

            # Get files
            files = File.objects.filter(id__in=file_ids)

            # Filter by user if specified
            if user_id:
                files = files.filter(user_id=user_id)

            logger.info(
                f"Found {files.count()} files for keywords: {', '.join(normalized_keywords)}"
            )
            return list(files)

        except Exception as e:
            logger.error(f"Error searching for keywords: {str(e)}")
            return []

    @staticmethod
    def get_keyword_stats() -> dict:
        """
        Get statistics about the search index.

        Returns:
            Dictionary with statistics
        """
        try:
            total_keywords = FileSearchIndex.objects.count()

            # Get keyword with most files
            top_keyword = (
                FileSearchIndex.objects.annotate(file_count=models.Count("files"))
                .order_by("-file_count")
                .first()
            )

            return {
                "total_keywords": total_keywords,
                "top_keyword": {
                    "keyword": top_keyword.keyword if top_keyword else None,
                    "file_count": top_keyword.file_count if top_keyword else 0,
                },
            }

        except Exception as e:
            logger.error(f"Error getting keyword stats: {str(e)}")
            return {"total_keywords": 0, "top_keyword": {"keyword": None, "file_count": 0}}

"""Message handler for enhancing queries with context and filters."""

import sqlite3
from typing import Optional


class MessageHandler:
    """
    Handles message processing and query enhancement.
    
    Enhances user queries with:
    - Conversation history context
    - Channel filtering
    - Project/topic filtering
    """
    
    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize message handler.
        
        Args:
            conn: Database connection
        """
        self.conn = conn
    
    def enhance_query(
        self,
        user_query: str,
        history: Optional[list[dict]] = None,
        channel_filter: Optional[str] = None,
        project_filter: Optional[str] = None
    ) -> str:
        """
        Enhance user query with context and filters.
        
        Args:
            user_query: Original user query
            history: Recent conversation history
            channel_filter: Channel name to filter by
            project_filter: Project/topic to filter by
        
        Returns:
            Enhanced query string with context
        
        Examples:
            >>> handler.enhance_query(
            ...     "What about last week?",
            ...     history=[{"role": "user", "content": "What did Dan ask me?"}],
            ...     channel_filter="TMA Disasterville"
            ... )
            "In the TMA Disasterville channel, what did Dan ask me to do last week?"
        """
        enhanced_parts = []
        
        # Add channel context if set
        if channel_filter:
            enhanced_parts.append(f"In the {channel_filter} channel")
        
        # Add project context if set
        if project_filter:
            enhanced_parts.append(f"related to {project_filter}")
        
        # Check if query is a follow-up (contains pronouns or relative time without context)
        is_followup = self._is_followup_query(user_query)
        
        # Add conversation context for follow-ups
        if is_followup and history:
            # Get the last user query for context
            last_user_query = None
            for msg in reversed(history):
                if msg["role"] == "user":
                    last_user_query = msg["content"]
                    break
            
            if last_user_query:
                enhanced_parts.append(f"(previous question: {last_user_query})")
        
        # Combine parts with the original query
        if enhanced_parts:
            prefix = ", ".join(enhanced_parts)
            return f"{prefix}, {user_query}"
        
        return user_query
    
    def _is_followup_query(self, query: str) -> bool:
        """
        Detect if a query is likely a follow-up question.
        
        Args:
            query: User query
        
        Returns:
            True if query appears to be a follow-up
        
        Examples:
            >>> handler._is_followup_query("What about last week?")
            True
            >>> handler._is_followup_query("Show me all tasks")
            False
        """
        query_lower = query.lower()
        
        # Follow-up indicators
        followup_patterns = [
            "what about",
            "how about",
            "and ",
            "also ",
            "what else",
            "any other",
            "show me those",
            "show me them",
            "show me that",
            "from there",
            "from that",
            "from those",
        ]
        
        # Relative time without specific context
        relative_time_patterns = [
            "last week",
            "this week",
            "yesterday",
            "today",
            "this month",
            "last month",
        ]
        
        # Check for follow-up patterns
        for pattern in followup_patterns:
            if pattern in query_lower:
                return True
        
        # Check for relative time in short queries (likely follow-ups)
        if len(query.split()) < 6:
            for pattern in relative_time_patterns:
                if pattern in query_lower:
                    return True
        
        return False
    
    def extract_channel_mention(self, query: str) -> Optional[str]:
        """
        Extract channel name from query if mentioned.
        
        Args:
            query: User query
        
        Returns:
            Channel name if found, None otherwise
        
        Examples:
            >>> handler.extract_channel_mention("What's new in TMA Disasterville?")
            "TMA Disasterville"
            >>> handler.extract_channel_mention("Show me tasks")
            None
        """
        # Get available channels from database
        cursor = self.conn.execute(
            """SELECT DISTINCT channel_name 
               FROM conversations 
               WHERE channel_name IS NOT NULL AND channel_name != ''"""
        )
        channels = [row[0] for row in cursor.fetchall()]
        
        # Check if any channel name appears in the query
        query_lower = query.lower()
        for channel in channels:
            if channel.lower() in query_lower:
                return channel
        
        return None
    
    def extract_project_mention(self, query: str) -> Optional[str]:
        """
        Extract project/topic keywords from query.
        
        Args:
            query: User query
        
        Returns:
            Project name/keywords if found, None otherwise
        
        Examples:
            >>> handler.extract_project_mention("Tasks for the Orchestrator app")
            "Orchestrator"
            >>> handler.extract_project_mention("Show me all tasks")
            None
        """
        # Common project indicators
        project_indicators = [
            "for the",
            "about the",
            "regarding",
            "related to",
            "concerning",
            "for",
            "about",
        ]
        
        query_lower = query.lower()
        
        # Look for project indicators followed by capitalized words
        import re
        
        for indicator in project_indicators:
            pattern = rf"{indicator}\s+([A-Z][A-Za-z0-9\s]+?)(?:\s+(?:app|project|feature|task|channel|issue)|\s*$|[,.])"
            match = re.search(pattern, query)
            if match:
                project_name = match.group(1).strip()
                # Remove common suffixes
                project_name = re.sub(r'\s+(app|project|feature|task|channel|issue)$', '', project_name, flags=re.IGNORECASE)
                return project_name
        
        # Look for capitalized multi-word phrases (potential project names)
        # e.g., "Orchestrator API", "TMA System"
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        matches = re.findall(pattern, query)
        if matches:
            # Return the first match
            return matches[0]
        
        return None
    
    def get_context_summary(
        self,
        channel_filter: Optional[str] = None,
        project_filter: Optional[str] = None
    ) -> str:
        """
        Get a summary of current context filters.
        
        Args:
            channel_filter: Current channel filter
            project_filter: Current project filter
        
        Returns:
            Human-readable context summary
        
        Examples:
            >>> handler.get_context_summary("TMA Disasterville", "Orchestrator")
            "Channel: TMA Disasterville | Project: Orchestrator"
        """
        parts = []
        
        if channel_filter:
            parts.append(f"Channel: {channel_filter}")
        
        if project_filter:
            parts.append(f"Project: {project_filter}")
        
        if parts:
            return " | ".join(parts)
        
        return "No filters active"


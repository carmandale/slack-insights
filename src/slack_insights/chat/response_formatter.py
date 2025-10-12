"""Response formatter for chat messages."""

from typing import Optional


class ResponseFormatter:
    """
    Formats chat responses for display.
    
    Provides consistent, readable formatting for different types of responses.
    """
    
    def format_response(
        self,
        results: list[dict],
        explanation: str,
        channel_filter: Optional[str] = None,
        project_filter: Optional[str] = None
    ) -> str:
        """
        Format query results into a readable response.
        
        Args:
            results: Grouped query results
            explanation: Query explanation from Claude
            channel_filter: Active channel filter
            project_filter: Active project filter
        
        Returns:
            Formatted response string
        """
        if not results:
            return self._format_no_results(channel_filter, project_filter)
        
        lines = []
        
        # Add context if filters are active
        context_parts = []
        if channel_filter:
            context_parts.append(f"Channel: {channel_filter}")
        if project_filter:
            context_parts.append(f"Project: {project_filter}")
        
        if context_parts:
            lines.append(f"[{' | '.join(context_parts)}]")
            lines.append("")
        
        # Add summary
        total_instances = sum(group.get("count", 1) for group in results)
        lines.append(
            f"Found {len(results)} unique task(s) "
            f"({total_instances} total mention(s))"
        )
        lines.append("")
        
        # Format each result group
        for i, group in enumerate(results, 1):
            lines.extend(self._format_result_group(i, group))
            lines.append("")  # Blank line between groups
        
        return "\n".join(lines)
    
    def _format_result_group(self, index: int, group: dict) -> list[str]:
        """
        Format a single result group.
        
        Args:
            index: Result number
            group: Grouped result dictionary
        
        Returns:
            List of formatted lines
        """
        lines = []
        
        canonical_task = group.get("canonical_task", "Unknown task")
        count = group.get("count", 1)
        status = group.get("status", "unknown")
        instances = group.get("instances", [])
        
        # Header with frequency indicator
        if count > 1:
            lines.append(f"{index}. ⚠ {count}x {canonical_task}")
        else:
            lines.append(f"{index}. {canonical_task}")
        
        # Status with emoji
        status_emoji = "✅" if status == "completed" else "⏳"
        lines.append(f"   Status: {status_emoji} {status}")
        
        # Show first instance details
        if instances:
            first = instances[0]
            
            # Assigner
            assigner = first.get("assigner_username", "Unknown")
            lines.append(f"   From: {assigner}")
            
            # Date
            date = first.get("date", "Unknown date")
            lines.append(f"   Date: {date}")
            
            # Context quote if available
            context = first.get("context_quote", "")
            if context and len(context.strip()) > 0:
                # Truncate long context
                if len(context) > 100:
                    context = context[:97] + "..."
                lines.append(f"   Context: \"{context}\"")
        
        return lines
    
    def _format_no_results(
        self,
        channel_filter: Optional[str] = None,
        project_filter: Optional[str] = None
    ) -> str:
        """
        Format message when no results are found.
        
        Args:
            channel_filter: Active channel filter
            project_filter: Active project filter
        
        Returns:
            Formatted message
        """
        lines = ["No results found."]
        
        # Suggest removing filters if active
        if channel_filter or project_filter:
            lines.append("")
            lines.append("Active filters:")
            if channel_filter:
                lines.append(f"  - Channel: {channel_filter}")
            if project_filter:
                lines.append(f"  - Project: {project_filter}")
            lines.append("")
            lines.append("Try removing filters with /clear-filters")
        
        return "\n".join(lines)
    
    def format_help(self) -> str:
        """
        Format help message with available commands.
        
        Returns:
            Formatted help text
        """
        return """
Available Commands:
  /help              - Show this help message
  /history           - Show conversation history
  /clear             - Clear conversation history
  /channel <name>    - Set channel filter
  /project <name>    - Set project filter
  /clear-filters     - Clear all filters
  /channels          - List available channels
  /exit or /quit     - Exit chat session

Example Queries:
  - What did Dan ask me to do?
  - Show me urgent tasks from last week
  - What's the latest update in TMA Disasterville?
  - What tasks are related to the Orchestrator app?
  - Show me all open items
  - What has been completed this month?

Tips:
  - Ask follow-up questions naturally
  - Use /channel to focus on a specific channel
  - Use /project to filter by topic or project name
  - The chat remembers context from previous questions
"""
    
    def format_history(self, messages: list[dict]) -> str:
        """
        Format conversation history.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Formatted history
        """
        if not messages:
            return "No conversation history."
        
        lines = ["Conversation History:", ""]
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            # Truncate long messages
            if len(content) > 200:
                content = content[:197] + "..."
            
            if role == "user":
                lines.append(f"You: {content}")
            else:
                lines.append(f"Assistant: {content}")
            lines.append("")
        
        return "\n".join(lines)
    
    def format_channels_list(self, channels: list[str]) -> str:
        """
        Format list of available channels.
        
        Args:
            channels: List of channel names
        
        Returns:
            Formatted channel list
        """
        if not channels:
            return "No channels found in database."
        
        lines = [f"Available Channels ({len(channels)}):", ""]
        
        for channel in channels:
            lines.append(f"  - {channel}")
        
        return "\n".join(lines)
    
    def format_context_change(
        self,
        change_type: str,
        value: Optional[str] = None
    ) -> str:
        """
        Format context change notification.
        
        Args:
            change_type: Type of change (channel, project, clear)
            value: New value (if applicable)
        
        Returns:
            Formatted notification
        """
        if change_type == "channel":
            if value:
                return f"✓ Channel filter set to: {value}"
            else:
                return "✓ Channel filter cleared"
        
        elif change_type == "project":
            if value:
                return f"✓ Project filter set to: {value}"
            else:
                return "✓ Project filter cleared"
        
        elif change_type == "clear":
            return "✓ All filters cleared"
        
        elif change_type == "clear_history":
            return "✓ Conversation history cleared"
        
        return "✓ Context updated"


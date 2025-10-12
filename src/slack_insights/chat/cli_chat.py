"""Interactive CLI chat interface."""

import os
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .chat_engine import ChatEngine
from .response_formatter import ResponseFormatter


class InteractiveChatCLI:
    """
    Interactive command-line chat interface.
    
    Provides a REPL-style interface for chatting with the LLM about Slack data.
    """
    
    def __init__(self, db_path: str = "slack_insights.db"):
        """
        Initialize interactive chat CLI.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.console = Console()
        self.formatter = ResponseFormatter()
        self.chat_engine: Optional[ChatEngine] = None
        self.session_id: Optional[str] = None
    
    def run(self):
        """Run the interactive chat session."""
        try:
            # Initialize chat engine
            self.chat_engine = ChatEngine(self.db_path)
            self.session_id = self.chat_engine.start_session()
            
            # Show welcome message
            self._show_welcome()
            
            # Main chat loop
            while True:
                try:
                    # Get user input
                    user_input = self.console.input("\n[bold cyan]You:[/bold cyan] ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Check for commands
                    if user_input.startswith("/"):
                        if not self._handle_command(user_input):
                            break  # Exit command
                        continue
                    
                    # Process query
                    self._process_query(user_input)
                
                except KeyboardInterrupt:
                    self.console.print("\n\n[yellow]Chat interrupted. Type /exit to quit or continue chatting.[/yellow]")
                    continue
                except EOFError:
                    break
        
        except Exception as e:
            self.console.print(f"\n[red]Error:[/red] {e}")
        
        finally:
            # Cleanup
            if self.chat_engine:
                self.chat_engine.close()
            self.console.print("\n[dim]Chat session ended.[/dim]")
    
    def _show_welcome(self):
        """Show welcome message and instructions."""
        welcome_text = """
# 🤖 Slack Insights Chat

Ask questions about your Slack conversations in natural language!

**Example queries:**
- What did Dan ask me to do?
- Show me urgent tasks from last week
- What's the latest update in TMA Disasterville?
- What tasks are related to the Orchestrator app?

**Commands:** Type `/help` for available commands

**Exit:** Type `/exit` or press Ctrl+D
"""
        self.console.print(Panel(Markdown(welcome_text), border_style="cyan"))
    
    def _handle_command(self, command: str) -> bool:
        """
        Handle slash commands.
        
        Args:
            command: Command string starting with /
        
        Returns:
            True to continue chat, False to exit
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None
        
        if cmd in ["/exit", "/quit"]:
            return False
        
        elif cmd == "/help":
            help_text = self.formatter.format_help()
            self.console.print(help_text)
        
        elif cmd == "/history":
            history = self.chat_engine.get_history(self.session_id)
            history_text = self.formatter.format_history(history)
            self.console.print(history_text)
        
        elif cmd == "/clear":
            self.chat_engine.clear_session(self.session_id)
            msg = self.formatter.format_context_change("clear_history")
            self.console.print(f"[green]{msg}[/green]")
        
        elif cmd == "/channel":
            if arg:
                self.chat_engine.set_channel_filter(self.session_id, arg)
                msg = self.formatter.format_context_change("channel", arg)
                self.console.print(f"[green]{msg}[/green]")
            else:
                self.console.print("[yellow]Usage: /channel <name>[/yellow]")
        
        elif cmd == "/project":
            if arg:
                self.chat_engine.set_project_filter(self.session_id, arg)
                msg = self.formatter.format_context_change("project", arg)
                self.console.print(f"[green]{msg}[/green]")
            else:
                self.console.print("[yellow]Usage: /project <name>[/yellow]")
        
        elif cmd == "/clear-filters":
            self.chat_engine.set_channel_filter(self.session_id, None)
            self.chat_engine.set_project_filter(self.session_id, None)
            msg = self.formatter.format_context_change("clear")
            self.console.print(f"[green]{msg}[/green]")
        
        elif cmd == "/channels":
            channels = self.chat_engine.get_available_channels()
            channels_text = self.formatter.format_channels_list(channels)
            self.console.print(channels_text)
        
        else:
            self.console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            self.console.print("[dim]Type /help for available commands[/dim]")
        
        return True
    
    def _process_query(self, user_query: str):
        """
        Process user query and display response.
        
        Args:
            user_query: User's natural language query
        """
        try:
            # Show processing indicator
            with self.console.status("[cyan]Thinking...[/cyan]"):
                response = self.chat_engine.send_message(self.session_id, user_query)
            
            # Display response
            self.console.print("\n[bold green]Assistant:[/bold green]")
            self.console.print(response["response"])
            
            # Optionally show SQL query (for debugging/transparency)
            if os.getenv("SHOW_SQL", "").lower() in ["true", "1", "yes"]:
                self.console.print(f"\n[dim]SQL: {response['sql_query']}[/dim]")
        
        except Exception as e:
            self.console.print(f"\n[red]Error processing query:[/red] {e}")
            self.console.print("[dim]Please try rephrasing your question.[/dim]")


def run_interactive_chat(db_path: str = "slack_insights.db"):
    """
    Run interactive chat session.
    
    Args:
        db_path: Path to SQLite database
    """
    cli = InteractiveChatCLI(db_path)
    cli.run()


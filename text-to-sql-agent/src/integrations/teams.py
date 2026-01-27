"""Microsoft Teams integration for the Text-to-SQL agent."""

from typing import Optional
from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    ActivityHandler,
    MessageFactory
)
from botbuilder.schema import Activity, ActivityTypes
from loguru import logger

from ..agent.agent import TextToSQLAgent, ResponseType
from ..utils.config import Config


class TextToSQLBot(ActivityHandler):
    """Teams bot for text-to-SQL agent."""
    
    def __init__(self, agent: TextToSQLAgent):
        """Initialize Teams bot."""
        super().__init__()
        self.agent = agent
        logger.info("Teams bot initialized")
    
    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming messages."""
        question = turn_context.activity.text.strip()
        
        if not question:
            await turn_context.send_activity("Please provide a question about your data.")
            return
        
        # Get or create session for this conversation
        conversation_id = turn_context.activity.conversation.id
        
        # Send typing indicator
        await turn_context.send_activities([
            Activity(type=ActivityTypes.typing)
        ])
        
        try:
            # Process question
            result = self.agent.process_question(
                question=question,
                session_id=conversation_id
            )
            
            # Format response
            response = await self._format_response(result)
            await turn_context.send_activity(response)
            
        except Exception as e:
            logger.error(f"Error processing Teams message: {e}")
            await turn_context.send_activity(
                f"Sorry, I encountered an error: {str(e)}"
            )
    
    async def on_members_added_activity(
        self,
        members_added: list,
        turn_context: TurnContext
    ):
        """Handle new members added to conversation."""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_message = (
                    "👋 Hello! I'm your Text-to-SQL assistant.\n\n"
                    "Ask me any question about your data in natural language, "
                    "and I'll convert it to SQL and show you the results!\n\n"
                    "Example: \"Show me the top 10 customers by revenue\""
                )
                await turn_context.send_activity(welcome_message)
    
    async def _format_response(self, result: dict) -> str:
        """Format agent response for Teams."""
        if result['response_type'] == ResponseType.ERROR:
            error = result['data']['error']
            sql_query = result.get('metadata', {}).get('sql_query')
            
            message = f"❌ **Error:** {error}\n\n"
            if sql_query:
                message += f"```sql\n{sql_query}\n```"
            return message
        
        elif result['response_type'] == ResponseType.SIMILAR_QUESTION:
            data = result['data']
            similarity = data['similarity'] * 100
            
            message = (
                f"🔍 **Similar Question Found** (Similarity: {similarity:.1f}%)\n\n"
                f"*{data['similar_question']}*\n\n"
                f"Would you like to use this answer or generate a new one?\n"
                f"Reply with 'use existing' or 'generate new'"
            )
            return message
        
        elif result['success']:
            row_count = result['data']['row_count']
            execution_time = result['data']['execution_time']
            sql_query = result['metadata']['sql_query']
            
            message = (
                f"✅ **Query executed successfully!**\n\n"
                f"📊 Found {row_count} rows in {execution_time:.2f}s\n\n"
                f"**SQL Query:**\n```sql\n{sql_query}\n```\n\n"
            )
            
            # Add table preview for Teams (limit rows for readability)
            if result['data']['rows']:
                columns = result['data']['columns']
                rows = result['data']['rows'][:10]  # Limit to 10 rows
                
                message += "**Results Preview:**\n\n"
                
                # Simple table format
                header = " | ".join(columns)
                separator = " | ".join(["-" * len(col) for col in columns])
                message += f"{header}\n{separator}\n"
                
                for row in rows:
                    message += " | ".join([str(val) for val in row]) + "\n"
                
                if row_count > 10:
                    message += f"\n... and {row_count - 10} more rows"
            
            # Add metadata
            metadata = result['metadata']
            if metadata.get('relevant_tables'):
                message += f"\n\n**Tables used:** {', '.join(metadata['relevant_tables'])}"
            
            return message
        
        return "Unable to process your request."


class TeamsIntegration:
    """Microsoft Teams integration manager."""
    
    def __init__(self, agent: TextToSQLAgent, config: Config):
        """Initialize Teams integration."""
        self.agent = agent
        self.config = config
        
        # Create adapter
        settings = BotFrameworkAdapterSettings(
            app_id=config.teams.app_id,
            app_password=config.teams.app_password
        )
        self.adapter = BotFrameworkAdapter(settings)
        
        # Error handler
        async def on_error(context: TurnContext, error: Exception):
            logger.error(f"Teams adapter error: {error}")
            await context.send_activity("Sorry, something went wrong.")
        
        self.adapter.on_turn_error = on_error
        
        # Create bot
        self.bot = TextToSQLBot(agent)
        
        logger.info("Teams integration initialized")
    
    async def handle_message(self, req: Request) -> Response:
        """Handle incoming Teams message."""
        if "application/json" in req.headers["Content-Type"]:
            body = await req.json()
        else:
            return Response(status=415)
        
        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")
        
        try:
            response = await self.adapter.process_activity(
                activity,
                auth_header,
                self.bot.on_turn
            )
            
            if response:
                return Response(
                    body=response.body,
                    status=response.status
                )
            return Response(status=200)
            
        except Exception as e:
            logger.error(f"Error handling Teams message: {e}")
            return Response(status=500)
    
    def setup_routes(self, app: web.Application):
        """Setup Teams routes in aiohttp app."""
        endpoint = self.config.teams.endpoint
        app.router.add_post(endpoint, self.handle_message)
        logger.info(f"Teams endpoint configured: {endpoint}")


def create_teams_integration(agent: TextToSQLAgent, config: Config) -> Optional[TeamsIntegration]:
    """Create Teams integration if enabled."""
    if not config.teams.enabled:
        logger.info("Teams integration disabled")
        return None
    
    if not config.teams.app_id or not config.teams.app_password:
        logger.warning("Teams integration enabled but credentials not provided")
        return None
    
    return TeamsIntegration(agent, config)

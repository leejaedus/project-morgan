"""
Morgan - Slack API Client

Handles all interactions with the Slack API for collecting activities.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from models import SlackMessage, ActivityType


class SlackClient:
    """Slack API client for collecting user activities"""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize Slack client"""
        self.token = token or os.getenv("SLACK_TOKEN")
        if not self.token:
            raise ValueError("Slack token is required. Set SLACK_TOKEN environment variable.")
        
        self.client = WebClient(token=self.token)
        self.user_id: Optional[str] = None
        self._user_info_cache: Dict[str, Any] = {}
        self._channel_info_cache: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """Initialize client and get user info"""
        try:
            # Get current user info
            response = self.client.auth_test()
            self.user_id = response["user_id"]
            print(f"✅ Authenticated as user {self.user_id}")
        except SlackApiError as e:
            raise Exception(f"Failed to authenticate with Slack: {e.response['error']}")
    
    def _get_timestamp_filter(self, hours: int) -> float:
        """Get timestamp for filtering messages"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return cutoff_time.timestamp()
    
    def _parse_slack_message(self, message_data: Dict[str, Any], 
                           channel_info: Dict[str, Any],
                           activity_type: ActivityType) -> SlackMessage:
        """Parse Slack API message data into SlackMessage model"""
        
        # Get user info
        user_info = self._get_user_info(message_data.get("user", ""))
        
        # Parse timestamp
        timestamp = datetime.fromtimestamp(float(message_data.get("ts", 0)))
        
        # Check if message mentions current user
        text = message_data.get("text", "")
        mentions_me = f"<@{self.user_id}>" in text if self.user_id else False
        
        # Create permalink
        permalink = f"https://{self.client.token[:10]}.slack.com/archives/{channel_info['id']}/p{message_data.get('ts', '').replace('.', '')}"
        
        return SlackMessage(
            message_id=message_data.get("ts", ""),
            channel_id=channel_info["id"],
            channel_name=channel_info.get("name", "unknown"),
            user_id=message_data.get("user", ""),
            username=user_info.get("real_name", user_info.get("name", "unknown")),
            text=text,
            timestamp=timestamp,
            permalink=permalink,
            activity_type=activity_type,
            thread_ts=message_data.get("thread_ts"),
            is_bot=message_data.get("bot_id") is not None,
            mentions_me=mentions_me
        )
    
    def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get cached user info"""
        if user_id not in self._user_info_cache:
            try:
                response = self.client.users_info(user=user_id)
                self._user_info_cache[user_id] = response["user"]
            except SlackApiError:
                self._user_info_cache[user_id] = {"name": "unknown", "real_name": "Unknown User"}
        return self._user_info_cache[user_id]
    
    def _get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Get cached channel info"""
        if channel_id not in self._channel_info_cache:
            try:
                response = self.client.conversations_info(channel=channel_id)
                self._channel_info_cache[channel_id] = response["channel"]
            except SlackApiError:
                self._channel_info_cache[channel_id] = {"id": channel_id, "name": "unknown"}
        return self._channel_info_cache[channel_id]
    
    async def fetch_mentions(self, hours: int = 24) -> List[SlackMessage]:
        """Fetch messages where user is mentioned"""
        if not self.user_id:
            await self.initialize()
        
        messages = []
        oldest = self._get_timestamp_filter(hours)
        
        try:
            # Search for mentions
            query = f"<@{self.user_id}>"
            response = self.client.search_messages(
                query=query,
                sort="timestamp",
                sort_dir="desc"
            )
            
            for message in response.get("messages", {}).get("matches", []):
                # Filter by time
                if float(message.get("ts", 0)) < oldest:
                    continue
                
                channel_info = self._get_channel_info(message.get("channel", {}).get("id", ""))
                slack_message = self._parse_slack_message(
                    message, channel_info, ActivityType.MENTION
                )
                messages.append(slack_message)
            
            print(f"📍 Found {len(messages)} mentions")
            return messages
            
        except SlackApiError as e:
            print(f"❌ Error fetching mentions: {e.response['error']}")
            return []
    
    async def fetch_direct_messages(self, hours: int = 24) -> List[SlackMessage]:
        """Fetch direct messages"""
        messages = []
        oldest = self._get_timestamp_filter(hours)
        
        try:
            # Get DM conversations
            response = self.client.conversations_list(types="im")
            dm_channels = response.get("channels", [])
            
            for channel in dm_channels:
                try:
                    # Get messages from this DM
                    history_response = self.client.conversations_history(
                        channel=channel["id"],
                        oldest=oldest,
                        limit=100
                    )
                    
                    for message in history_response.get("messages", []):
                        # Skip own messages and bot messages
                        if message.get("user") == self.user_id or message.get("bot_id"):
                            continue
                        
                        slack_message = self._parse_slack_message(
                            message, channel, ActivityType.DM
                        )
                        messages.append(slack_message)
                        
                except SlackApiError:
                    continue
            
            print(f"💬 Found {len(messages)} DMs")
            return messages
            
        except SlackApiError as e:
            print(f"❌ Error fetching DMs: {e.response['error']}")
            return []
    
    async def fetch_thread_replies(self, hours: int = 24) -> List[SlackMessage]:
        """Fetch replies to threads user participated in"""
        messages = []
        oldest = self._get_timestamp_filter(hours)
        
        try:
            # This is more complex - we need to find threads user participated in
            # For now, implement a simplified version that checks recent channels
            
            response = self.client.conversations_list(
                types="public_channel,private_channel",
                limit=50
            )
            
            for channel in response.get("channels", []):
                try:
                    # Get recent messages
                    history_response = self.client.conversations_history(
                        channel=channel["id"],
                        oldest=oldest,
                        limit=100
                    )
                    
                    for message in history_response.get("messages", []):
                        # Check if this is a thread reply and user is involved
                        if (message.get("thread_ts") and 
                            message.get("user") != self.user_id and
                            not message.get("bot_id")):
                            
                            # Check if user participated in thread
                            try:
                                replies_response = self.client.conversations_replies(
                                    channel=channel["id"],
                                    ts=message.get("thread_ts")
                                )
                                
                                # Check if user has any messages in this thread
                                user_in_thread = any(
                                    reply.get("user") == self.user_id 
                                    for reply in replies_response.get("messages", [])
                                )
                                
                                if user_in_thread:
                                    slack_message = self._parse_slack_message(
                                        message, channel, ActivityType.THREAD_REPLY
                                    )
                                    messages.append(slack_message)
                                    
                            except SlackApiError:
                                continue
                                
                except SlackApiError:
                    continue
            
            print(f"🧵 Found {len(messages)} thread replies")
            return messages
            
        except SlackApiError as e:
            print(f"❌ Error fetching thread replies: {e.response['error']}")
            return []
    
    async def fetch_channel_activities(self, hours: int = 24, limit_channels: int = 20) -> List[SlackMessage]:
        """Fetch activities from channels user is active in"""
        messages = []
        oldest = self._get_timestamp_filter(hours)
        
        try:
            # Get channels user is member of
            response = self.client.conversations_list(
                types="public_channel,private_channel",
                limit=limit_channels
            )
            
            for channel in response.get("channels", []):
                try:
                    # Get recent messages
                    history_response = self.client.conversations_history(
                        channel=channel["id"],
                        oldest=oldest,
                        limit=50
                    )
                    
                    for message in history_response.get("messages", []):
                        # Skip own messages, bot messages, and already processed mentions
                        if (message.get("user") == self.user_id or 
                            message.get("bot_id") or
                            f"<@{self.user_id}>" in message.get("text", "")):
                            continue
                        
                        slack_message = self._parse_slack_message(
                            message, channel, ActivityType.CHANNEL_MESSAGE
                        )
                        messages.append(slack_message)
                        
                except SlackApiError:
                    continue
            
            print(f"📢 Found {len(messages)} channel activities")
            return messages
            
        except SlackApiError as e:
            print(f"❌ Error fetching channel activities: {e.response['error']}")
            return []
    
    async def collect_all_activities(self, hours: int = 24) -> List[SlackMessage]:
        """Collect all types of activities"""
        print(f"🔍 Collecting Slack activities from last {hours} hours...")
        
        # Initialize if needed
        if not self.user_id:
            await self.initialize()
        
        # Collect all activity types in parallel
        activities = []
        
        try:
            # Run all fetching operations concurrently
            results = await asyncio.gather(
                self.fetch_mentions(hours),
                self.fetch_direct_messages(hours),
                self.fetch_thread_replies(hours),
                self.fetch_channel_activities(hours),
                return_exceptions=True
            )
            
            # Combine results
            for result in results:
                if isinstance(result, list):
                    activities.extend(result)
                elif isinstance(result, Exception):
                    print(f"⚠️ Warning: {result}")
            
            # Remove duplicates based on message_id and channel_id
            seen = set()
            unique_activities = []
            for activity in activities:
                key = (activity.message_id, activity.channel_id)
                if key not in seen:
                    seen.add(key)
                    unique_activities.append(activity)
            
            print(f"✅ Collected {len(unique_activities)} unique activities")
            return unique_activities
            
        except Exception as e:
            print(f"❌ Error collecting activities: {e}")
            return []


# Test the client
if __name__ == "__main__":
    async def test_client():
        client = SlackClient()
        activities = await client.collect_all_activities(hours=24)
        
        if activities:
            print(f"\n📋 Sample activities:")
            for i, activity in enumerate(activities[:3]):  # Show first 3
                print(f"{i+1}. [{activity.activity_type}] {activity.username}: {activity.text[:50]}...")
        else:
            print("No activities found or authentication failed.")
    
    # Uncomment to test
    # asyncio.run(test_client())
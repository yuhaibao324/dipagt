import datetime
import uuid
from peewee import *
from playhouse.postgres_ext import *
from dotenv import load_dotenv

from app.db.database import db

load_dotenv()

class BaseModel(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        return super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        database = db

class Agent(BaseModel):
    name = CharField(max_length=100)
    description = TextField(null=True)
    type = CharField(max_length=50)  # e.g., "assistant", "user", "system"
    avatar = CharField(null=True) # Add avatar field
    config = JSONField(null=True)  # Store agent-specific configuration
    is_active = BooleanField(default=True)

    class Meta:
        database = db
        indexes = (
            (('name',), False),
            (('type',), False),
            (('is_active',), False),
        )

class Tool(BaseModel):
    name = CharField(max_length=100)
    description = TextField()
    function_name = CharField(max_length=100)
    parameters = JSONField()  # Store tool parameters schema
    is_active = BooleanField(default=True)

    class Meta:
        database = db
        indexes = (
            (('name',), True),  # Unique tool names
            (('function_name',), True),  # Unique function names
            (('is_active',), False),
        )

# Many-to-many relationship between Agent and Tool
class AgentTool(BaseModel):
    agent = ForeignKeyField(Agent, backref='agent_tools')
    tool = ForeignKeyField(Tool, backref='agent_tools')
    config = JSONField(null=True)  # Store tool-specific configuration for this agent

    class Meta:
        indexes = (
            (('agent', 'tool'), True),  # Unique together
        )

class Chat(BaseModel):
    title = CharField(max_length=200)
    description = TextField(null=True)
    status = CharField(max_length=50, default='active')  # active, archived, completed
    metadata = JSONField(null=True)
    owner = CharField(max_length=100)  # Add owner field

    class Meta:
        database = db
        indexes = (
            (('title',), False),
            (('status',), False),
            (('owner',), False),  # Add index for owner field
            (('created_at',), False),  # For sorting chats by creation time
        )

class Message(BaseModel):
    chat = ForeignKeyField(Chat, backref='messages')
    agent_id = UUIDField(null=True, constraints=[SQL('DEFAULT NULL')])  # Explicitly set as nullable
    content = TextField()
    role = CharField(max_length=50)  # e.g., "user", "assistant", "system"
    type = CharField(max_length=50, default='text')  # text, image, file, etc.
    metadata = JSONField(null=True)

    class Meta:
        database = db
        indexes = (
            (('chat',), False),  # For retrieving messages by chat
            (('agent_id',), False),  # For retrieving messages by agent
            (('role',), False),
            (('type',), False),
            (('created_at',), False),  # For chronological sorting
        )

class Task(BaseModel):
    name = CharField(max_length=200)
    description = TextField(null=True)
    status = CharField(max_length=50, default='pending')  # pending, running, completed, failed
    parent = ForeignKeyField('self', null=True, backref='subtasks')
    chat = ForeignKeyField(Chat, backref='tasks')
    # Removed the direct agent ForeignKey and replaced with JSONField for agent IDs
    agents = JSONField(null=True)  # Store array of agent IDs involved in this task
    input_data = JSONField(null=True)
    output_data = JSONField(null=True)
    metadata = JSONField(null=True)

    class Meta:
        database = db
        indexes = (
            (('name',), False),
            (('status',), False),
            (('parent',), False),  # For retrieving subtasks
            (('chat',), False),  # For retrieving tasks by chat
            (('created_at',), False),  # For sorting tasks by creation time
        )


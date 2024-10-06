# DatabaseManager API Documentation

## Related Modules
- [DeerTick Main](deertick_doc.md)
- [Web Crawler](crawler_doc.md)
- [Dynamic Blog Scraper](scraper_doc.md)
- [Discord Bot](bot_doc.md)

This module manages database operations for the DeerTick project. For an overview of how it fits into the larger system, see the [DeerTick Main Documentation](deertick_doc.md).

## Initialization
```python
db_manager = DatabaseManager(config_file='config.ini')
```

## Database Schema

```mermaid
classDiagram
    class bots {
        UUID id PK
        BIGINT guild_id
        BIGINT bot_id
        TEXT bot_name
    }
    
    class agents {
        UUID id PK
        UUID bot_id FK
        TEXT model
        TEXT system_prompt
        TEXT provider
        TEXT nickname
        TEXT color
        TEXT font
        INTEGER max_tokens
        INTEGER min_tokens
        FLOAT temperature
        FLOAT presence_penalty
        FLOAT frequency_penalty
        INTEGER top_k
        FLOAT top_p
        FLOAT repetition_penalty
        FLOAT min_p
        FLOAT top_a
        INTEGER seed
        JSONB logit_bias
        BOOLEAN logprobs
        INTEGER top_logprobs
        JSONB response_format
        JSONB stop
        JSONB tool_choice
        TEXT prompt_template
        TEXT tts_path
        TEXT img_path
        TEXT output_format
        INTEGER num_outputs
        FLOAT lora_scale
        TEXT aspect_ratio
        FLOAT guidance_scale
        INTEGER num_inference_steps
        BOOLEAN disable_safety_checker
        TEXT audio_path
        JSONB tools
        TEXT created_by
        TIMESTAMP created_at
        TIMESTAMP updated_at
        JSONB history
        BOOLEAN is_active
    }
    
    class messages {
        UUID id PK
        BIGINT guild_id
        BIGINT channel_id
        BIGINT user_id
        TEXT username
        BOOLEAN is_bot
        UUID bot_id FK
        TIMESTAMP timestamp
        TEXT content
        TEXT bot_name
    }
    
    class error_log {
        UUID id PK
        TIMESTAMP timestamp
        TEXT agent_name
        TEXT error
        BIGINT channel_id
        BIGINT guild_id
        TEXT context
    }
    
    class agent_server_channels {
        UUID id PK
        UUID agent_id FK
        BIGINT guild_id
        BIGINT channel_id
        BOOLEAN is_enabled
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    class admins {
        UUID id PK
        BIGINT user_id
        BIGINT guild_id
        TIMESTAMP created_at
    }
    
    class scraped_data {
        UUID id PK
        TEXT url
        TEXT title
        TEXT content
        TEXT full_text
        TIMESTAMP created_at
    }
    
    class normal_crawl_data {
        UUID id PK
        TEXT url
        TEXT links
        TEXT selenium_required
        TEXT description
        TEXT errors
        TEXT additional_notes
        TIMESTAMP created_at
    }
    
    class deep_crawl_data {
        UUID id PK
        TEXT url
        TEXT selenium_required
        TEXT elements
        TEXT challenges
        TEXT notes
        TEXT important_elements
        TIMESTAMP created_at
    }
    
    bots "1" -- "*" agents : has
    bots "1" -- "*" messages : sends
    agents "1" -- "*" agent_server_channels : enabled_in
    agents "1" -- "*" error_log : logs_errors
````


This Mermaid class diagram shows all the tables in your database, their attributes, and the relationships between them. Here's a brief explanation of the relationships:

1. A `bot` can have multiple `agents` (one-to-many relationship).
2. A `bot` can send multiple `messages` (one-to-many relationship).
3. An `agent` can be enabled in multiple `agent_server_channels` (one-to-many relationship).
4. An `agent` can log multiple errors in the `error_log` (one-to-many relationship).

The other tables (`admins`, `scraped_data`, `normal_crawl_data`, and `deep_crawl_data`) are not directly related to the other tables in this schema.

You can add this diagram to your `db_doc.md` file to provide a visual representation of your database schema.

## Methods

### create_pool()
Establishes a connection pool to the database.
```python
await db_manager.create_pool()
```

### create_tables()
Creates necessary tables in the database if they don't exist.
```python
await db_manager.create_tables()
```

### load_agents_from_db()
Loads all agents from the database. Decodes fields: 'bot_name', 'system_prompt', 'logit_bias', 'response_format', 'stop', 'tool_choice', 'tools', 'history'.
```python
agents = await db_manager.load_agents_from_db()
```

### log_error(agent_name, error_message, channel_id, guild_id, context)
Logs an error to the database. No encoding/decoding.
```python
await db_manager.log_error(agent_name, error_message, channel_id, guild_id, context)
```

### log_message(guild_id, channel_id, user_id, username, content, is_bot_message)
Logs a message to the database. Encodes 'username' and 'content'.
```python
await db_manager.log_message(guild_id, channel_id, user_id, username, content, is_bot_message)
```

### get_context(channel_id)
Retrieves the context for a given channel. Decodes 'content' field.
```python
context = await db_manager.get_context(channel_id)
```

### get_or_create_bot(guild_id, bot_id, bot_name)
Gets an existing bot or creates a new one if it doesn't exist. No encoding/decoding.
```python
bot_id = await db_manager.get_or_create_bot(guild_id, bot_id, bot_name)
```

### delete_agent(agent_name)
Deletes an agent from the database. No encoding/decoding.
```python
await db_manager.delete_agent(agent_name)
```

### get_agent(agent_name)
Retrieves an agent's data from the database. Decoding happens in load_agents_from_db().
```python
agent_data = await db_manager.get_agent(agent_name)
```

### backup_database()
Creates a backup of the entire database. Decodes all fields when creating CSV files.
```python
backups = await db_manager.backup_database()
```

### get_last_bot_message(channel_id)
Retrieves the last bot message for a given channel. Decodes 'username' and 'content'.
```python
last_message = await db_manager.get_last_bot_message(channel_id)
```

### update_agent(agent_name, updated_data)
Updates an agent's data in the database. Encodes 'logit_bias', 'response_format', 'stop', 'tool_choice', 'tools'.
```python
await db_manager.update_agent(agent_name, updated_data)
```

### add_agent_to_channel(agent_id, guild_id, channel_id, user_id)
Adds an agent to a channel. No encoding/decoding.
```python
success = await db_manager.add_agent_to_channel(agent_id, guild_id, channel_id, user_id)
```

### remove_agent_from_channel(agent_id, guild_id, channel_id, user_id)
Removes an agent from a channel. No encoding/decoding.
```python
success = await db_manager.remove_agent_from_channel(agent_id, guild_id, channel_id, user_id)
```

### get_enabled_agents_for_channel(guild_id, channel_id)
Gets enabled agents for a channel. No encoding/decoding.
```python
enabled_agents = await db_manager.get_enabled_agents_for_channel(guild_id, channel_id)
```

### update_agent_history(agent_name, new_history_entry)
Updates an agent's history. Encodes the new history entry.
```python
await db_manager.update_agent_history(agent_name, new_history_entry)
```

### insert_scraped_data(url, title, content, full_text)
Inserts scraped data into the database. Encodes all fields.
```python
await db_manager.insert_scraped_data(url, title, content, full_text)
```

### insert_normal_crawl_data(url, links, selenium_required, description, errors, additional_notes)
Inserts normal crawl data into the database. Encodes all fields.
```python
await db_manager.insert_normal_crawl_data(url, links, selenium_required, description, errors, additional_notes)
```

### insert_deep_crawl_data(url, selenium_required, elements, challenges, notes, important_elements)
Inserts deep crawl data into the database. Encodes all fields.
```python
await db_manager.insert_deep_crawl_data(url, selenium_required, elements, challenges, notes, important_elements)
```

### update_agent_prompt(agent_name, prompt)
Updates the system prompt for a specific agent. Encodes the prompt.
```python
await db_manager.update_agent_prompt(agent_name, prompt)
```

### agent_exists(agent_name)
Checks if an agent with the given name exists in the database. No encoding/decoding.
```python
exists = await db_manager.agent_exists(agent_name)
```

### create_agent(bot_id, model, system_prompt, provider, nickname, ...)
Creates a new agent in the database. Encodes complex fields like system_prompt, logit_bias, etc.
```python
agent_id = await db_manager.create_agent(bot_id, model, system_prompt, provider, nickname, ...)
```

### add_admin(user_id, guild_id)
Adds a user as an admin for a specific guild. No encoding/decoding.
```python
await db_manager.add_admin(user_id, guild_id)
```

### remove_admin(user_id, guild_id)
Removes a user from the admin list for a specific guild. No encoding/decoding.
```python
await db_manager.remove_admin(user_id, guild_id)
```

### is_admin(user_id, guild_id)
Checks if a user is an admin for a specific guild. No encoding/decoding.
```python
is_admin = await db_manager.is_admin(user_id, guild_id)
```

### create_scraped_data_table()
Creates the scraped_data table if it doesn't exist. No encoding/decoding.
```python
await db_manager.create_scraped_data_table()
```

### insert_multiple_scraped_data(data_list)
Inserts multiple scraped data entries into the database. Encodes all fields.
```python
await db_manager.insert_multiple_scraped_data(data_list)
```

### create_crawler_tables()
Creates tables for normal and deep crawl data if they don't exist. No encoding/decoding.
```python
await db_manager.create_crawler_tables()
```

## Utility Methods

### encode_data(data)
Encodes data for storage in the database. Used internally by other methods.
```python
encoded_data = db_manager.encode_data(data)
```

### decode_data(data)
Decodes data retrieved from the database. Used internally by other methods.
```python
decoded_data = db_manager.decode_data(data)
```

Note: It's important to be aware of which fields are being encoded and decoded, especially when working with complex data structures or when you need to ensure data consistency across different parts of your application.

### is_agent_creator(user_id, agent_name)
Checks if a user is the creator of a specific agent. No encoding/decoding.
```python
is_creator = await db_manager.is_agent_creator(user_id, agent_name)
```
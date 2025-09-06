# Chroma Memory Directory

## Purpose
This directory contains the persistent storage for ChromaDB vector embeddings and metadata used by the conversation memory system.

## What's Stored Here
ChromaDB automatically creates and manages files in this directory to provide persistent storage for:

### Vector Embeddings
- **User questions** converted to numerical vectors using sentence-transformers
- **Semantic representations** that enable similarity search across past conversations
- **Multi-dimensional vectors** (384 dimensions from `all-MiniLM-L6-v2` model)

### Conversation Metadata  
- **User identifiers** for memory isolation between different users
- **Agent types** (normal vs strict) for contextual search
- **Programming languages** discussed in conversations
- **Difficulty levels** and learning progression
- **Timestamps** and interaction context

### ChromaDB Internal Files
- **Database files** (`.sqlite` format internally)
- **Index files** for fast vector similarity search
- **Configuration metadata** for the collection schema

## Directory Structure
```
chroma_memory/
├── CLAUDE.md              # This documentation file
├── [uuid-based-files]     # ChromaDB internal storage files
└── [index-files]          # Vector search optimization files
```

**Note**: The exact file structure is managed by ChromaDB and may include:
- SQLite database files
- Vector index files  
- Metadata storage files
- Collection configuration files

## Memory System Integration

### How It Works
1. **User asks question** → API receives message
2. **Create embedding** → Sentence transformer converts text to vector
3. **Search similar** → ChromaDB finds past conversations with similar vectors
4. **Store interaction** → New question + response stored for future reference
5. **Learn patterns** → System builds understanding of user's learning journey

### Configuration
- **Collection name**: `conversation_memories`
- **Embedding model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Similarity metric**: Cosine similarity
- **Persistence**: Local file storage (Railway deployment compatible)

## Data Privacy & Security

### User Isolation
- Each user's memories are tagged with unique user IDs
- Cross-user data access is prevented by metadata filtering
- No personal data stored beyond conversation content

### Data Retention
- Conversations stored indefinitely for learning continuity
- Future cleanup mechanism planned for old memories
- Users can request data deletion (GDPR compliance ready)

## Backup & Migration

### Backup Strategy
```bash
# Backup the entire directory
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_memory/

# Restore backup
tar -xzf chroma_backup_YYYYMMDD.tar.gz
```

### Migration Path
For future upgrades to pgvector:
1. Export embeddings from ChromaDB
2. Transform to PostgreSQL format
3. Import to pgvector tables
4. Update connection configuration

## Development Notes

### Local Development
- Directory created automatically on first API startup
- Safe to delete for fresh start (loses conversation history)
- Gitignored to prevent committing user data

### Production Deployment
- Railway provides persistent file storage
- Directory survives container restarts
- Scales with conversation volume

### Performance Characteristics
- **Fast similarity search** (< 100ms for thousands of conversations)
- **Low memory footprint** (vectors stored on disk)
- **Incremental indexing** (new conversations indexed automatically)

## Troubleshooting

### If Memory Search Fails
1. Check if directory exists and is writable
2. Verify ChromaDB dependency installation
3. Check disk space availability
4. Review error logs for specific issues

### If Performance Degrades
1. Consider periodic index optimization
2. Implement memory cleanup for old conversations
3. Monitor disk usage growth
4. Plan migration to pgvector for larger scale

## Monitoring

### Health Checks
The API `/stats` endpoint reports memory store status:
```json
{
  "memory_store": {
    "total_memories": 1247,
    "status": "operational"
  }
}
```

### Key Metrics to Track
- **Total stored conversations** (growth over time)
- **Average similarity scores** (search quality)
- **Storage size** (disk usage monitoring)
- **Query response times** (performance tracking)

## Future Enhancements

### Planned Improvements
- **Automatic cleanup** of very old memories
- **User-specific retention policies**
- **Enhanced metadata** for better categorization
- **Migration tools** for pgvector transition

### Integration Possibilities
- **Analytics dashboard** for learning patterns
- **Export functionality** for user data portability
- **Advanced search filters** (by date, topic, difficulty)
- **Conversation clustering** for curriculum recommendations
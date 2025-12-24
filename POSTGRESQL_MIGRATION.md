# PostgreSQL Migration Guide

## 🚀 Quick Start

### 1. Start PostgreSQL Container

```bash
# Start only PostgreSQL
docker-compose up postgres -d

# Or start all services
docker-compose up --build
```

### 2. Run Migration Script

```bash
# Option 1: Inside Docker container
docker exec -it movie-backend python scripts/migrate_to_postgresql.py

# Option 2: Local Python (if you have PostgreSQL running locally)
cd app
python scripts/migrate_to_postgresql.py
```

### 3. Verify Migration

```bash
# Connect to PostgreSQL
docker exec -it movie-postgres psql -U filmflow_user -d filmflow

# Check tables
\dt

# Check counts
SELECT COUNT(*) FROM movies;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM ratings;
SELECT COUNT(*) FROM reviews;

# Exit
\q
```

## 📊 Database Schema

### Tables

#### users
- `id` - Primary key
- `user_id` - Unique user identifier (string)
- `name` - User name
- `email` - User email (unique)
- `created_at`, `updated_at` - Timestamps

#### movies
- `id` - Primary key
- `movie_id` - Unique movie identifier (string)
- `title` - Movie title
- `genres` - JSON array of genres
- `overview`, `tagline` - Descriptions
- `cast_data` - JSON cast information
- `poster_url`, `poster_path` - Images
- `year`, `release_date` - Release info
- `vote_average`, `vote_count`, `popularity` - Ratings
- Indexes on: movie_id, title, year, vote_average, popularity

#### ratings
- `id` - Primary key
- `user_id` - Foreign key to users
- `movie_id` - Foreign key to movies  
- `rating` - Float rating value
- `timestamp` - When rated
- Index on: (user_id, movie_id)

#### reviews
- `id` - Primary key
- `movie_id` - Foreign key to movies
- `user_id` - Foreign key to users
- `username` - Display name
- `rating` - Integer 1-5
- `review_text` - Review content
- `helpful_count` - Upvotes
- `timestamp` - When posted

#### watch_history
- `id` - Primary key
- `user_id` - Foreign key to users
- `movie_id` - Foreign key to movies
- `watched_at` - When watched
- `progress` - Watch progress (0-100%)
- `completed` - Boolean

#### watchlist
- `id` - Primary key
- `user_id` - Foreign key to users
- `movie_id` - Foreign key to movies
- `added_at` - When added

## 🔧 Manual Database Operations

### Create Database Manually

```bash
# Connect to PostgreSQL
docker exec -it movie-postgres psql -U filmflow_user

# Create database
CREATE DATABASE filmflow;

# Connect to database
\c filmflow

# Create extensions (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Backup Database

```bash
# Backup
docker exec movie-postgres pg_dump -U filmflow_user filmflow > backup.sql

# Restore
docker exec -i movie-postgres psql -U filmflow_user filmflow < backup.sql
```

### Reset Database

```bash
# Drop all tables
docker exec -it movie-postgres psql -U filmflow_user -d filmflow -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-run migration
docker exec -it movie-backend python scripts/migrate_to_postgresql.py
```

## 🐛 Troubleshooting

### Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs movie-postgres

# Test connection
docker exec movie-postgres pg_isready -U filmflow_user -d filmflow
```

### Permission Errors

```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE filmflow TO filmflow_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO filmflow_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO filmflow_user;
```

### Performance Tuning

```sql
-- Create additional indexes
CREATE INDEX idx_movie_title_search ON movies USING gin(to_tsvector('english', title));
CREATE INDEX idx_movie_genres ON movies USING gin(genres);

-- Analyze tables
ANALYZE movies;
ANALYZE ratings;
```

## 📝 Environment Variables

Add to `.env` file:

```bash
DATABASE_URL=postgresql://filmflow_user:filmflow_pass123@localhost:5432/filmflow
POSTGRES_DB=filmflow
POSTGRES_USER=filmflow_user
POSTGRES_PASSWORD=filmflow_pass123
```

## 🔄 Migration Checklist

- [ ] Start PostgreSQL container
- [ ] Verify connection
- [ ] Run migration script
- [ ] Verify data counts
- [ ] Test API endpoints
- [ ] Check query performance
- [ ] Backup database
- [ ] Update application code to use new DB
- [ ] Test all features
- [ ] Monitor logs for errors

## 📈 Performance Tips

1. **Use Indexes**: Already created on common query fields
2. **Connection Pooling**: Configured in db_postgresql.py
3. **Batch Operations**: Use bulk_save_objects() for inserts
4. **Query Optimization**: Use `.limit()`, `.offset()` for pagination
5. **Caching**: Consider Redis for frequent queries

## 🔒 Security

1. **Change Default Password**: Update docker-compose.yml
2. **Use Environment Variables**: Don't commit passwords
3. **SSL Connection**: Enable in production
4. **Regular Backups**: Schedule automatic backups
5. **User Permissions**: Follow principle of least privilege

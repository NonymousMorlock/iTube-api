iTube-api
==========

Overview
--------

The iTube-api is the core backend API service for the iTube video platform. Built with FastAPI, it handles user authentication (via AWS Cognito), video metadata management, presigned URL generation for S3 uploads, and provides IAM-authenticated endpoints for internal microservices. In short: the central brain of the video platform.

Key responsibilities
--------------------

- **User authentication**: AWS Cognito integration with cookie-based sessions
- **Video upload orchestration**: Generate presigned S3 URLs for client-side uploads
- **Video metadata management**: Store and retrieve video information (title, description, visibility, processing status)
- **Internal service APIs**: IAM-authenticated endpoints for transcoder service communication
- **Video discovery**: Public APIs for listing and retrieving processed videos
- **Database management**: PostgreSQL for persistent storage with SQLAlchemy ORM
- **Caching layer**: Redis integration for video metadata caching
- **Logging & observability**: Structured logging with request tracking

Architecture
------------

```
┌──────────┐     HTTP/REST       ┌─────────────┐
│  Client  │ ◄─────────────────► │  iTube-api  │
│ (Web/App)│   Cookie Auth       │   FastAPI   │
└──────────┘                     └──────┬──────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              ┌──────────┐        ┌──────────┐      ┌──────────┐
              │   AWS    │        │PostgreSQL│      │  Redis   │
              │ Cognito  │        │  Database│      │  Cache   │
              └──────────┘        └──────────┘      └──────────┘
                    │                   │
                    │                   │
                    ▼                   ▼
              ┌──────────┐        ┌──────────┐
              │    S3    │        │   SQS    │
              │  Buckets │        │  Queue   │
              └──────────┘        └──────────┘
                    ▲
                    │ AWS SigV4 (IAM Auth)
                    │
              ┌─────┴──────┐
              │ Transcoder │
              │   Service  │
              └────────────┘
```

API Endpoints
-------------

### Public Endpoints (User Authentication)

- **POST** `/api/v1/auth/register` - User registration
- **POST** `/api/v1/auth/login` - User login (returns cookie)
- **POST** `/api/v1/auth/logout` - User logout
- **GET** `/api/v1/auth/me` - Get current user info

### Video Endpoints (Requires User Auth)

- **POST** `/api/v1/upload/videos/upload-url` - Get presigned URL for video upload
- **POST** `/api/v1/upload/videos/thumbnail/upload-url` - Get presigned URL for thumbnail upload
- **POST** `/api/v1/upload/videos/metadata` - Save video metadata after upload
- **GET** `/api/v1/upload/videos/` - List all public completed videos
- **GET** `/api/v1/upload/videos/{video_id}` - Get specific video details

### Internal Service Endpoints (Requires IAM Auth)

- **GET** `/api/v1/upload/videos/by-key/{s3_key}` - Lookup video ID by S3 key (for transcoder)
- **PATCH** `/api/v1/upload/videos/{video_id}/status` - Update processing status (for transcoder)

Prerequisites
-------------

- **Python 3.11+** (for local development)
- **PostgreSQL 16** (database)
- **Redis 7** (caching layer)
- **AWS Account** with:
  - AWS Cognito user pool configured
  - S3 buckets for raw videos, processed videos, and thumbnails
  - IAM credentials with S3 access
- **Docker** (optional, for containerized development)

Environment variables
---------------------

Create a `.env` file (copy from `.env.example` if available) or set these environment variables:

### Database
- `POSTGRES_DATABASE_URL` — PostgreSQL connection string (e.g., `postgresql://user:pass@localhost:5432/itube`)
- `POSTGRES_USER` — Database username
- `POSTGRES_PASSWORD` — Database password
- `POSTGRES_DB` — Database name

### AWS Cognito
- `COGNITO_CLIENT_ID` — AWS Cognito app client ID
- `COGNITO_CLIENT_SECRET` — AWS Cognito app client secret

### AWS Configuration
- `REGION_NAME` — AWS region (e.g., `us-east-1`)
- `AWS_ACCESS_KEY_ID` — AWS access key
- `AWS_SECRET_ACCESS_KEY` — AWS secret key

### S3 Buckets
- `S3_RAW_VIDEOS_BUCKET` — Bucket for raw uploaded videos
- `S3_PROCESSED_VIDEOS_BUCKET` — Bucket for transcoded videos
- `S3_VIDEO_THUMBNAILS_BUCKET` — Bucket for video thumbnails

### Redis
- `REDIS_HOST` — Redis server hostname (default: `localhost`)
- `REDIS_PORT` — Redis server port (default: `6379`)

Do NOT commit `.env`
--------------------

Seriously — don't commit `.env` to version control. Treat it like your browser history: deeply personal and best kept private. Add `.env` to `.gitignore` if it's not already there.

Local development (quick start)
-------------------------------

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up infrastructure (PostgreSQL & Redis)

**Option A: Docker Compose (Recommended)**

```bash
# From iTube-api/ directory
docker compose up -d db redis

# Wait a few seconds for services to initialize
sleep 5
```

This starts PostgreSQL on port 5433 and Redis on port 6379.

**Option B: Local Installation**

Install PostgreSQL and Redis locally, then create the database:

```bash
createdb itube
redis-server
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your AWS credentials and Cognito configuration
```

Example `.env`:

```env
POSTGRES_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/itube
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=itube

COGNITO_CLIENT_ID=your_cognito_client_id
COGNITO_CLIENT_SECRET=your_cognito_client_secret

REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

S3_RAW_VIDEOS_BUCKET=itube-raw-videos
S3_PROCESSED_VIDEOS_BUCKET=itube-processed-videos
S3_VIDEO_THUMBNAILS_BUCKET=itube-thumbnails

REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. Initialize the database

The application automatically creates tables on startup via `init_db()` in `app/core/database.py`. For production, consider using Alembic for migrations.

### 5. Run the API server

```bash
# Export environment variables
export $(grep -v '^#' .env | xargs)

# Run with uvicorn (development server with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

Docker: build and run locally
------------------------------

The repository includes a `Dockerfile` and `docker-compose.yml` for full-stack local development.

### Run entire stack (API + Database + Redis)

```bash
# From iTube-api/ directory
docker compose build
docker compose up
```

This starts:
- API server on port 8000
- PostgreSQL on port 5433
- Redis on port 6379

### Build and run API container only

```bash
docker build -t itube-api .
docker run --env-file .env -p 8000:8000 itube-api
```

Project structure
-----------------

```
iTube-api/
├── app/
│   ├── main.py                    # FastAPI application entrypoint
│   ├── auth/                      # Authentication module
│   │   ├── routes.py              # Auth endpoints (register, login, logout)
│   │   ├── service.py             # Auth business logic
│   │   ├── repository.py          # User database operations
│   │   ├── models.py              # User SQLAlchemy models
│   │   └── schemas.py             # Pydantic schemas for auth
│   ├── video/                     # Video management module
│   │   ├── routes.py              # Video endpoints (upload, metadata, status)
│   │   ├── service.py             # Video business logic
│   │   ├── repository.py          # Video database operations
│   │   ├── models.py              # Video SQLAlchemy models
│   │   └── schemas.py             # Pydantic schemas for videos
│   └── core/                      # Core utilities and configuration
│       ├── config.py              # Environment configuration (Pydantic Settings)
│       ├── database.py            # SQLAlchemy database setup
│       ├── redis.py               # Redis client configuration
│       ├── cognito.py             # AWS Cognito client setup
│       ├── security.py            # Password hashing utilities
│       ├── logging_config.py      # Structured logging setup
│       ├── exceptions.py          # Custom exception classes
│       ├── error_handlers.py      # FastAPI exception handlers
│       └── middleware/
│           ├── auth_user.py       # Authentication dependencies
│           └── access_log.py      # Request logging middleware
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container image definition
├── docker-compose.yml             # Local development stack
└── README.md                      # This file
```

Authentication methods
----------------------

The API supports two authentication methods depending on the endpoint:

### 1. User Authentication (Cookie-based)

For client-facing endpoints (user registration, video uploads, listing videos):

- **Method**: AWS Cognito with HTTP-only cookies
- **Flow**:
  1. User logs in via `/api/v1/auth/login`
  2. API validates credentials with AWS Cognito
  3. Access token stored in secure HTTP-only cookie
  4. Subsequent requests include cookie automatically
- **Protected by**: `get_current_user()` dependency
- **Endpoints**: `/api/v1/auth/*`, `/api/v1/upload/videos/*` (except internal endpoints)

### 2. IAM Authentication (AWS SigV4)

For internal microservice communication (transcoder → API):

- **Method**: AWS Signature Version 4 (SigV4)
- **Flow**:
  1. Transcoder signs requests using ECS task role credentials
  2. API Gateway verifies signature (recommended) or API validates headers
  3. Request forwarded to API with verified credentials
- **Protected by**: `verify_iam_auth()` dependency
- **Endpoints**: `/api/v1/upload/videos/by-key/*`, `/api/v1/upload/videos/{id}/status`
- **Production setup**: See `API_GATEWAY_SETUP.md` in the project root

Database migrations
-------------------

Currently, the application uses SQLAlchemy's `Base.metadata.create_all()` for automatic table creation on startup. For production deployments, consider implementing proper database migrations with **Alembic**:

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic

# Generate migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

Logging and error handling
---------------------------

- **Logging**: Configured centrally in `app/core/logging_config.py`. Uses structured logging with JSON format for production readiness.
- **Error handlers**: Global exception handlers in `app/core/error_handlers.py` catch and format errors consistently.
- **Access logs**: Custom middleware (`AccessLogMiddleware`) logs all HTTP requests with timing information.
- **Validation errors**: Pydantic schemas provide automatic request/response validation with detailed error messages.

Video upload workflow
---------------------

Understanding how videos flow through the system:

1. **Client requests upload URL**: `POST /api/v1/upload/videos/upload-url`
   - API generates unique S3 key: `videos/{user_id}/{uuid}`
   - Returns presigned S3 URL valid for direct upload
   
2. **Client uploads to S3**: Direct browser → S3 upload (no API involved)
   - Uses presigned URL
   - Faster, doesn't burden API server
   
3. **Client submits metadata**: `POST /api/v1/upload/videos/metadata`
   - Title, description, S3 key, visibility
   - Creates database record with status `IN_PROGRESS`
   - S3 event triggers SQS → Consumer → Transcoder
   
4. **Transcoder processes video**:
   - Downloads from S3
   - Transcodes to multiple formats/resolutions
   - Uploads processed files to processed bucket
   - Calls API: `GET /videos/by-key/{s3_key}` (lookup video ID)
   - Calls API: `PATCH /videos/{video_id}/status?status=COMPLETED`
   
5. **Video available**: Status changes to `COMPLETED`, visible in listings

Deployment notes
----------------

### Production considerations

- **Database**: Use managed PostgreSQL (AWS RDS, GCP Cloud SQL) with connection pooling
- **Redis**: Use managed Redis (AWS ElastiCache, GCP Memorystore) for high availability
- **API Gateway**: Deploy behind AWS API Gateway for IAM auth, rate limiting, and DDoS protection (see `API_GATEWAY_SETUP.md`)
- **Secrets management**: Use AWS Secrets Manager or Parameter Store instead of environment variables
- **Monitoring**: Enable CloudWatch metrics, distributed tracing, and alerting
- **CORS**: Update `allow_origins` in `app/main.py` to restrict to your domain (currently set to `*` for development)
- **Database migrations**: Implement Alembic for safe schema changes

### Container deployment (ECS/EKS/Cloud Run)

```bash
# Build production image
docker build -t itube-api:latest .

# Tag for your registry (ECR example)
docker tag itube-api:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/itube-api:latest

# Push to registry
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/itube-api:latest
```

**Health checks**: The API runs on port 8000. Use `/docs` or create a dedicated `/health` endpoint for load balancer health checks.

Troubleshooting
---------------

### Database connection errors

**Symptom**: `could not connect to server` or `connection refused`

**Solutions**:
- Verify PostgreSQL is running: `docker compose ps` or `pg_isready`
- Check `POSTGRES_DATABASE_URL` in `.env` matches your database configuration
- Ensure database exists: `psql -U postgres -c "CREATE DATABASE itube;"`
- Check firewall rules if using remote database

### AWS Cognito authentication errors

**Symptom**: `UnauthorizedError` or `InvalidParameterException`

**Solutions**:
- Verify `COGNITO_CLIENT_ID` and `COGNITO_CLIENT_SECRET` are correct
- Check Cognito user pool is in the same region as `REGION_NAME`
- Ensure Cognito app client has correct auth flow enabled (USER_PASSWORD_AUTH)
- Verify user is confirmed in Cognito (check email confirmation)

### Redis connection errors

**Symptom**: `ConnectionRefusedError` or cache misses

**Solutions**:
- Verify Redis is running: `docker compose ps` or `redis-cli ping`
- Check `REDIS_HOST` and `REDIS_PORT` in `.env`
- Redis is optional for basic functionality (only affects caching)
- Errors are logged but don't crash the application

### S3 permission errors

**Symptom**: `AccessDenied` or `NoSuchBucket`

**Solutions**:
- Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` have S3 permissions
- Ensure buckets exist: `aws s3 ls | grep itube`
- Check bucket names in `.env` match actual bucket names
- Verify IAM policy allows `s3:PutObject` and `s3:GetObject` on your buckets

### Import errors or missing dependencies

**Symptom**: `ModuleNotFoundError`

**Solutions**:
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# If using virtual environment, ensure it's activated
source .venv/bin/activate
```

### Port already in use

**Symptom**: `Address already in use` when starting the server

**Solutions**:
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
kill -9 $(lsof -ti:8000)

# Or use a different port
uvicorn app.main:app --port 8001
```

API Documentation
-----------------

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
  - Try endpoints directly in the browser
  - See request/response schemas
  - Generate curl commands

- **ReDoc**: http://localhost:8000/redoc
  - Alternative documentation format
  - Better for reading/printing

Testing the API
---------------

### Quick smoke test

```bash
# Health check (via docs page)
curl http://localhost:8000/docs

# Register a user (replace with your values)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }' \
  -c cookies.txt

# Get presigned upload URL (using saved cookies)
curl -X POST http://localhost:8000/api/v1/upload/videos/upload-url \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

Further improvements
--------------------

- **Testing**: Add unit tests (pytest), integration tests, and API tests
- **Database migrations**: Implement Alembic for version-controlled schema changes
- **Rate limiting**: Add request rate limiting per user/IP
- **Video analytics**: Track view counts, likes, comments
- **Search**: Add full-text search for video discovery (Elasticsearch/OpenSearch)
- **Webhooks**: Notify clients when video processing completes
- **Admin panel**: Create admin endpoints for moderation and management
- **GraphQL**: Consider GraphQL API for more flexible client queries

Performance tips
----------------

- **Connection pooling**: SQLAlchemy uses connection pooling by default (5-20 connections)
- **Redis caching**: Video metadata cached for 1 hour, reduces database load
- **Async operations**: Consider making S3/database operations fully async for better concurrency
- **CDN**: Serve processed videos through CloudFront for faster delivery
- **Database indexing**: Ensure indexes on `video_s3_key`, `user_id`, `visibility`, `processing_status`

License
-------

See the top-level [LICENSE](LICENSE) file.

Support
-------

If you're stuck on AWS Cognito setup (we've all been there), check out this [helpful guide](https://lmgt.org/?q=aws+cognito+user+pool+setup+step+by+step).

For S3 presigned URL issues, try searching: [AWS S3 presigned URL troubleshooting](https://lmgt.org/?q=aws+s3+presigned+url+issues).

Still stuck? AWS docs and Stack Overflow are your friends. The FastAPI documentation is also excellent: https://fastapi.tiangolo.com/

---

**Happy coding! 🚀**


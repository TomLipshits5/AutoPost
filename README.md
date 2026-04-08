# AutoPost API

Automatically upload videos to TikTok and other social media platforms. Built with FastAPI, SQLite, and Docker for easy deployment.

## Features

- 🎬 **Multi-platform support** - Currently supports TikTok, easily extensible for Instagram, YouTube, etc.
- 👥 **Multi-user system** - Each user manages their own account and credentials
- 🔐 **Dual authentication** - Both OAuth and manual token entry for TikTok credentials
- ⚙️ **Background processing** - Automatic upload scheduling with retry logic
- 📊 **Job tracking** - Full upload history and status monitoring
- 🐳 **Docker ready** - Complete Docker and Docker Compose setup
- 📚 **OpenAPI docs** - Interactive API documentation at `/docs`
- ⚡ **Async operations** - Built on FastAPI for high performance

## Quick Start

### Prerequisites

- Python 3.11+ (for local development)
- Docker & Docker Compose (for containerized deployment)
- TikTok for Developers account with Content Posting API enabled

### Option 1: Local Development

1. **Clone and setup**
   ```bash
   git clone <repository>
   cd AutoPost
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your TikTok credentials
   ```

3. **Run the API**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

   API available at `http://localhost:8000`

### Option 2: Docker Deployment

1. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your TikTok credentials
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

   API available at `http://localhost:8000`

3. **Stop the service**
   ```bash
   docker-compose -f docker/docker-compose.yml down
   ```

## API Usage

### 1. Register User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password"
  }'
```

Response includes your API key - save it for future requests.

### 2. Add TikTok Credentials

First, get your TikTok access token. Then:

```bash
curl -X POST http://localhost:8000/api/auth/tiktok/token \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "your_tiktok_access_token",
    "open_id": "your_tiktok_open_id"
  }'
```

### 3. Upload Video

```bash
curl -X POST http://localhost:8000/api/videos/upload \
  -H "X-API-Key: your_api_key" \
  -F "title=My Awesome Video" \
  -F "description=Check this out!" \
  -F "tiktok_credential_id=1" \
  -F "file=@video.mp4"
```

Response includes the upload job ID.

### 4. Check Upload Status

```bash
curl http://localhost:8000/api/videos/1 \
  -H "X-API-Key: your_api_key"
```

### 5. List Your Uploads

```bash
curl http://localhost:8000/api/videos \
  -H "X-API-Key: your_api_key"
```

### 6. Get Jobs Summary

```bash
curl http://localhost:8000/api/jobs-summary \
  -H "X-API-Key: your_api_key"
```

## Environment Variables

```env
# Application & Logging
LOG_LEVEL=INFO

# Database (SQLite path)
DATABASE_URL=sqlite:///./data/autopost.db

# Security (Change in production!)
JWT_SECRET_KEY=your-secret-key-change-in-production

# TikTok API Credentials
TIKTOK_CLIENT_KEY=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
TIKTOK_OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/tiktok/callback

# Upload Settings
UPLOAD_DIR=./uploads
UPLOAD_CHECK_INTERVAL=10  # seconds
MAX_RETRIES=5
```

## Project Structure

```
AutoPost/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # SQLAlchemy ORM models
│   ├── database.py          # Database setup
│   ├── schemas.py           # Pydantic validation models
│   ├── security.py          # Authentication & security
│   ├── api/
│   │   ├── auth.py          # User & credential endpoints
│   │   ├── videos.py        # Video upload endpoints
│   │   └── status.py        # Status & health endpoints
│   ├── services/
│   │   ├── tiktok_service.py    # TikTok API integration
│   │   └── upload_manager.py    # Upload orchestration
│   └── tasks/
│       └── scheduler.py     # Background job processing
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
│   ├── TERMS_OF_SERVICE.md
│   └── PRIVACY_POLICY.md
├── requirements.txt
├── .env.example
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - Login and get API key
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/tiktok/token` - Store TikTok access token
- `GET /api/auth/tiktok/credentials` - List TikTok credentials
- `GET /api/auth/tiktok/oauth-url` - Get OAuth redirect URL
- `GET /api/auth/tiktok/callback` - OAuth callback handler

### Videos
- `POST /api/videos/upload` - Upload video for posting
- `GET /api/videos/{job_id}` - Get upload job status
- `GET /api/videos` - List all uploads with optional status filter

### Status
- `GET /api/status` - Health check
- `GET /api/jobs-summary` - Summary of upload jobs

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## How It Works

1. **User registers** with email and password
2. **User adds TikTok credentials** (access token + open ID)
3. **User uploads video** file with title and description
4. **System stores video** locally and creates upload job
5. **Background scheduler** processes jobs every 10 seconds:
   - Initializes upload with TikTok
   - Uploads video file to TikTok's endpoint
   - Checks upload status
   - Publishes video when ready
   - Cleans up local file on success
6. **User can check status** anytime via API

## Upload Status Flow

```
PENDING → PROCESSING → COMPLETED
            ↓
          FAILED (with retry logic)
```

Failed uploads automatically retry up to 5 times with exponential backoff.

## Security Considerations

- **Passwords** are hashed with bcrypt
- **API keys** are generated securely and unique per user
- **TikTok tokens** stored encrypted in database
- **HTTPS recommended** in production
- **API key required** for all video operations
- **User isolation** - users only see their own uploads and credentials

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Style

- Black for formatting
- isort for imports
- Linting with flake8

## Docker Compose Commands

```bash
# Start services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml stop

# Remove containers and volumes
docker-compose -f docker/docker-compose.yml down -v

# Rebuild image
docker-compose -f docker/docker-compose.yml build --no-cache
```

## Future Enhancements

- [ ] Instagram integration
- [ ] YouTube integration
- [ ] Webhook support for TikTok notifications
- [ ] Advanced scheduling (publish at specific times)
- [ ] Bulk upload from directories
- [ ] Video preview/thumbnail generation
- [ ] Analytics dashboard
- [ ] PostgreSQL support for production
- [ ] Celery + Redis for distributed processing

## Troubleshooting

### Videos stuck in PROCESSING
- Check logs: `docker-compose logs -f`
- Verify TikTok token is valid
- Check upload check interval setting

### Upload fails immediately
- Verify video format is MP4 with H.264 codec
- Check file size isn't exceeding limits
- Verify TikTok credentials are correct

### Database locked
- Only one process should access SQLite at a time
- In production, migrate to PostgreSQL

## Legal

- [Terms of Service](./docs/TERMS_OF_SERVICE.md)
- [Privacy Policy](./docs/PRIVACY_POLICY.md)

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or suggestions, please open an issue on the project repository.
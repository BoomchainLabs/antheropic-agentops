# Anthropic Computer Use 

A production-ready implementation of Anthropic’s Computer Use capabilities with AgentOps monitoring, enabling AI agents to interact with computer interfaces through a secure, scalable web platform.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue.svg)](https://www.typescriptlang.org/)

## 🚀 Features

- **Real-time AI Computer Control**: Watch Claude interact with computer interfaces in real-time
- **AgentOps Integration**: Advanced monitoring and analytics for AI agent performance
- **Modern React Frontend**: Responsive, accessible UI built with React 18, TypeScript, and Tailwind CSS
- **Real-time Updates**: WebSocket integration for live AI action streaming
- **Interactive Dashboard**: Monitor sessions, view logs, and manage configurations
- **Secure API Management**: Production-grade API key handling and rate limiting
- **Multi-user Support**: User authentication and session management with role-based access
- **Audit Trail**: Complete logging of all AI actions for compliance and debugging
- **Safety Controls**: Built-in guardrails and content filtering
- **Mobile Responsive**: Optimized for desktop, tablet, and mobile devices

## 📋 Prerequisites

### Backend

- Node.js 18+ or Python 3.9+
- Anthropic API key with Computer Use access
- AgentOps API key for monitoring and analytics
- PostgreSQL or MongoDB for production data storage
- Redis (optional, for caching and session storage)

### Frontend

- Node.js 18+
- npm or yarn package manager
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+)

### Development Tools

- Docker (optional, for containerized deployment)
- Git for version control

## 🛠️ Quick Start

### Local Development

1. **Clone the repository**
   
   ```bash
   git clone https://github.com/BoomchainLabs/antheropic-agentops.git
   cd antheropic-agentops
   ```
1. **Install backend dependencies**
   
   ```bash
   # For Node.js backend
   cd backend
   npm install
   
   # For Python backend
   cd backend
   pip install -r requirements.txt
   ```
1. **Install frontend dependencies**
   
   ```bash
   cd frontend
   npm install
   ```
1. **Configure environment**
   
   ```bash
   # Backend configuration
   cd backend
   cp .env.example .env
   
   # Frontend configuration
   cd ../frontend
   cp .env.example .env.local
   ```
1. **Set required environment variables**
   
   **Backend (.env)**:
   
   ```bash
   ANTHROPIC_API_KEY="your_anthropic_api_key_here"
   AGENTOPS_API_KEY="your_agentops_api_key_here"
   DATABASE_URL="your_database_connection_string"
   JWT_SECRET="your_jwt_secret"
   CORS_ORIGIN="http://localhost:3000"
   ```
   
   **Frontend (.env.local)**:
   
   ```bash
   REACT_APP_API_URL="http://localhost:8000/api"
   REACT_APP_WS_URL="ws://localhost:8000"
   REACT_APP_ENVIRONMENT="development"
   ```
1. **Start the development servers**
   
   ```bash
   # Terminal 1: Start backend
   cd backend
   npm run dev
   # Backend runs on http://localhost:8000
   
   # Terminal 2: Start frontend
   cd frontend
   npm start
   # Frontend runs on http://localhost:3000
   ```
1. **Access the application**
- Frontend Application: http://localhost:3000
- Backend API: http://localhost:8000/api
- API Documentation: http://localhost:8000/api/docs

## 🐳 Docker Deployment

### Development with Docker Compose

```bash
# Build and run full stack with Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

### Production Deployment

```bash
# Build and run production stack
docker-compose -f docker-compose.prod.yml up -d

# Or build manually
docker build -t anthropic-computer-use-backend ./backend
docker build -t anthropic-computer-use-frontend ./frontend
```

**docker-compose.prod.yml example:**

```yaml
version: '3.8'
services:
  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
      - "443:443"
    environment:
      - REACT_APP_API_URL=https://api.yourdomain.com
    depends_on:
      - backend
    
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=production
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AGENTOPS_API_KEY=${AGENTOPS_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - database
      
  database:
    image: postgres:15
    environment:
      - POSTGRES_DB=anthropic_computer_use
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🔧 Configuration

### Environment Variables

#### Backend Configuration

|Variable               |Description                         |Required|Default|
|-----------------------|------------------------------------|--------|-------|
|`ANTHROPIC_API_KEY`    |Your Anthropic API key              |Yes     |-      |
|`AGENTOPS_API_KEY`     |Your AgentOps API key for monitoring|Yes     |-      |
|`DATABASE_URL`         |Database connection string          |Yes     |-      |
|`JWT_SECRET`           |Secret for JWT token signing        |Yes     |-      |
|`REDIS_URL`            |Redis connection for caching        |No      |-      |
|`MAX_REQUESTS_PER_HOUR`|Rate limiting per user              |No      |100    |
|`ENABLE_AUDIT_LOGGING` |Enable detailed audit logs          |No      |true   |
|`CORS_ORIGIN`          |Allowed frontend origins            |No      |*      |
|`PORT`                 |Backend server port                 |No      |8000   |
|`AGENTOPS_ENABLED`     |Enable AgentOps monitoring          |No      |true   |

#### Frontend Configuration

|Variable                |Description                   |Required|Default   |
|------------------------|------------------------------|--------|----------|
|`REACT_APP_API_URL`     |Backend API base URL          |Yes     |-         |
|`REACT_APP_WS_URL`      |WebSocket server URL          |Yes     |-         |
|`REACT_APP_ENVIRONMENT` |Environment (dev/staging/prod)|No      |production|
|`REACT_APP_SENTRY_DSN`  |Sentry DSN for error tracking |No      |-         |
|`REACT_APP_ANALYTICS_ID`|Google Analytics ID           |No      |-         |
|`GENERATE_SOURCEMAP`    |Generate source maps          |No      |false     |

### AgentOps Configuration

AgentOps provides comprehensive monitoring and analytics for your AI agents. Configure it in your backend:

```javascript
// backend/config/agentops.js
const agentops = require('agentops-node');

agentops.init({
  apiKey: process.env.AGENTOPS_API_KEY,
  environment: process.env.NODE_ENV || 'development',
  tags: ['anthropic', 'computer-use'],
  instrumentLLMs: true,
  autoStartSession: true
});

module.exports = agentops;
```

**AgentOps Features Enabled:**

- **Session Tracking**: Automatic session management for computer use tasks
- **LLM Monitoring**: Track Anthropic API calls, tokens, and costs
- **Performance Metrics**: Response times, success rates, and error tracking
- **Custom Events**: Log specific computer use actions and outcomes
- **Cost Analytics**: Monitor API usage and associated costs
- **Error Tracking**: Detailed error logs with context and stack traces

**Environment Variables for AgentOps:**

```bash
AGENTOPS_API_KEY="your_agentops_api_key"
AGENTOPS_ENABLED=true
AGENTOPS_ENVIRONMENT="production"
AGENTOPS_AUTO_START_SESSION=true
AGENTOPS_INSTRUMENT_LLMS=true
```

### Security Configuration

```json
{
  "security": {
    "rateLimit": {
      "windowMs": 3600000,
      "maxRequests": 100
    },
    "cors": {
      "allowedOrigins": ["https://yourdomain.com"],
      "credentials": true
    },
    "contentSecurityPolicy": {
      "enabled": true,
      "directives": {
        "defaultSrc": ["'self'"],
        "scriptSrc": ["'self'", "'unsafe-inline'"]
      }
    }
  }
}
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                          │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   React App     │   Redux Store   │   WebSocket     │   Router  │
│   (TypeScript)  │   (State Mgmt)  │   (Real-time)   │ (React)   │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
         │                       │                       │
         │ HTTPS/API Calls       │ WebSocket             │
         │                       │                       │
┌─────────────────────────────────────────────────────────────────┐
│                        Backend Layer                           │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   API Gateway   │   Auth Service  │  WebSocket Srv  │  AI Svc   │
│   (Express)     │   (JWT/OAuth)   │   (Socket.io)   │ (Anthropic│
└─────────────────┴─────────────────┴─────────────────┴───────────┘
         │                       │                       │
         │              ┌─────────────────┐             │
         │              │   Middleware    │             │
         │              │ Rate Limit/CORS │             │
         │              └─────────────────┘             │
         │                       │                       │
┌─────────────────┬─────────────────┬─────────────────┬───────────┐
│    Database     │   File Storage  │      Cache      │ Monitoring│
│  (PostgreSQL)   │   (S3/Local)    │    (Redis)      │ (AgentOps)│
└─────────────────┴─────────────────┴─────────────────┴───────────┘
```

### Frontend Architecture

```
src/
├── components/           # Reusable UI components
│   ├── ui/              # Basic UI elements (Button, Input, etc.)
│   ├── forms/           # Form components
│   ├── layout/          # Layout components (Header, Sidebar)
│   └── computer-use/    # Computer use specific components
├── pages/               # Route pages
│   ├── Dashboard/       # Main dashboard
│   ├── Sessions/        # Session management
│   ├── Settings/        # User settings
│   └── Auth/            # Authentication pages
├── hooks/               # Custom React hooks
├── store/               # Redux store and slices
├── services/            # API calls and WebSocket handling
├── utils/               # Utility functions
├── types/               # TypeScript type definitions
└── styles/              # Global styles and Tailwind config
```

## 📚 API Documentation

### Authentication

```bash
# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password"
}

# Response
{
  "token": "jwt_token",
  "user": { "id": 1, "email": "user@example.com" }
}
```

### Computer Use Endpoints

```bash
# Start a new computer use session
POST /api/computer-use/session
Authorization: Bearer <token>
{
  "instructions": "Take a screenshot and describe what you see"
}

# Get session status
GET /api/computer-use/session/{sessionId}
Authorization: Bearer <token>

# Stream real-time updates
GET /api/computer-use/stream/{sessionId}
Authorization: Bearer <token>
```

## 🔒 Security Features

- **API Key Encryption**: All API keys encrypted at rest
- **Rate Limiting**: Per-user and global rate limits
- **Input Sanitization**: All user inputs validated and sanitized
- **Audit Logging**: Complete audit trail of all AI actions
- **Content Filtering**: Built-in safety filters for inappropriate content
- **Session Management**: Secure JWT-based authentication
- **CORS Protection**: Configurable cross-origin request handling

## 📊 Monitoring & Observability

### AgentOps Dashboard

AgentOps provides a comprehensive dashboard for monitoring your AI agents:

- **Real-time Metrics**: Live session tracking and performance monitoring
- **Cost Analysis**: Track API usage and costs across all Anthropic calls
- **Session Replay**: Review complete agent sessions with detailed logs
- **Performance Analytics**: Response times, success rates, and error patterns
- **Custom Events**: Track specific computer use actions and outcomes

Access your AgentOps dashboard at: <https://app.agentops.ai>

### Health Checks

```bash
# Application health
GET /health

# Database connectivity
GET /health/database

# Anthropic API status
GET /health/anthropic

# AgentOps connection status
GET /health/agentops
```

### Application Metrics

- Request/response times
- API usage statistics (Anthropic + AgentOps)
- Error rates and types
- User session analytics
- Computer use action frequency
- Cost per session tracking

### Logging with AgentOps Integration

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "action": "computer_use_screenshot",
  "userId": "user_123",
  "sessionId": "session_456",
  "agentopsSessionId": "ao_session_789",
  "duration": 1250,
  "success": true,
  "cost": 0.003,
  "tokens": {
    "input": 150,
    "output": 75
  }
}
```

## 🧪 Testing

```bash
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Run end-to-end tests
npm run test:e2e

# Generate coverage report
npm run test:coverage
```

## 🚀 Deployment

### Production Checklist

- [ ] Environment variables configured (Anthropic + AgentOps)
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Rate limiting configured
- [ ] AgentOps monitoring setup and validated
- [ ] Backup strategy implemented
- [ ] Error tracking configured (Sentry, Rollbar)
- [ ] Load balancer configured
- [ ] CDN setup for static assets
- [ ] AgentOps dashboard access configured
- [ ] Cost monitoring alerts setup

### Deployment Options

#### AWS ECS/Fargate

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    image: anthropic-computer-use:latest
    environment:
      - NODE_ENV=production
    ports:
      - "80:3000"
```

#### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anthropic-computer-use
spec:
  replicas: 3
  selector:
    matchLabels:
      app: anthropic-computer-use
  template:
    metadata:
      labels:
        app: anthropic-computer-use
    spec:
      containers:
      - name: app
        image: anthropic-computer-use:latest
        ports:
        - containerPort: 3000
```

## 🔧 Troubleshooting

### Common Issues

**AgentOps API Key Issues**

```bash
# Verify AgentOps connection
curl -X POST "https://api.agentops.ai/v1/sessions" \
  -H "X-AgentOps-API-Key: YOUR_AGENTOPS_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tags": ["test"]}'
```

**API Key Issues**

```bash
# Verify Anthropic API key
curl -H "x-api-key: YOUR_ANTHROPIC_KEY" https://api.anthropic.com/v1/messages
```

**Database Connection**

```bash
# Test database connection
npm run db:test
```

**Rate Limiting**

- Check rate limit headers in API responses
- Monitor rate limit metrics in dashboard
- Adjust limits in configuration

## 🤝 Contributing

1. Fork the repository
1. Create a feature branch (`git checkout -b feature/amazing-feature`)
1. Commit your changes (`git commit -m 'Add amazing feature'`)
1. Push to the branch (`git push origin feature/amazing-feature`)
1. Open a Pull Request

### Development Guidelines

- Follow ESLint/Prettier configuration
- Write unit tests for new features
- Update documentation for API changes
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the <LICENSE> file for details.

## 📞 Support

- **Documentation**: [Wiki](https://github.com/BoomchainLabs/antheropic-agentops/wiki)
- **Issues**: [GitHub Issues](https://github.com/BoomchainLabs/antheropic-agentops/issues)
- **Discussions**: [GitHub Discussions](https://github.com/BoomchainLabs/antheropic-agentops/discussions)
- **Email**: support@boomchainlab.com,cashapppaymentpay01@gmail.com

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) for the Claude API and Computer Use capabilities
- [AgentOps](https://agentops.ai) for comprehensive AI agent monitoring and analytics
- [Replit](https://replit.com) for the original demo inspiration
- Contributors and community members

-----

**⚠️ Important Security Note**: This application enables AI to control computer interfaces. Always review and understand the security implications before deploying to production. Ensure proper access controls, monitoring, and safety measures are in place.

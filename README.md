# MiniMart AI Inventory Management System

An intelligent, multi-agent inventory management system that automates ordering, demand forecasting, supplier negotiations, and logistics coordination for mini mart operations.

## 🚀 Features

### Core Functionality
- **Customer Ordering System**: Seamless order placement with fake payment processing
- **Real-time Inventory Management**: Live inventory updates and stock level monitoring
- **AI-Powered Demand Forecasting**: 5-year historical analysis with seasonal patterns
- **Automated Supplier Negotiations**: Email-based RFQ and price negotiations
- **Intelligent Logistics Coordination**: Supplier performance tracking and delivery management

### AI Agents
- **Order Placement Agent**: EOQ calculations, reorder point optimization
- **Demand Forecast Agent**: Statistical forecasting with OpenAI market insights
- **Supplier Agent**: Automated RFQ, price negotiations, supplier selection
- **Logistics Agent**: Performance tracking, delivery coordination, issue resolution
- **Supervisor Agent**: Multi-agent orchestration using LangGraph

### Advanced Features
- **RAG System**: Vector-based knowledge retrieval for internal data
- **Multi-Agent Coordination**: A2A protocols and workflow orchestration
- **Real-time Analytics**: Sales trends, inventory performance, supplier metrics
- **Comprehensive Testing**: Unit, integration, and evaluation frameworks

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AI Agents     │
                       │   (LangGraph)   │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   RAG System    │
                       │   (ChromaDB)    │
                       └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **PostgreSQL**: Primary database
- **LangChain + LangGraph**: Multi-agent framework
- **OpenAI API**: Demand forecasting and market analysis
- **ChromaDB**: Vector database for RAG
- **Statsmodels**: Statistical analysis and forecasting

### Frontend
- **React.js**: Modern UI framework
- **Tailwind CSS**: Utility-first CSS framework
- **Recharts**: Data visualization
- **Axios**: HTTP client

### Infrastructure
- **Docker**: Containerization
- **Nginx**: Reverse proxy
- **Prometheus + Grafana**: Monitoring
- **Redis**: Caching and session management

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose
- OpenAI API Key

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/minimart.git
cd minimart
```

### 2. Environment Setup
```bash
# Copy environment template
cp env.example .env

# Edit environment variables
nano .env
```

Required environment variables:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/minimart_db
OPENAI_API_KEY=your_openai_api_key_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SECRET_KEY=your_secret_key_here
```

### 3. Database Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database with sample data
python app/database/init_db.py
```

### 4. Start the Application

#### Development Mode
```bash
# Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in another terminal)
cd frontend
npm install
npm start
```

#### Production Mode with Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 5. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3001 (admin/admin)

## 📊 Sample Data

The system comes pre-loaded with:
- **20 Products**: Beverages, snacks, household items, personal care, food items
- **4 Suppliers**: Each product has 4 suppliers with different pricing
- **10 Years of Sales Data**: Historical transactions for demand forecasting
- **Sample Customers**: Test customer data for order processing

## 🤖 AI Agents Usage

### Demand Forecasting
```python
# Trigger demand forecast
POST /api/v1/agents/demand-forecast
{
    "product_ids": [1, 2, 3],
    "forecast_period_days": 30
}
```

### Inventory Management Workflow
```python
# Execute complete inventory management workflow
POST /api/v1/agents/workflow/inventory-management
{
    "product_ids": [1, 2, 3, 4, 5]
}
```

### Emergency Reorder
```python
# Trigger emergency reorder
POST /api/v1/agents/workflow/emergency-reorder
{
    "product_id": 1,
    "quantity": 50
}
```

## 🧪 Testing

### Run All Tests
```bash
# Backend tests
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test
```

### Agent Evaluation
```bash
# Run comprehensive agent evaluation
python -m app.evaluation.evaluator
```

### Performance Testing
```bash
# Load testing with Locust
locust -f tests/load_test.py --host=http://localhost:8000
```

## 📈 Monitoring

### Metrics Available
- **System Performance**: Response times, throughput, error rates
- **Agent Performance**: Execution times, success rates, decision quality
- **Business Metrics**: Stockout rates, cost savings, service levels
- **Database Performance**: Query times, connection pools, transaction rates

### Grafana Dashboards
- System Overview
- Agent Performance
- Business Metrics
- Database Health

## 🔧 Configuration

### Agent Configuration
```python
# app/core/config.py
class Settings:
    # Agent execution intervals
    reorder_check_interval_hours = 6
    forecast_horizon_days = 90
    performance_tracking_period_days = 90
```

### Database Configuration
```python
# Database connection settings
DATABASE_URL = "postgresql://user:pass@localhost:5432/minimart_db"
```

## 🚀 Deployment

### Production Deployment
```bash
# Build and deploy with Docker
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale backend=3
```

### Environment Variables for Production
```env
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your_secure_secret_key
DATABASE_URL=postgresql://prod_user:secure_pass@db:5432/minimart_prod
```

## 📚 API Documentation

### Core Endpoints
- `GET /api/v1/products/` - List all products
- `POST /api/v1/orders/` - Create new order
- `GET /api/v1/inventory/` - Get inventory levels
- `POST /api/v1/inventory/reorder-check` - Trigger reorder check

### Agent Endpoints
- `POST /api/v1/agents/demand-forecast` - Execute demand forecasting
- `POST /api/v1/agents/workflow/inventory-management` - Full workflow
- `GET /api/v1/agents/rag/product-insights/{id}` - Get product insights

### Interactive API Documentation
Visit http://localhost:8000/docs for interactive Swagger documentation.

## 🔒 Security

### Implemented Security Measures
- Input validation and sanitization
- SQL injection prevention
- CORS configuration
- Rate limiting
- Secure headers
- Environment variable protection

### Security Best Practices
- Use HTTPS in production
- Implement authentication/authorization
- Regular security updates
- Monitor for vulnerabilities
- Secure database connections

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run linting
black app/
flake8 app/
mypy app/
```

### Code Style
- Follow PEP 8 for Python code
- Use type hints
- Write comprehensive tests
- Document all functions and classes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Troubleshooting

#### Common Issues
1. **Database Connection Errors**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Verify connection
   psql -h localhost -U minimart_user -d minimart_db
   ```

2. **OpenAI API Errors**
   ```bash
   # Verify API key
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   ```

3. **Agent Execution Errors**
   ```bash
   # Check agent logs
   tail -f logs/agent.log
   ```

### Getting Help
- Check the [Issues](https://github.com/your-username/minimart/issues) page
- Review the [Documentation](docs/)
- Contact: support@minimart-ai.com

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ Core inventory management
- ✅ AI agent implementation
- ✅ Basic UI and API

### Phase 2 (Q1 2025)
- 🔄 Mobile application
- 🔄 Advanced analytics
- 🔄 Multi-location support

### Phase 3 (Q2 2025)
- 📋 Machine learning models
- 📋 Integration APIs
- 📋 Advanced reporting

## 🙏 Acknowledgments

- OpenAI for GPT API
- LangChain team for the agent framework
- FastAPI for the excellent web framework
- React team for the frontend framework

---

**Built with ❤️ for small business owners**

For more information, visit our [documentation](docs/) or [contact us](mailto:info@minimart-ai.com).
# Multi-Agent Travel Planning System

A sophisticated travel planning system built with LangGraph for agent orchestration and MCP (Model Context Protocol) for Google Services integration.

## 🏗️ Architecture

This system implements a multi-agent architecture with four core pillars:

1. **Reflection**: Trip Critic Agent provides continuous feedback and optimization
2. **Tool Use**: MCP connectors interface with Google APIs (Places, Weather, Geocoding)
3. **Planning**: Planner Agent coordinates the entire workflow strategically
4. **Multi-Agent Collaboration**: LangGraph orchestrates agent interactions

## 🤖 Agents

- **Planner Agent**: Main coordinator that manages the overall workflow
- **Destination Finder**: Researches and validates destination information
- **Local Expert**: Provides local insights and recommendations
- **Itinerary Expert**: Creates detailed day-by-day itineraries
- **Trip Critic**: Reviews and optimizes the travel plan through feedback loops

## 🔧 Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd travel-planning-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Google API keys
   ```

4. **Run the system**
   ```bash
   python src/main.py
   ```

## 📋 Input Format

```json
{
    "destination": "Paris, France",
    "start_date": "2024-08-15",
    "end_date": "2024-08-20",
    "budget": 2000.0,
    "interests": ["museums", "restaurants", "architecture"]
}
```

## 🎯 Output

The system generates a comprehensive travel itinerary including:
- Weather forecast for travel dates
- Hotel recommendations with ratings and pricing
- Tourist attractions based on interests
- Restaurant recommendations
- Day-by-day detailed itinerary
- Cost estimates and budget optimization

## 🚀 Features

- **Real-time Google API integration** via MCP
- **Intelligent agent collaboration** via LangGraph
- **Continuous optimization** through feedback loops
- **Budget-aware recommendations**
- **Weather-informed planning**
- **Interest-based personalization**

## 📱 Google APIs Used

- **Google Places API**: Hotel and restaurant recommendations
- **Google Weather API**: Weather forecasts and conditions
- **Google Geocoding API**: Location validation and coordinates

## 🧪 Testing

```bash
pytest tests/
```

## 📚 Documentation

- [Architecture Guide](docs/architecture.md)
- [API Reference](docs/api_reference.md)
- [Deployment Guide](docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

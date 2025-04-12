# Py-Quantix: Hexagonal Architecture Quantitative Trading System

![CI Status](https://github.com/RanchoCooper/py-quantix/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/RanchoCooper/py-quantix/branch/main/graph/badge.svg)](https://codecov.io/gh/RanchoCooper/py-quantix)

## Overview
Py-Quantix is a robust quantitative trading system built using Hexagonal Architecture (also known as Ports and Adapters pattern). This architecture enables clean separation of business logic from technical implementations, making the system highly maintainable, testable, and adaptable to changing requirements.

## Architecture
The system follows a hexagonal architecture with the following layers:

- **Domain Layer**: Contains core business entities, value objects, and domain services
- **Application Layer**: Implements use cases and orchestrates domain objects
- **Adapter Layer**: Connects the application to external systems through ports
- **Infrastructure Layer**: Provides technical implementations for the adapters

## Project Structure
```
py-quantix/
├── domain/          # Domain entities and business logic
├── application/     # Use cases and application services
├── adapter/         # Technical implementations of ports
│   ├── cache/       # Cache implementations (Redis)
│   ├── di/          # Dependency injection container
│   ├── event/       # Event bus implementations
│   ├── exchange/    # Exchange API implementations (Binance)
│   ├── http/        # HTTP/REST API (Flask)
│   └── repository/  # Data persistence (SQLAlchemy)
├── config/          # Configuration files
└── tests/           # Unit and integration tests
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- MySQL or PostgreSQL
- Redis

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/RanchoCooper/py-quantix.git
   cd py-quantix
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure the application:
   ```
   cp config/config.yaml.example config/config.yaml
   # Edit config.yaml with your database, Redis, and Binance API settings
   ```

### Running the Application
Set the PYTHONPATH to include the project root directory:

```
export PYTHONPATH=$PYTHONPATH:/path/to/py-quantix
# On Windows: set PYTHONPATH=%PYTHONPATH%;C:\path\to\py-quantix
```

Start the application:
```
python main.py
```

## Configuration
The application is configured through `config/config.yaml`. Key configuration sections include:

- **flask**: HTTP server configuration
- **db**: Database settings for MySQL and PostgreSQL
- **redis**: Cache configuration
- **exchange**: Exchange API settings (Binance)
- **logging**: Logging levels and formats

## Exchange API Support
The system supports cryptocurrency exchange integrations through a standardized port interface. Currently supported exchanges:

### Binance
To use the Binance exchange API:

1. Configure your API credentials in `config/config.yaml`:
   ```yaml
   exchange:
     binance:
       api_key: "your_api_key"
       api_secret: "your_api_secret"
       testnet: true  # Use testnet for testing
   ```

2. Run the Binance example script:
   ```
   python entry/binance_example.py
   ```

This script demonstrates fetching market data, getting account information, and more from the Binance API.

## Database Support
The system supports both MySQL and PostgreSQL. The default database can be configured in the `config.yaml` file.

## Testing
Run tests with:
```
pytest
```

## License
[MIT License](LICENSE)

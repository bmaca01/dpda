# DPDA Simulator

A Deterministic Pushdown Automaton (DPDA) simulator

Originally developed for CS341

## Features

- **Complete DPDA Simulation**: Full implementation of deterministic pushdown automata
- **Modular Architecture**: Clean separation of concerns with 7+ modules
- **REST API**: FastAPI-based web service for DPDA operations
- **Comprehensive Testing**: 157+ tests with TDD methodology
- **Multiple Output Formats**: JSON serialization, DOT graphs, D3.js, Cytoscape
- **Session Management**: Build and manage multiple DPDAs

## Requirements

- Python >= 3.9.2
- pip for dependency management

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/dpda-simulator.git
cd dpda-simulator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Run the interactive CLI simulator:
```bash
python3 main.py
```

Or use the original implementation:
```bash
python3 src/main.py
```

### REST API

Start the API server:
```bash
uvicorn api.endpoints:app --reload
```

API documentation available at: `http://localhost:8000/docs`

#### Example API Usage

```python
import requests

# Create a DPDA
response = requests.post("http://localhost:8000/api/dpda/create",
    json={"name": "0n1n", "description": "Accepts 0^n1^n"})
dpda_id = response.json()["id"]

# Set states
requests.post(f"http://localhost:8000/api/dpda/{dpda_id}/states",
    json={"states": ["q0", "q1", "q2"], "initial_state": "q0", "accept_states": ["q2"]})

# Set alphabets
requests.post(f"http://localhost:8000/api/dpda/{dpda_id}/alphabets",
    json={"input_alphabet": ["0", "1"], "stack_alphabet": ["$", "X"], "initial_stack_symbol": "$"})

# Add transitions
requests.post(f"http://localhost:8000/api/dpda/{dpda_id}/transition",
    json={"from_state": "q0", "input_symbol": "0", "stack_top": "$",
          "to_state": "q0", "stack_push": ["X", "$"]})

# Test a string
result = requests.post(f"http://localhost:8000/api/dpda/{dpda_id}/compute",
    json={"input_string": "0011", "show_trace": True})
print("Accepted:", result.json()["accepted"])
```

## Architecture

### Module Structure
- **`core/`**: DPDA computation engine and session management
  - `dpda_engine.py`: Stateless computation engine
  - `session.py`: Stateful DPDA builder and manager
- **`models/`**: Data models for DPDA components
  - `dpda_definition.py`: Formal DPDA structure
  - `transition.py`: State transitions
  - `configuration.py`: Instantaneous descriptions
  - `computation_result.py`: Computation outcomes
- **`validation/`**: DPDA determinism validation
  - `dpda_validator.py`: Enforces 4 determinism properties
- **`cli_io/`**: Command-line interface
  - `cli_interface.py`: Interactive DPDA construction
  - `formatter.py`: Output formatting
- **`serialization/`**: Save/load functionality
  - `dpda_serializer.py`: JSON serialization
- **`visualization/`**: Graph generation
  - `graph_builder.py`: DOT, D3.js, Cytoscape formats
- **`api/`**: REST API
  - `endpoints.py`: FastAPI routes
  - `models.py`: Pydantic request/response models

## Testing

Run the complete test suite:
```bash
pytest tests/ -v
```

Run specific test modules:
```bash
pytest tests/test_core/ -v        # Core engine tests
pytest tests/test_api/ -v         # API tests
pytest tests/test_integration.py  # Integration tests
```

### API Endpoints
- `POST /api/dpda/create` - Create new DPDA
- `GET /api/dpda/{id}` - Get DPDA info
- `POST /api/dpda/{id}/states` - Set states
- `POST /api/dpda/{id}/alphabets` - Set alphabets
- `POST /api/dpda/{id}/transition` - Add transition
- `DELETE /api/dpda/{id}/transition/{index}` - Remove transition
- `POST /api/dpda/{id}/compute` - Test string acceptance
- `POST /api/dpda/{id}/validate` - Validate determinism
- `GET /api/dpda/{id}/export` - Export as JSON
- `GET /api/dpda/{id}/visualize` - Generate visualization

## License

Todo

## Acknowledgments

- **Course**: NJIT CS341-005, Fall 2023
- **Instructor**: Prof. Ravi Varadarajan

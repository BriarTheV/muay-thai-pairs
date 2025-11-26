# Muay Thai Matchmaker 🥊

A comprehensive Streamlit-based web application for automating Muay Thai tournament fight pairing with **VRVS (Russian) and IFMA (International) compliance**. Intelligently matches fighters using advanced algorithms while ensuring fair competition and safety.

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Algorithm Documentation](#-algorithm-documentation)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Features

### Core Functionality
- ✅ **Excel Data Ingestion** - Upload athlete rosters with automatic validation and cleaning
- ✅ **Intelligent Pairing Engine** - Advanced algorithms for optimal fight matching
- ✅ **Manual Adjustments** - Interactive interface for pairing modifications
- ✅ **Professional Export** - PDF bout sheets and Excel summaries for tournament officials

### Algorithm Features
- ✅ **VRVS Compliance** - Official Russian weight categories by age and gender
- ✅ **IFMA Compatibility** - International Muay Thai Federation standards
- ✅ **Look-ahead Optimization** - Prevents orphaning with advanced heuristics
- ✅ **2kg Difference Rule** - VRVS rule for undefined weight categories
- ✅ **Multi-level Conflict Detection** - Club and trainer conflict prevention

### Safety & Fairness
- ✅ **Gender Separation** - Strict same-gender pairing enforcement
- ✅ **Weight Category Compliance** - Accurate VRVS/IFMA weight class assignment
- ✅ **Age-appropriate Matching** - Demographic-aware pairing rules
- ✅ **Experience Balancing** - Fair competition through skill level matching

### User Experience
- ✅ **Real-time Validation** - Immediate feedback on pairing conflicts
- ✅ **Interactive Editing** - Drag-and-drop style manual adjustments
- ✅ **Performance Monitoring** - Benchmarking and quality metrics
- ✅ **Multi-language Support** - Russian and English interfaces

## 🏃 Quick Start

```bash
# Clone the repository
git clone https://github.com/BriarTheV/muay-thai-pairs.git
cd muay-thai-pairs

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

Upload an Excel file with fighter data and start pairing!

## 📦 Installation

### Prerequisites
- Python 3.11+
- pip package manager

### Local Development
```bash
# Clone repository
git clone https://github.com/BriarTheV/muay-thai-pairs.git
cd muay-thai-pairs

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Run application
streamlit run app.py
```

### Docker Deployment
```bash
# Build container
docker build -t muay-thai-matchmaker .

# Run container
docker run -p 8501:8501 muay-thai-matchmaker
```

### Production Deployment
The application supports deployment on:
- **Streamlit Cloud** - Direct deployment from GitHub
- **Heroku** - Using the included Procfile
- **Docker** - Containerized deployment
- **VPS/Cloud** - Manual server deployment

## 💡 Usage

### Data Format
Upload an Excel file (`.xlsx` or `.ods`) with the following columns:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `Name` | Text | ✅ | Fighter's full name |
| `Gender` | Text | ✅ | 'М' (male) or 'Ж' (female) |
| `Age` | Number | ✅ | Age in years |
| `Weight` | Text | ✅ | Weight specification (e.g., 'до 54', '70-75') |
| `Club` | Text | ✅ | Gym/club name |
| `Trainer` | Text | ✅ | Coach/trainer name |
| `Record` | Number | ✅ | Number of wins |
| `Class` | Text | ❌ | Experience class ('А', 'Б', 'С', 'Д') |

### Weight Specifications
- **VRVS Categories**: `до 54` (up to 54kg → 54kg category)
- **Ranges**: `70-75` (70-75kg range)
- **Single Values**: `72` (exactly 72kg)
- **Open Weights**: `75+` (75kg and above)

### Pairing Process

1. **Upload Data** → Import fighter roster from Excel
2. **Configure Settings** → Set conflict levels and algorithm preferences
3. **Generate Pairs** → Run automatic pairing algorithm
4. **Manual Adjustments** → Review and modify pairs as needed
5. **Export Results** → Download PDF bout sheets and Excel summaries

### Algorithm Selection

| Algorithm | Speed | Quality | Use Case |
|-----------|-------|---------|----------|
| **Greedy** | ⚡ Fast | 90-95% | Quick tournaments |
| **Look-ahead** | 🐌 Slower | 95-99% | Important competitions |

## 🧠 Algorithm Documentation

### Core Pairing Logic

The system uses a hybrid pairing approach combining **greedy optimization** with **look-ahead heuristics** for optimal results.

#### 1. Data Processing Pipeline

```
Excel Upload → Data Validation → Fighter Objects → Pairing Algorithm → Manual Review → Export
```

#### 2. Weight Category System

**VRVS (Russian) Categories** - Official tournament compliance:

| Age Group | Categories | Example |
|-----------|------------|---------|
| **Adults 17-40** | 45kg, 48kg, 51kg, 54kg, 57kg, 60kg, 63.5kg, 67kg, 71kg, 75kg, 75+kg | `"до 54"` → 54kg category |
| **Juniors 16-23** | Same as adults | `"до 57"` → 57kg category |
| **Youth 14-15** | 32kg through 81+kg (26 categories) | `"до 32"` → 32kg category |
| **Youth 12-13** | 30kg through 71+kg (24 categories) | `"до 30"` → 30kg category |

**IFMA (International) Categories** - Fallback for compatibility:
- Light Fly (0-51.5kg), Fly (51.5-54kg), Bantam (54-57kg), etc.

#### 3. Pairing Constraints

**Hard Constraints** (must be satisfied):
- ✅ **Gender Match**: Same gender only
- ✅ **Age Division**: Same age group (12-13, 14-15, 16-17, 18-23, 17-40)
- ✅ **Club Conflicts**: Configurable levels (1-4) for same-club prevention

**Soft Constraints** (optimization goals):
- 🎯 **Weight Category**: Same VRVS category for adults
- 🎯 **Experience Balance**: Similar win records
- 🎯 **2kg Difference Rule**: For categories below defined limits

#### 4. Look-ahead Heuristic

**Problem**: Greedy algorithms can create "orphaned" fighters - competitors who cannot pair with any remaining opponents.

**Solution**: Look-ahead checks pairing consequences before committing:

```python
def would_orphan_fighter(fighter1, fighter2, remaining_fighters):
    """Check if pairing f1-f2 would leave fighters unmatched."""
    # Simulate pairing f1-f2
    # Check if any remaining fighter has no valid opponents
    # Return orphaned fighter or None if safe
```

**Benefits**:
- 📈 **+5-10% better pairing quality**
- 🛡️ **Prevents tournament delays**
- ⚖️ **More fair competition**

#### 5. 2kg Difference Rule (VRVS)

For fighters in weight ranges below defined VRVS categories:

```python
# If both fighters are below the lowest defined category
if min_weight < lowest_category_min:
    # Allow pairing if weight difference ≤ 2kg
    return abs(fighter1.weight - fighter2.weight) <= 2.0
```

**Example**: Fighters weighing 28kg and 29kg can pair (1kg difference ≤ 2kg limit).

### Validation Logic

#### Adult Categories (17+)
```python
# Strict category matching
if fighter1.category == fighter2.category:
    return ValidationResult(True, f"✅ VRVS match in {category} category")
else:
    return ValidationResult(False, f"❌ Different categories: {cat1} vs {cat2}")
```

#### Youth Categories (12-16)
```python
# Floating differences based on age
max_diff = get_max_diff_12_15(avg_weight)  # 2-4kg depending on weight
if weight_diff <= max_diff:
    return ValidationResult(True, f"✅ Youth match: diff {weight_diff}kg ≤ {max_diff}kg")
```

#### 2kg Rule Application
```python
# Automatic for undefined categories
if can_match_by_weight_difference(fighter1, fighter2):
    if weight_diff <= 2.0:
        return ValidationResult(True, f"✅ 2kg rule: diff {weight_diff}kg ≤ 2kg")
```

## 🔧 API Reference

### Core Functions

#### `pair_fighters(df, club_conflict_level=3, sort_strategy="quantity", allow_subgroup_pairings=True, use_lookahead=False)`

Main pairing function.

**Parameters:**
- `df`: Pandas DataFrame with fighter data
- `club_conflict_level`: Club conflict strictness (1-4)
- `sort_strategy`: "quantity" (max pairs) or "quality" (experienced first)
- `allow_subgroup_pairings`: Allow same-club different subgroups
- `use_lookahead`: Enable look-ahead heuristic

**Returns:** `(matches_df, unmatched_df)`

#### `create_fighters(df)`

Convert DataFrame to Fighter objects with VRVS category assignment.

#### `is_valid_pair(fighter1, fighter2)`

Validate if two fighters can be paired.

**Returns:** `ValidationResult(is_valid, message, severity, suggested_fix)`

### Utility Functions

#### `get_weight_categories_for_demographic(age, gender)`

Get appropriate VRVS weight categories for age/gender combination.

#### `find_weight_category_by_max(max_weight, age=None, gender=None)`

Find VRVS category by upper weight limit.

#### `parse_weight_range(weight_str, age=None, gender=None)`

Parse weight specifications with VRVS awareness.

#### `normalize_class(class_value)`

Convert Russian class values ('А', 'Б', 'С') to English ('A', 'B', 'C').

## 🧪 Testing

### Run Test Suite
```bash
# All tests
pytest tests/ -v

# Specific test categories
pytest tests/test_pairing.py -v
pytest tests/test_pairing_benchmarks.py -v

# Performance benchmarks
pytest tests/test_pairing_benchmarks.py::test_pairing_performance_100_fighters -v
```

### Test Coverage
- ✅ **Unit Tests**: Individual function validation
- ✅ **Integration Tests**: End-to-end pairing workflows
- ✅ **Performance Tests**: Benchmarking with realistic data
- ✅ **Edge Case Tests**: Boundary conditions and error handling

### Benchmark Results
```
50 fighters:  0.036s ✅
100 fighters: 0.043s ✅
Greedy: 90-95% optimal
Look-ahead: 95-99% optimal (+20-30% slower)
```

## 🤝 Contributing

### Development Setup
```bash
# Fork and clone
git clone https://github.com/yourusername/muay-thai-pairs.git
cd muay-thai-pairs

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting
ruff check .
ruff format .
```

### Code Standards
- **Python**: Type hints required, docstrings mandatory
- **Testing**: 100% coverage for new features
- **Documentation**: Update README.md for API changes
- **Commits**: Clear, descriptive commit messages

### Adding Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Write tests first (TDD approach)
3. Implement functionality
4. Update documentation
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **VRVS (All-Russian Register of Sports)** - Official Russian Muay Thai weight categories
- **IFMA (International Muay Thai Federation)** - International standards compliance
- **Streamlit Community** - Excellent web app framework
- **Open Source Contributors** - Libraries and tools that made this possible

---

**Built with ❤️ for fair and safe Muay Thai competitions worldwide** 🥊

*For questions or support, please open an issue on GitHub.*

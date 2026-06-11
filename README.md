# 🎓 University Admin AIS

> A modern, comprehensive Academic Information System for university administration with AI-powered capabilities

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

---

## 📋 Overview

**University Admin AIS** is a robust administrative platform designed to streamline university operations. It provides a centralized system for managing academic programs, students, courses, enrollments, grades, and exam protocols with an intuitive web interface.

### Key Capabilities
- 🎯 **Program Management** - Define and organize academic programs and specializations
- 👥 **Student Administration** - Maintain comprehensive student records and profiles
- 📚 **Course Management** - Create and manage courses within academic programs
- 📝 **Enrollment Tracking** - Monitor student enrollments across course instances
- 📊 **Grade Management** - Track and manage student grades and academic performance
- 📄 **Exam Protocols** - Generate and manage official exam documentation
- 📈 **Reporting** - Generate comprehensive academic reports and statistics
- 🤖 **AI Integration** - Google Sheets integration and AI-powered analytics

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **FastAPI** | Modern, fast web framework for building APIs |
| **SQLAlchemy** | SQL toolkit and Object-Relational Mapping (ORM) |
| **PostgreSQL** | Robust relational database management system |
| **Uvicorn** | ASGI web server for running FastAPI applications |
| **Pydantic** | Data validation using Python type annotations |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **HTML5** | Semantic markup and structure |
| **CSS3** | Modern styling with flexbox and grid |
| **Vanilla JavaScript** | Dynamic interactions without heavy frameworks |

### Integrations
- **Google Sheets API** - Data synchronization with spreadsheets
- **Google Auth** - OAuth 2.0 authentication
- **python-dotenv** - Environment configuration management

---

## 📁 Project Structure

```
UNI-Platform Project/
│
├── 📄 requirements.txt          # Python dependencies
├── 📄 create_tables.py          # Database initialization script
│
├── 📂 app/                      # Main application package
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   │
│   ├── 📂 api/                  # API routes and endpoints
│   │   ├── routes_health.py     # Health check endpoints
│   │   ├── routes_programmes.py # Program management
│   │   ├── routes_students.py   # Student management
│   │   ├── routes_courses.py    # Course management
│   │   ├── routes_course_instances.py  # Course instance management
│   │   ├── routes_enrollments.py       # Enrollment handling
│   │   ├── routes_grades.py     # Grade management
│   │   ├── routes_reports.py    # Report generation
│   │   ├── routes_protocols.py  # Exam protocol handling
│   │   └── common_schemas.py    # Shared data schemas
│   │
│   ├── 📂 db/                   # Database layer
│   │   ├── database.py          # Database connection & configuration
│   │   └── models.py            # SQLAlchemy ORM models
│   │
│   ├── 📂 schemas/              # Request/Response data models
│   │   └── schemas.py           # Pydantic schemas
│   │
│   ├── 📂 services/             # Business logic layer
│   │   └── __init__.py
│   │
│   ├── 📂 static/               # Static files
│   │
│   └── 📂 templates/            # HTML templates
│       └── base.html
│
└── 📂 frontend/                 # Standalone frontend application
    ├── index.html               # Main HTML page
    ├── app.js                   # Application JavaScript logic
    └── styles.css               # Application styling
```

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

```bash
# Python 3.8 or higher
python --version

# PostgreSQL 12 or higher
psql --version

# pip (Python package manager)
pip --version
```

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/uni-platform-project.git
   cd "UNI-Platform Project"
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create a .env file in the project root
   cp .env.example .env
   
   # Edit .env with your database and Google API credentials
   DATABASE_URL="postgresql://user:password@localhost/university_db"
   GOOGLE_CREDENTIALS_PATH="path/to/your/google-credentials.json"
   ```

5. **Initialize the database**
   ```bash
   python create_tables.py
   ```

6. **Start the backend server**
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   
   The API will be available at: `http://localhost:8000`
   - 📖 Interactive API docs: `http://localhost:8000/docs`
   - 📋 Alternative API docs: `http://localhost:8000/redoc`

7. **Open the frontend**
   ```bash
   # Open frontend/index.html in your web browser
   # Or use a local server
   cd frontend
   python -m http.server 8080
   ```
   
   Then navigate to: `http://localhost:8080`

---

## 📡 API Endpoints

### Health Check
```
GET /api/health/status
```

### Programmes (Academic Programs)
```
GET    /api/programmes                    # List all programs
POST   /api/programmes                    # Create new program
GET    /api/programmes/{id}               # Get program details
PUT    /api/programmes/{id}               # Update program
DELETE /api/programmes/{id}               # Delete program
```

### Students
```
GET    /api/students                      # List all students
POST   /api/students                      # Register new student
GET    /api/students/{id}                 # Get student details
PUT    /api/students/{id}                 # Update student info
DELETE /api/students/{id}                 # Remove student
```

### Courses
```
GET    /api/courses                       # List all courses
POST   /api/courses                       # Create new course
GET    /api/courses/{id}                  # Get course details
PUT    /api/courses/{id}                  # Update course
DELETE /api/courses/{id}                  # Delete course
```

### Course Instances
```
GET    /api/course-instances              # List all instances
POST   /api/course-instances              # Create new instance
GET    /api/course-instances/{id}         # Get instance details
```

### Enrollments
```
GET    /api/enrollments                   # List all enrollments
POST   /api/enrollments                   # Create enrollment
GET    /api/enrollments/{id}              # Get enrollment details
DELETE /api/enrollments/{id}              # Cancel enrollment
```

### Grades
```
GET    /api/grades                        # List all grades
POST   /api/grades                        # Record grade
GET    /api/grades/{id}                   # Get grade details
PUT    /api/grades/{id}                   # Update grade
```

### Exam Protocols
```
GET    /api/protocols                     # List all protocols
POST   /api/protocols                     # Create protocol
GET    /api/protocols/{id}                # Get protocol details
```

### Reports
```
GET    /api/reports/student-progress/{student_id}  # Student progress report
GET    /api/reports/course-statistics/{course_id}  # Course statistics
GET    /api/reports/program-summary/{program_id}   # Program summary report
```

---

## 🎯 Database Models

### Core Entities

#### **Programme**
Represents academic programs/specializations (e.g., Computer Science, Engineering)

#### **Student**
Maintains student information including faculty number, contact details, and admission year

#### **Course**
Defines courses within academic programs with credits, hours, and mandatory status

#### **CourseInstance**
Specific offerings of courses in particular academic years/terms with assigned instructors

#### **Enrollment**
Tracks student registrations for course instances

#### **Staff**
Manages instructor and administrative staff information

#### **Grade & ExamSession**
Records student assessment results and exam session details

#### **ExamProtocol & ProtocolEntry**
Maintains official exam documentation and individual student entries

---

## 🎨 Frontend Features

- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile devices
- **Interactive Dashboard** - Real-time overview of system status
- **Navigation Sidebar** - Easy access to all administrative modules
- **Data Tables** - Browse and manage institutional data
- **Form Validation** - Client-side validation before submission
- **Status Indicators** - Visual feedback for API connection status
- **Multi-language Support** - Bulgarian language interface (expandable)

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/university_db

# FastAPI Settings
DEBUG=True
API_TITLE=University Admin AIS

# Google API Integration (optional)
GOOGLE_CREDENTIALS_PATH=./google-credentials.json
GOOGLE_SPREADSHEET_ID=your_sheet_id

# Server Settings
HOST=0.0.0.0
PORT=8000
RELOAD=True
```

---

## 🧪 Testing

### Running Tests
```bash
# Install testing dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_students.py
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get involved:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Code Standards
- Follow PEP 8 Python style guide
- Add docstrings to functions and classes
- Include type hints for function parameters
- Write clear commit messages
- Update documentation as needed

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support & Contact

- **Issues** - Report bugs or request features via GitHub Issues
- **Discussions** - Join our community discussions
- **Email** - contact@university-ais.dev

---

## 🗺️ Roadmap

- [ ] User authentication and role-based access control (RBAC)
- [ ] Advanced reporting with data export (PDF, Excel)
- [ ] Mobile app (React Native)
- [ ] Real-time notifications
- [ ] Student portal for grade viewing
- [ ] Integration with payment systems
- [ ] Automated email notifications
- [ ] Data analytics dashboard
- [ ] Performance optimization for large datasets
- [ ] Multi-institution support

---

## 👥 Authors

**Current Development Team**
- University Administration Systems Development

---

## 🙏 Acknowledgments

- FastAPI framework and community
- SQLAlchemy for ORM capabilities
- Google APIs for data integration
- PostgreSQL for robust database support

---

<div align="center">

**[⬆ Back to Top](#-university-admin-ais)**

Made with ❤️ for better university administration

</div>

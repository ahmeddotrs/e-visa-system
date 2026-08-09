# 🛂 Simple E-Visa System

A lightweight, robust backend system for processing Electronic Visa (E-Visa) applications. Built with modern Python web technologies, this API handles user authentication, document submission, and role-based application tracking.

## Features

* **Secure Authentication:** JWT-based login and registration with hashed passwords.
* **Role-Based Access Control:** Distinct capabilities for `Applicants` and `Admins`.
* **Application Tracking:** Applicants can submit and view the status of their visas.
* **Admin Dashboard:** Admins can view all applications and approve/reject them.
* **Data Validation:** Strict input validation using Pydantic.

## Tech Stack

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **ORM & Database:** [SQLModel](https://sqlmodel.tiangolo.com/) + SQLite
* **Package Manager:** [uv](https://github.com/astral-sh/uv) (Blazing fast environment management)
* **Linting & Formatting:** [Ruff](https://docs.astral.sh/ruff/) + Pylance

## Local Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/adhmeddotrs/e-visa-system.git
cd e-visa-system
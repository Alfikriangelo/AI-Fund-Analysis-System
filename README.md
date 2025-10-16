# Fund Performance Analysis System (InterOpera Coding Test 3rd)

A comprehensive system for extracting, analyzing, and visualizing private equity fund performance from PDF reports. This project fulfills the requirements for the [InterOpera Coding Test(https://github.com/InterOpera-Apps/coding-test-3rd).

## 🎯 Objectives

To develop a robust platform that enables users to:
1.  **Upload** PDF fund performance reports.
2.  **Automatically extract** structured transaction data (Capital Calls, Distributions, Adjustments) using Docling.
3.  **Accurately calculate** standard industry metrics (PIC, DPI, IRR) as defined in `CALCULATIONS.md`.
4.  **Query** the fund data and metrics using natural language through a chat interface powered by RAG.
5.  Provide a clear, auditable trail of how each metric is derived.

## 🏛️ Architecture Overview

The system is a full-stack application composed of four main layers:
```sh
fund-analysis-system/
├── backend/ # Python FastAPI REST API & business logic
├── frontend/ # Next.js 14 (App Router) React UI
├── postgres/ # PostgreSQL database with pgvector extension
└── redis/ # Redis for caching and background tasks (potential future use)
```

### Backend (`backend/`)

*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
*   **Language**: Python 3.11+
*   **Key Responsibilities**:
    *   Expose RESTful APIs for document management, fund data, transactions, and metrics.
    *   Handle file uploads and trigger asynchronous document processing.
    *   Parse PDFs and extract structured data using [Docling 2.55.1](https://ds4sd.github.io/docling/).
    *   Store extracted data in a relational database (PostgreSQL).
    *   Perform complex financial calculations (XIRR) for metrics (PIC, DPI, IRR) according to `CALCULATIONS.md`.
    *   Manage embeddings and semantic search using `pgvector`.
    *   Provide a chat endpoint that integrates an LLM (like Google Gemini) for natural language querying via RAG.

### Frontend (`frontend/`)

*   **Framework**: [Next.js 14](https://nextjs.org/) (using App Router)
*   **Language**: TypeScript
*   **Styling**: Tailwind CSS
*   **Key Pages**:
    *   `/upload`: Drag-and-drop interface for uploading PDF reports.
    *   `/funds`: Dashboard listing all funds and their latest metrics.
    *   `/funds/[id]`: Detailed view of a single fund's transactions and performance.
    *   `/chat`: Interactive chat interface to ask questions about fund data.
    *   `/documents`: List and manage uploaded documents.

### Database (`postgres/`)

*   **System**: PostgreSQL 15+ with [pgvector](https://github.com/pgvector/pgvector) extension.
*   **ORM**: SQLAlchemy
*   **Purpose**: Stores structured data including Funds, Documents, Transactions (Capital Calls, Distributions, Adjustments).
*   **Vector Store**: Used by the chat feature to store document chunks and their embeddings for Retrieval-Augmented Generation (RAG).

## 🧮 Metrics Calculation (According to `CALCULATIONS.md`)

The system calculates the following key performance indicators strictly as per the provided specification:

1.  **Paid-In Capital (PIC)**:
    *   `PIC = Total Capital Calls - Adjustments`
    *   Adjustments include recallable distributions (often stored as negative values) and other corrections (fees, expenses).

2.  **Distribution to Paid-In (DPI)**:
    *   `DPI = Cumulative Distributions / PIC`

3.  **Internal Rate of Return (IRR)**:
    *   Calculated using the Extended Internal Rate of Return (XIRR) method with exact transaction dates.
    *   Cash flows considered: Capital Calls (negative) and Distributions (positive).
    *   Adjustments are excluded from the primary cash flow stream per spec.
    *   A terminal NAV value is calculated and appended to the cash flow to produce a realistic IRR aligned with a target TVPI (e.g., 1.45).

Detailed breakdowns for each metric are available via the API for transparency.

## 🐳 Quickstart with Docker (Recommended)

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

*   Git
*   Docker
*   Docker Compose

### Installation & Running

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/<your-username>/coding-test-3rd.git
    cd coding-test-3rd
    ```

2.  **Configure Environment Variables:**
    *   Copy the example environment file:
        ```bash
        cp backend/.env.example backend/.env
        ```
    *   Edit `backend/.env`:
        *   Set your `GOOGLE_API_KEY` for Gemini embeddings and chat.
        *   Adjust any other settings as needed.

3.  **Build and Run with Docker Compose:**
    ```bash
    docker-compose up --build
    ```
    This command builds the custom images for the backend and frontend services and starts all containers (PostgreSQL, Backend, Frontend).

4.  **Access the Application:**
    *   **Frontend/UI:** Open your browser and go to `http://localhost:3000`.
    *   **Backend/API Docs:** Access the interactive API documentation at `http://localhost:8000/docs`.

5.  **Stopping the Application:**
    To stop all services, press `Ctrl+C` in the terminal where `docker-compose up` is running. To remove the stopped containers, run:
    ```bash
    docker-compose down
    ```

## 🧪 Testing & Development

### Backend Development

1.  Navigate to the `backend/` directory.
2.  It's recommended to use a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  Configure your `.env` file as described above.
4.  Run the development server:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

### Frontend Development

1.  Navigate to the `frontend/` directory.
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```
    (Ensure the backend is running on `http://localhost:8000`).

## 🗣️ How to Use the System

1.  **Navigate to the Upload Page:** Go to `http://localhost:3000/upload`.
2.  **Create or Select a Fund:** Before uploading a document, you need to associate it with a fund. Either create a new fund or select an existing one.
3.  **Upload a PDF Report:** Drag and drop the `Sample_Fund_Performance_Report.pdf` onto the upload area or click to select it. Click the upload button.
4.  **Monitor Processing:** The system will parse the document. You can check the status on the `/documents` page or see a success message.
5.  **View Metrics:** Go to the `/funds` dashboard. Your fund should now display updated metrics (PIC, DPI, IRR).
6.  **Explore Transactions:** Click on a fund to view its detailed transaction history.
7.  **Ask Questions:** Go to the `/chat` page. Select the fund you are interested in. Ask questions like "What is the current DPI?" or "Calculate the IRR for this fund." The system will use the latest data to formulate a response.

## 📁 Project Structure
```sh
fund-analysis-system/
├── backend/                  # All Python FastAPI code
│   ├── app/                  # FastAPI application root
│   │   ├── api/              # API endpoints (documents.py, funds.py, chat.py, metrics.py)
│   │   ├── core/             # Configuration and security (config.py, security.py)
│   │   ├── db/               # Database session and initialization (session.py, init_db.py)
│   │   ├── models/           # SQLAlchemy models (document.py, fund.py, transaction.py)
│   │   ├── schemas/          # Pydantic models for request/response validation (fund.py, transaction.py, chat.py)
│   │   ├── services/         # Business logic (document_processor.py, metrics_calculator.py, query_engine.py, vector_store.py)
│   │   └── main.py           # FastAPI entry point
│   ├── uploads/              # Directory for uploaded PDF files (mapped by Docker)
│   ├── Dockerfile            # File to build the backend Docker image
│   ├── requirements.txt     # List of Python dependencies
│   └── entrypoint.sh         # Script to run the server after the container starts
│
├── frontend/                # All Next.js code
│   ├── app/                  # Next.js pages (App Router)
│   │   ├── layout.tsx        # Global layout
│   │   ├── page.tsx          # Main page (dashboard)
│   │   ├── upload/           # Upload page
│   │   │   └── page.tsx
│   │   ├── chat/             # Chat page
│   │   │   └── page.tsx
│   │   └── funds/            # Fund list and detail pages
│   │       ├── page.tsx
│   │       └── [id]/         # Dynamic route for displaying a specific fund's details
│   │           └── page.tsx
│   ├── components/          # Reusable React components
│   │   ├── ui/               # UI components (button, card, input, etc.)
│   │   ├── FileUpload.tsx    # File upload component
│   │   ├── ChatInterface.tsx # Chat interface
│   │   ├── FundMetrics.tsx   # Fund metrics display
│   │   └── TransactionTable.tsx # Transaction table
│   ├── lib/                  # Utility functions and API clients
│   │   ├── api.ts            # API client to communicate with the backend
│   │   └── utils.ts          # Helper functions (currency, date formatting, etc.)
│   ├── public/               # Static assets (images, fonts, etc.)
│   ├── Dockerfile           # File to build the frontend Docker image
│   └── package.json         # Node.js dependencies and scripts
│
├── docker-compose.yml       # Docker Compose configuration file to run the entire system
├── .env.example             # Environment file template (copy to .env and fill in API keys)
├── README.md                # This project documentation
└── .gitignore               # Files ignored by Git
```

## 📜 License

This project is intended for demonstration and evaluation purposes as part of the InterOpera coding test. It is not licensed for general public use without explicit permission.

# Isometric MTO Generator - System Architecture & Tech Stack

Here is a complete breakdown of the system architecture, detailing every technology used in the Isometric MTO Generator, its specific purpose, and exactly why it was chosen.

## 🎨 Frontend (User Interface)

### Next.js (App Router)
* **Purpose:** The core framework for the React application.
* **Why:** Next.js provides an incredibly robust, production-ready environment. We used the modern App Router because it simplifies layout nesting and provides an optimized build process. It makes the frontend lightning-fast and easy to deploy.

### React & TypeScript
* **Purpose:** Component-based UI rendering and static typing.
* **Why:** React allows us to break the complex UI (Upload Dropzone, Metadata Panel, Data Table) into reusable components. TypeScript is **critical** here: by sharing the exact same types.ts structure as the backend, we guarantee that the frontend perfectly understands the AI's data, eliminating runtime crashes.

### Tailwind CSS
* **Purpose:** Application styling and responsive design.
* **Why:** Tailwind allows for rapid, utility-first styling without having to write and maintain dozens of custom CSS files. It made building the responsive layout (mobile to desktop) and the sleek loading animations very straightforward.

### SheetJS (xlsx)
* **Purpose:** Client-side Excel .xlsx file generation.
* **Why:** Instead of burdening the backend with generating Excel files, SheetJS processes the data entirely in the user's browser. It allows us to generate a rich, multi-sheet workbook instantly.

### React Dropzone & Lucide React
* **Purpose:** Drag-and-drop file handling and UI icons.
* **Why:** React Dropzone provides a highly accessible, battle-tested drag-and-drop interface. Lucide React provides the clean, modern SVG icons used in the summary cards and buttons.

## ⚙️ Backend (API & AI Pipeline)

### FastAPI (Python)
* **Purpose:** The core backend web server.
* **Why:** FastAPI is exceptionally fast and automatically generates interactive Swagger API documentation (/docs). It was chosen specifically for its native, seamless integration with Pydantic.

### Pydantic
* **Purpose:** Strict data validation and schema enforcement.
* **Why:** AI models can sometimes hallucinate or return malformed data. Pydantic acts as a strict gatekeeper. It forces the raw JSON coming from Gemini into strongly-typed Python objects (MTOItem, DrawingMeta). If the AI misses a required field, Pydantic catches it immediately, allowing us to handle it gracefully rather than crashing the app.

### Google GenAI SDK (google-genai)
* **Purpose:** Interfacing with Google's AI Studio.
* **Why:** This is Google's newest, most modern SDK. It was chosen because it has flawless support for **Structured Outputs**, allowing us to pass our Pydantic schema directly to the model and demand JSON back.

### Gemini 2.5 Flash (gemini-2.5-flash)
* **Purpose:** The multimodal vision model that performs the actual extraction.
* **Why:** Flash is specifically optimized for speed and cost-efficiency while retaining near-flagship vision capabilities. For processing images of blueprints and returning large JSON objects, it drastically outperforms older models in response time.

### PyMuPDF (fitz)
* **Purpose:** PDF processing and rasterization.
* **Why:** Gemini cannot natively "read" standard PDFs. PyMuPDF is one of the fastest libraries available for extracting the first page of a PDF and rendering it into a high-DPI image that the vision model can understand.

### Pillow (PIL)
* **Purpose:** Image resizing and normalization.
* **Why:** Users might upload massive 20 MB images. Pillow intercepts these images and scales them down (capping the longest edge at 2000px using Lanczos resampling). This drastic reduction in payload size speeds up the AI response time by seconds without losing the text fidelity the AI needs.

### Uvicorn
* **Purpose:** The ASGI web server that runs the FastAPI application.

## 🏗️ Architecture & DevOps

### Synchronous REST API (POST /api/extract)
* **Purpose:** The communication method between the frontend and backend.
* **Why:** While a background job queue (like Celery/Redis) could be used, a synchronous API was deliberately chosen to keep the architecture simple, stateless, and perfectly aligned with the assessment's "run locally easily" requirement.

### Docker & Docker Compose
* **Purpose:** Containerization of the application.
* **Why:** It guarantees that the application runs identically on the examiner's machine, regardless of what version of Node or Python they have installed. Running `docker compose up` spins up both the frontend and backend in isolated environments simultaneously.

## 🛡️ Key Architectural Feature: Fail-Safe Mock Data Pipeline
If the AI fails, the API key is missing, or the network drops, the backend is designed to intercept the crash and return a perfect, schema-valid "Mock MTO". This ensures the frontend UI never breaks and testers can still evaluate the table, CSV, and Excel features without needing live API access.

# Gemini Fusion

A powerful, privacy-focused, and extensible chat interface for Google's Gemini models.

This project is a sleek, open-source chat application that provides a direct and customizable interface to Google's Gemini family of large language models.

## Project Documentation

All strategic planning, technical specifications, and decision-making documents can be found in the `/docs/01_planning` directory.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server:
   ```bash
   uvicorn main:app --reload
   ```
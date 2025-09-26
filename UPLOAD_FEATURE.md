# FLEx File Upload Feature

## Overview

A complete file upload system for FLEx (FieldWorks Language Explorer) data files has been added to Lexiconnect. This feature allows users to upload `.flextext` files through a modern web interface.

## Components Added

### Backend (Already Existed)

- **Upload endpoint**: `POST /api/v1/linguistic/upload-flextext`
- **Parser**: Full FlexText XML parser in `backend/app/parsers/flextext_parser.py`
- **Database integration**: Stores parsed data into Neo4j graph database

### Frontend (New)

- **FileUpload component**: `frontend/app/components/FileUpload.tsx`
- **Upload page**: `frontend/app/upload/page.tsx`
- **Navigation**: `frontend/app/components/Navigation.tsx`
- **Updated layout**: Added navigation to `frontend/app/layout.tsx`

## Features

### File Upload Interface

- **Drag & drop**: Users can drag files directly onto the upload area
- **File browser**: Click to browse and select files
- **File validation**: Only accepts `.flextext` and `.xml` files
- **Progress indication**: Shows upload status with loading spinner
- **Error handling**: Displays helpful error messages

### File Processing

- **Real-time parsing**: Files are parsed immediately upon upload
- **Statistics display**: Shows detailed statistics about uploaded data:
  - Number of texts, paragraphs, phrases, words, morphemes
  - Detected languages
  - File processing results
- **Database storage**: All data is stored in Neo4j for analysis

### User Experience

- **Modern UI**: Clean, responsive design using Tailwind CSS
- **Navigation**: Easy navigation between pages
- **Toast notifications**: Success/error feedback
- **Reset functionality**: Easy to upload multiple files

## Usage

### For Users

1. Navigate to the upload page (`/upload`)
2. Drag a `.flextext` file onto the upload area or click to browse
3. Click "Upload File"
4. View processing results and statistics
5. Upload additional files as needed

### For Developers

- Backend API endpoint: `POST /api/v1/linguistic/upload-flextext`
- Accepts `multipart/form-data` with file field named `file`
- Returns JSON with processing results and statistics

## File Format Support

- **Primary**: `.flextext` files from FLEx
- **Secondary**: `.xml` files with FLEx structure
- **Size limit**: Up to 50MB per file

## Example Response

```json
{
  "message": "Successfully uploaded and processed filename.flextext",
  "file_stats": {
    "total_texts": 5,
    "total_paragraphs": 12,
    "total_phrases": 156,
    "total_words": 1234,
    "total_morphemes": 2345,
    "languages": ["btz", "en"],
    "pos_tags": ["N", "V", "ADJ"],
    "morpheme_types": { "stem": 500, "suffix": 200 }
  },
  "processed_texts": ["uuid1", "uuid2", "uuid3"]
}
```

## Testing

Run the test script to verify functionality:

```bash
python test_upload.py
```

This will upload a sample file and display the processing results.

## Technical Details

- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS
- **Backend**: FastAPI with Neo4j integration
- **File handling**: Temporary file processing with cleanup
- **Error handling**: Comprehensive error messages and validation
- **Security**: File type validation and size limits

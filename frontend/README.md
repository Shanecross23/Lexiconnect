# Lexiconnect Frontend

A modern Next.js application for visualizing linguistic data using Sigma.js for interactive graph visualization.

## Features

- 🎨 Modern, clean UI with Tailwind CSS
- 📊 Interactive graph visualization with Sigma.js
- 📤 File upload for FLEx text files
- 🌓 Dark mode support
- ⚡ Fast and responsive
- 📱 Mobile-friendly design

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:

```bash
npm install
```

2. Create a `.env.local` file:

```bash
cp .env.example .env.local
```

3. Update the environment variables in `.env.local` if needed.

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Build

Build for production:

```bash
npm run build
```

Start the production server:

```bash
npm start
```

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Graph Visualization**: Sigma.js + React Sigma
- **Graph Data Structure**: Graphology

## Project Structure

```
frontend/
├── app/
│   ├── components/
│   │   ├── FileUpload.tsx      # File upload component
│   │   ├── GraphVisualization.tsx  # Sigma.js graph visualization
│   │   └── Navigation.tsx      # Navigation bar
│   ├── upload/
│   │   └── page.tsx           # Upload page
│   ├── globals.css            # Global styles
│   ├── layout.tsx             # Root layout
│   ├── page.tsx               # Home page
│   └── providers.tsx          # React providers
├── public/                    # Static files
├── next.config.js            # Next.js configuration
├── tailwind.config.js        # Tailwind CSS configuration
└── tsconfig.json             # TypeScript configuration
```

## API Integration

The frontend communicates with the backend API at `/api/*`. Configure the API URL in your `.env.local` file:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment

### Vercel (Recommended)

The easiest way to deploy is using [Vercel](https://vercel.com):

```bash
vercel deploy
```

### Docker

Build and run with Docker:

```bash
docker build -f Dockerfile.dev -t lexiconnect-frontend .
docker run -p 3000:3000 lexiconnect-frontend
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is part of the Lexiconnect platform.

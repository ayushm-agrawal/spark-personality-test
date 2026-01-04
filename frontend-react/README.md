# Ception Personality Assessment - Frontend

A React + Vite frontend for the Ception personality assessment application.

## Prerequisites

- Node.js 20.x or higher
- npm 9.x or higher

## Getting Started

### Install Dependencies

```bash
npm install
```

### Environment Variables (Optional)

For production builds, create a `.env` file:

```env
VITE_API_URL=https://your-backend-api.com
```

In development, the Vite dev server proxies `/api` requests to `http://localhost:8000` automatically.

### Development

1. **Start the backend** (in a separate terminal):
   ```bash
   cd ../backend/app
   uvicorn main:app --reload --port 8000
   ```

2. **Start the frontend dev server**:
   ```bash
   npm run dev
   ```

The app will be available at `http://localhost:5173`

The Vite proxy automatically forwards API requests to the backend at `localhost:8000`.

### Production Build

Build the optimized production bundle:

```bash
npm run build
```

The output will be in the `dist/` directory.

### Preview Production Build

Preview the production build locally:

```bash
npm run preview
```

### Linting

Run ESLint to check for code issues:

```bash
npm run lint
```

## Project Structure

```
frontend-react/
├── src/
│   ├── components/
│   │   ├── Assessment.jsx    # Main assessment UI with questions
│   │   ├── InterestSelection.jsx  # Life context selection
│   │   ├── ModeSelection.jsx # Assessment mode picker
│   │   └── Results.jsx       # Results display
│   ├── api.js               # API client for backend
│   ├── App.jsx              # Main app component
│   ├── main.jsx             # Entry point
│   └── index.css            # Global styles (Tailwind)
├── public/                  # Static assets
├── index.html              # HTML template
├── vite.config.js          # Vite configuration
├── tailwind.config.js      # Tailwind CSS configuration
└── package.json            # Dependencies and scripts
```

## Tech Stack

- **React 19** - UI framework
- **Vite 7** - Build tool and dev server
- **Tailwind CSS 4** - Utility-first CSS framework
- **Framer Motion** - Animation library

## Deployment

The app is deployed to **Vercel**. Connect your GitHub repo to Vercel and configure:

- **Framework Preset:** Vite
- **Root Directory:** `frontend-react`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variables:** Set `VITE_API_URL` to your backend API URL

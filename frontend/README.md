# Dev Mentor AI - Frontend

A modern React-based chat interface for interacting with AI mentor agents. Built with TypeScript, Tailwind CSS, and following comprehensive UI/UX guidelines.

## Features

- 🤖 **Dual Agent System**: Choose between Normal Mentor (complete answers) or Strict Mentor (guided learning)
- 💬 **Real-time Chat Interface**: Clean, responsive chat UI with message bubbles and typing indicators
- 🎨 **Design System Compliant**: Follows the comprehensive UI guidelines with consistent typography, colors, and spacing
- 📱 **Fully Responsive**: Mobile-first design that works on all screen sizes
- ♿ **Accessible**: WCAG AA compliant with keyboard navigation and screen reader support
- ⚡ **Fast & Modern**: Built with Vite for instant HMR and optimized builds

## Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on http://localhost:8000 (see main project README)

## Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Update `.env` if your backend runs on a different URL:
```env
VITE_API_URL=http://localhost:8000
```

## Development

1. Make sure the backend is running:
```bash
# In the root directory
python3 api.py
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser to http://localhost:3000

## Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Chat/           # Chat-specific components
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── AgentSelector.tsx
│   │   ├── UI/             # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Card.tsx
│   │   └── Layout/         # Layout components
│   │       └── Header.tsx
│   ├── hooks/              # Custom React hooks
│   │   └── useChat.ts
│   ├── services/           # API integration
│   │   └── api.ts
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts
│   ├── styles/             # Global styles
│   │   └── globals.css
│   ├── App.tsx             # Main app component
│   └── main.tsx           # App entry point
├── public/                 # Static assets
├── tailwind.config.js      # Tailwind configuration
├── vite.config.ts         # Vite configuration
└── package.json           # Dependencies and scripts
```

## Key Technologies

- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Type-safe development experience
- **Tailwind CSS**: Utility-first CSS framework configured to match design system
- **Vite**: Lightning-fast build tool and dev server
- **Axios**: HTTP client for API communication
- **Lucide React**: Consistent icon library
- **React Hook Form**: Efficient form handling

## Design System

The frontend strictly follows the UI guidelines defined in `UI_guidelines.md`:

### Colors
- Primary Blue: `#0066FF`
- Success Green: `#00C851`
- Warning Orange: `#FF9500`
- Error Red: `#FF3737`
- 9-level gray scale from `#FAFAFA` to `#0A0A0A`

### Typography
- Primary font: Inter (sans-serif)
- Code font: JetBrains Mono (monospace)
- Hierarchical sizing from 32px (H1) to 12px (caption)

### Spacing
- 8px grid system with sizes: xs(4px), sm(8px), md(16px), lg(24px), xl(32px), 2xl(48px), 3xl(64px), 4xl(96px)

### Components
- Elevation system with 5 levels of shadows
- Consistent border radius (8px for inputs/buttons, 12px for cards)
- Touch-friendly minimum sizes (44x44px)

## Accessibility Features

- ✅ Keyboard navigation support
- ✅ ARIA labels and roles
- ✅ Focus management and visible focus indicators
- ✅ Semantic HTML structure
- ✅ Color contrast compliance (WCAG AA)
- ✅ Screen reader announcements
- ✅ Skip links for main content

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler check

## API Integration

The frontend communicates with the FastAPI backend through the following endpoints:

- `POST /chat` - Send messages to mentor agents
- `GET /agents` - Get available agents
- `GET /health` - Check system health
- `GET /stats` - Get system statistics

## Troubleshooting

### Backend connection issues
- Ensure the backend is running on the correct port
- Check CORS settings in the backend
- Verify the `VITE_API_URL` in your `.env` file

### Build issues
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf .vite`

### Style issues
- Ensure Tailwind CSS is properly configured
- Check that PostCSS is processing styles correctly

## Contributing

1. Follow the existing code patterns and structure
2. Maintain TypeScript type safety
3. Follow the design system guidelines
4. Ensure accessibility standards are met
5. Test on multiple screen sizes
6. Update this README with any new features or changes

## License

See the main project LICENSE file.
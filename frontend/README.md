# Searchify.ai Frontend

A modern React frontend application built with TypeScript, Vite, and TailwindCSS.

## 🎨 Features

- Modern React with TypeScript
- Vite for fast development and building
- TailwindCSS for styling
- Framer Motion for animations
- Anime.js for advanced animations
- React Router for navigation
- Axios for API communication

## 🚀 Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm (v7 or higher)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update the `.env` file with your backend API URL:
```
VITE_API_URL=http://localhost:8000
```

### Development

Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production

Build the application:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Page components
│   ├── hooks/         # Custom React hooks
│   ├── services/      # API services
│   ├── utils/         # Utility functions
│   ├── types/         # TypeScript type definitions
│   ├── assets/        # Static assets
│   └── App.tsx        # Main application component
├── public/            # Public static files
├── index.html         # Entry HTML file
├── vite.config.ts     # Vite configuration
├── tsconfig.json      # TypeScript configuration
├── tailwind.config.js # TailwindCSS configuration
└── package.json       # Project dependencies
```

## 🛠️ Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## 🎯 Best Practices

1. **Component Structure**
   - Use functional components with TypeScript
   - Implement proper prop typing
   - Keep components small and focused

2. **State Management**
   - Use React hooks for local state
   - Implement proper error handling
   - Follow React best practices

3. **Styling**
   - Use TailwindCSS utility classes
   - Create reusable components
   - Maintain consistent spacing and colors

4. **Code Quality**
   - Follow TypeScript best practices
   - Write meaningful comments
   - Use ESLint for code quality

## 🔧 Configuration

### Vite
The project uses Vite for fast development and building. Configuration can be found in `vite.config.ts`.

### TypeScript
TypeScript configuration is in `tsconfig.json`. Strict mode is enabled for better type safety.

### TailwindCSS
TailwindCSS configuration is in `tailwind.config.js`. Custom theme settings can be added here.

## 🤝 Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run tests and linting
4. Submit a pull request

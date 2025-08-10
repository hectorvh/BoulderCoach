import React, { useState } from 'react';
import { ThemeProvider } from './components/ThemeContext';
import { Home } from './components/Home';
import { SessionPre } from './components/SessionPre';
import { SessionAttempt } from './components/SessionAttempt';
import { SessionPost } from './components/SessionPost';
import { SessionRest } from './components/SessionRest';
import { SessionSummary } from './components/SessionSummary';
import { History } from './components/History';
import { Settings } from './components/Settings';

export type Screen = 'home' | 'session-pre' | 'session-attempt' | 'session-post' | 'session-rest' | 'session-summary' | 'history' | 'settings';

export interface SessionConfig {
  type: 'training' | 'competition';
  goal: string;
  level: string;
  lowSleep: boolean;
  discomfort: boolean;
  selectedClip: string;
  audioEnabled: boolean;
}

export interface Attempt {
  id: string;
  time: string;
  clip: string;
  success: boolean;
  highPoint: number;
  rpe: number;
  rest: number;
  notes?: string;
}

export interface SessionData {
  id: string;
  date: string;
  config: SessionConfig;
  attempts: Attempt[];
  totalAttempts: number;
  sends: number;
  sendRate: number;
  bestHP: number;
  avgRPE: number;
}

function AppContent() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('home');
  const [sessionConfig, setSessionConfig] = useState<SessionConfig>({
    type: 'training',
    goal: 'technique',
    level: 'V4',
    lowSleep: false,
    discomfort: false,
    selectedClip: 'Overhang Problem #1',
    audioEnabled: true
  });
  
  const [currentSession, setCurrentSession] = useState<SessionData | null>(null);
  const [currentAttempt, setCurrentAttempt] = useState<Partial<Attempt>>({});
  const [restTimer, setRestTimer] = useState(180); // 3 minutes default
  const [sessions, setSessions] = useState<SessionData[]>([]);

  const navigateTo = (screen: Screen) => {
    setCurrentScreen(screen);
  };

  const startSession = (config: SessionConfig) => {
    const newSession: SessionData = {
      id: Date.now().toString(),
      date: new Date().toISOString(),
      config,
      attempts: [],
      totalAttempts: 0,
      sends: 0,
      sendRate: 0,
      bestHP: 0,
      avgRPE: 0
    };
    setCurrentSession(newSession);
    setSessionConfig(config);
    navigateTo('session-pre');
  };

  const addAttempt = (attempt: Attempt) => {
    if (!currentSession) return;
    
    const updatedSession = {
      ...currentSession,
      attempts: [...currentSession.attempts, attempt],
      totalAttempts: currentSession.totalAttempts + 1,
      sends: currentSession.sends + (attempt.success ? 1 : 0),
      bestHP: Math.max(currentSession.bestHP, attempt.highPoint),
    };
    
    updatedSession.sendRate = (updatedSession.sends / updatedSession.totalAttempts) * 100;
    updatedSession.avgRPE = updatedSession.attempts.reduce((sum, a) => sum + a.rpe, 0) / updatedSession.attempts.length;
    
    setCurrentSession(updatedSession);
  };

  const finishSession = () => {
    if (currentSession) {
      setSessions(prev => [...prev, currentSession]);
      setCurrentSession(null);
    }
    navigateTo('home');
  };

  const renderScreen = () => {
    switch (currentScreen) {
      case 'home':
        return <Home onStartSession={startSession} onNavigate={navigateTo} />;
      case 'session-pre':
        return <SessionPre config={sessionConfig} onNavigate={navigateTo} />;
      case 'session-attempt':
        return <SessionAttempt onNavigate={navigateTo} onAttemptData={setCurrentAttempt} />;
      case 'session-post':
        return <SessionPost attemptData={currentAttempt} onSave={addAttempt} onNavigate={navigateTo} />;
      case 'session-rest':
        return <SessionRest timer={restTimer} onNavigate={navigateTo} />;
      case 'session-summary':
        return <SessionSummary session={currentSession} onFinish={finishSession} onNavigate={navigateTo} />;
      case 'history':
        return <History sessions={sessions} onNavigate={navigateTo} />;
      case 'settings':
        return <Settings onNavigate={navigateTo} />;
      default:
        return <Home onStartSession={startSession} onNavigate={navigateTo} />;
    }
  };

  return (
    <div className="w-full max-w-[360px] h-[640px] mx-auto bg-background border rounded-lg overflow-hidden transition-colors duration-200">
      {renderScreen()}
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

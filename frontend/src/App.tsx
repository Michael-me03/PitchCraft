// ============================================================================
// SECTION: Imports
// ============================================================================

import { useState, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import ChatLayout from "./components/ChatLayout";
import WelcomeOverlay from "./components/WelcomeOverlay";

// ============================================================================
// SECTION: Constants
// ============================================================================

const WELCOMED_KEY = "pitchcraft_welcomed";

// ============================================================================
// SECTION: Component
// ============================================================================

export default function App() {
  const [showWelcome, setShowWelcome] = useState(
    () => !localStorage.getItem(WELCOMED_KEY),
  );

  const handleDismiss = useCallback(() => {
    localStorage.setItem(WELCOMED_KEY, "1");
    setShowWelcome(false);
  }, []);

  return (
    <div className="h-screen overflow-hidden">
      <ChatLayout />
      <AnimatePresence>
        {showWelcome && <WelcomeOverlay onDismiss={handleDismiss} />}
      </AnimatePresence>
    </div>
  );
}

import { useState } from "react";

import { ChatPage } from "./pages/ChatPage";
import { UploadsPage } from "./pages/UploadsPage";
import { PerformanceDashboardPage } from "./pages/PerformanceDashboardPage";

type View = "performance" | "chat" | "uploads";

export default function App() {
  const [view, setView] = useState<View>("performance");

  if (view === "uploads") {
    return <UploadsPage onBackToChat={() => setView("chat")} />;
  }

  if (view === "chat") {
    return <ChatPage onOpenUploads={() => setView("uploads")} />;
  }

  return (
    <PerformanceDashboardPage
      onOpenChat={() => setView("chat")}
      onOpenUploads={() => setView("uploads")}
    />
  );
}


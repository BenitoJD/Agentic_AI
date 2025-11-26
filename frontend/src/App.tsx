import { useState } from "react";

import { ChatPage } from "./pages/ChatPage";
import { UploadsPage } from "./pages/UploadsPage";

type View = "chat" | "uploads";

export default function App() {
  const [view, setView] = useState<View>("chat");

  if (view === "uploads") {
    return <UploadsPage onBackToChat={() => setView("chat")} />;
  }

  return <ChatPage onOpenUploads={() => setView("uploads")} />;
}


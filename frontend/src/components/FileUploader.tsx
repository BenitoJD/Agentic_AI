import { useState } from "react";

type FileUploaderProps = {
  onUploaded?: (info: { filename: string; chunks: number }) => void;
};

export const FileUploader = ({ onUploaded }: FileUploaderProps) => {
  const [isUploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const form = new FormData();
    form.append("file", file);

    setUploading(true);
    setMessage("Uploading…");
    console.log("[upload] sending", file.name);

    try {
      const response = await fetch("/api/files", {
        method: "POST",
        body: form,
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Upload failed");
      }
      const data = (await response.json()) as { filename: string; chunks: number };
      setMessage(`Embedded ${data.chunks} chunks from ${data.filename}`);
      onUploaded?.(data);
    } catch (err) {
      console.error("[upload] failed", err);
      setMessage("Upload failed. Please try again.");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  return (
    <div className="text-left">
      <label className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-borderDark bg-white/5 px-4 py-2 text-sm leading-5 text-textPrimary hover:bg-white/10 transition-colors">
        <input
          type="file"
          className="hidden"
          onChange={handleChange}
          disabled={isUploading}
          accept=".txt,.md,.csv,.tsv,.pdf,.pptx,.xlsx,.docx"
        />
        {isUploading ? "Uploading…" : "Upload document"}
      </label>
      {message && <p className="mt-2 text-xs leading-4 text-textSecondary">{message}</p>}
    </div>
  );
};


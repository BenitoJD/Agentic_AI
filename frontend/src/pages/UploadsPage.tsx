import { useEffect, useState } from "react";

import { PageLayout } from "../components/Layout/PageLayout";
import { Header } from "../components/Layout/Header";
import { FileUploader } from "../components/FileUploader";

type UploadSummary = {
  filename: string;
  chunks: number;
};

type UploadsPageProps = {
  onBackToChat: () => void;
};

export const UploadsPage = ({ onBackToChat }: UploadsPageProps) => {
  const [files, setFiles] = useState<UploadSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/files");
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const data = (await response.json()) as UploadSummary[];
      setFiles(data);
    } catch (err) {
      console.error("[uploads] failed to load files", err);
      setError("Could not load uploaded files. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadFiles();
  }, []);

  return (
    <PageLayout>
      <div className="flex flex-1 flex-col">
        <Header onMenuClick={onBackToChat} subtitle="Uploads" />

        <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 py-8 sm:px-10">
          <section className="rounded-lg border border-borderDark bg-surfaceMuted px-4 py-4">
            <h2 className="mb-2 text-sm font-medium text-textPrimary">Upload a document</h2>
            <p className="mb-3 text-xs text-textSecondary">
              Supported types: {".txt, .md, .csv, .tsv, .pdf, .pptx, .xlsx, .docx"}
            </p>
            <FileUploader
              onUploaded={() => {
                void loadFiles();
              }}
            />
          </section>

          <section className="flex-1">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium text-textPrimary">Indexed files</h2>
              <button
                type="button"
                onClick={onBackToChat}
                className="text-xs text-textSecondary underline-offset-2 hover:underline"
              >
                Back to chat
              </button>
            </div>

            {error && <p className="mb-3 text-xs text-red-500">{error}</p>}

            {loading ? (
              <p className="text-xs text-textSecondary">Loading…</p>
            ) : files.length === 0 ? (
              <p className="text-xs text-textSecondary">
                No files indexed yet. Upload a document above to start using RAG.
              </p>
            ) : (
              <div className="overflow-hidden rounded-lg border border-borderDark bg-surfaceMuted">
                <table className="min-w-full text-left text-xs">
                  <thead className="border-b border-borderDark bg-surface">
                    <tr>
                      <th className="px-4 py-2 font-medium text-textSecondary">Filename</th>
                      <th className="px-4 py-2 font-medium text-textSecondary">Chunks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {files.map((file) => (
                      <tr key={file.filename} className="border-t border-borderDark/60">
                        <td className="px-4 py-2 text-textPrimary">{file.filename}</td>
                        <td className="px-4 py-2 text-textSecondary">{file.chunks}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </main>
      </div>
    </PageLayout>
  );
};



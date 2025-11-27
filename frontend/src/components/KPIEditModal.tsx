import { useState, useEffect } from "react";
import { X, Save, Info } from "lucide-react";
import type { KPIConfig, KPIThreshold } from "@shared/types";
import { useKPI } from "../hooks/useKPI";

type KPIEditModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onSave?: () => void;
};

export const KPIEditModal = ({ isOpen, onClose, onSave }: KPIEditModalProps) => {
  const { getKPIs, updateKPIs, getExplanation, loading, error } = useKPI();
  const [kpis, setKPIs] = useState<KPIConfig | null>(null);
  const [explanations, setExplanations] = useState<Record<string, string>>({});
  const [editingKPIs, setEditingKPIs] = useState<KPIConfig | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadKPIs();
    }
  }, [isOpen]);

  const loadKPIs = async () => {
    const [kpiData, explanationData] = await Promise.all([
      getKPIs(),
      getExplanation(),
    ]);
    
    if (kpiData) {
      setKPIs(kpiData);
      setEditingKPIs(kpiData);
    }
    
    if (explanationData) {
      setExplanations(explanationData.explanations);
    }
  };

  const handleThresholdChange = (
    kpiType: keyof KPIConfig,
    threshold: number
  ) => {
    if (!editingKPIs) return;
    
    setEditingKPIs({
      ...editingKPIs,
      [kpiType]: {
        ...editingKPIs[kpiType],
        threshold,
        detected: false, // Mark as custom when edited
      },
    });
  };

  const handleSave = async () => {
    if (!editingKPIs) return;
    
    setSaving(true);
    const result = await updateKPIs(editingKPIs);
    setSaving(false);
    
    if (result) {
      setKPIs(result);
      onSave?.();
      onClose();
    }
  };

  if (!isOpen) return null;

  const kpiTypes: Array<{ key: keyof KPIConfig; label: string }> = [
    { key: "cpu", label: "CPU Usage" },
    { key: "memory", label: "Memory Usage" },
    { key: "network", label: "Network Latency" },
    { key: "database", label: "Database Query Time" },
    { key: "disk_io", label: "Disk I/O Wait" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-300 dark:border-gray-600 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Edit KPI Thresholds</h2>
          <button
            onClick={onClose}
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6 bg-white dark:bg-gray-800">
          {error && (
            <div className="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg p-3 text-sm text-red-700 dark:text-red-400">
              {error}
            </div>
          )}

          {loading && !editingKPIs && (
            <div className="text-center text-gray-600 dark:text-gray-400 py-8">Loading KPIs...</div>
          )}

          {editingKPIs && (
            <div className="space-y-4">
              {kpiTypes.map(({ key, label }) => {
                const kpi = editingKPIs[key];
                const explanation = explanations[key] || "";
                const isDetected = kpis?.[key]?.detected ?? false;

                return (
                  <div
                    key={key}
                    className="border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-gray-100">{label}</h3>
                        {isDetected && kpis?.[key]?.detected && (
                          <span className="text-xs text-green-600 dark:text-green-400 mt-1 inline-block">
                            Detected from logs
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          step="0.1"
                          value={kpi.threshold}
                          onChange={(e) =>
                            handleThresholdChange(key, parseFloat(e.target.value) || 0)
                          }
                          className="w-24 px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="text-gray-600 dark:text-gray-400 text-sm">{kpi.unit}</span>
                      </div>
                    </div>
                    {explanation && (
                      <div className="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-400">
                        <Info className="h-3 w-3 mt-0.5 flex-shrink-0" />
                        <p>{explanation}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-300 dark:border-gray-600">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !editingKPIs}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};


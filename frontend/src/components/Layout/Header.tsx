import { Menu } from "lucide-react";

type HeaderProps = {
  onMenuClick: () => void;
  subtitle?: string;
  onUploadsClick?: () => void;
  onHomeClick?: () => void;
};

export const Header = ({ onMenuClick, subtitle, onUploadsClick, onHomeClick }: HeaderProps) => (
  <header className="flex items-center justify-between border-b border-borderDark bg-surface px-4 py-3">
    <div>
      <div className="flex items-center gap-3">
        <h1 className="text-base font-semibold text-textPrimary">Nova</h1>
        {onHomeClick && (
          <button
            type="button"
            onClick={onHomeClick}
            className="text-xs text-textSecondary underline-offset-2 hover:underline"
          >
            Home
          </button>
        )}
      </div>
      {subtitle && <p className="mt-0.5 text-xs text-textSecondary">{subtitle}</p>}
    </div>
    <div className="flex items-center gap-3">
      {onUploadsClick && (
        <button
          type="button"
          onClick={onUploadsClick}
          className="hidden text-xs text-textSecondary underline-offset-2 hover:underline sm:inline"
        >
          Uploads
        </button>
      )}
      <button
        type="button"
        onClick={onMenuClick}
        className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-borderDark text-textPrimary hover:bg-black/5"
        aria-label="Toggle sidebar or navigate"
      >
        <Menu className="h-5 w-5" />
      </button>
    </div>
  </header>
);


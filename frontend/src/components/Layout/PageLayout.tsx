import { ReactNode } from "react";

type PageLayoutProps = {
  children: ReactNode;
};

export const PageLayout = ({ children }: PageLayoutProps) => (
  <div className="flex h-full w-full bg-surface text-textPrimary">
    {children}
  </div>
);


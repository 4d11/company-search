import { useEffect } from "react";

interface ShortcutHandlers {
  onSearch?: () => void;
  onEscape?: () => void;
  onSave?: () => void;
}

export const useKeyboardShortcuts = ({ onSearch, onEscape, onSave }: ShortcutHandlers) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onSearch?.();
      }

      if (e.key === "Escape") {
        onEscape?.();
      }

      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        onSave?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onSearch, onEscape, onSave]);
};

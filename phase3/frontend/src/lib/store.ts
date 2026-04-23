/**
 * Tiny Zustand store for app-wide client state (theme, selected merchant slug).
 * Server state goes through TanStack Query, not here.
 */
import { create } from "zustand";

interface AppState {
  activeMerchantSlug: string | null;
  setActiveMerchant: (slug: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  activeMerchantSlug: null,
  setActiveMerchant: (slug) => set({ activeMerchantSlug: slug }),
}));

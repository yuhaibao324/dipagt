import { create, StateCreator } from "zustand";
import { persist, createJSONStorage, PersistOptions } from "zustand/middleware";

// Export the interface
export interface UserState {
  ownerName: string | null;
  setOwnerName: (name: string) => void;
  logout: () => void;
}

// Define the store creator function with proper typing for set
const storeCreator: StateCreator<UserState, [], [], UserState> = (set) => ({
  ownerName: null,
  setOwnerName: (name: string) => set({ ownerName: name }),
  logout: () => set({ ownerName: null }),
});

// Define the persist options
const persistOptions: PersistOptions<UserState> = {
  name: "user-storage", // unique name
  storage: createJSONStorage(() => localStorage), // use localStorage
};

// Dummy store for SSR
const dummyStore: UserState = {
  ownerName: null,
  setOwnerName: () => console.warn("Attempted to set owner name on server"),
  logout: () => console.warn("Attempted to logout on server"),
};

// Export the store, handling SSR by returning a dummy store
export const useUserStore =
  typeof window === "undefined"
    ? create(() => dummyStore)
    : create<UserState>()(persist(storeCreator, persistOptions));

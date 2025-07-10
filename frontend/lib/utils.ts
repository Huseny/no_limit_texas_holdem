import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export * from "./utils/poker"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

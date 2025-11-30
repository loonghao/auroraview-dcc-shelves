/**
 * Types for DCC Shelves frontend.
 */

export enum ToolType {
  PYTHON = 'python',
  EXECUTABLE = 'executable',
}

export enum ToolStatus {
  IDLE = 'IDLE',
  RUNNING = 'RUNNING',
  UPDATE_AVAILABLE = 'UPDATE_AVAILABLE',
  NOT_INSTALLED = 'NOT_INSTALLED',
}

/** Special category for showing all tools */
export const ALL_TOOLS_CATEGORY = 'All Tools'

/** Category is now dynamic - it comes from shelf names */
export type ToolCategory = string

export interface ButtonConfig {
  id: string
  name: string
  toolType: ToolType
  toolPath: string
  icon: string
  args: string[]
  description: string
  /** Category from shelf name or ToolCategory enum */
  category: ToolCategory | string
  version?: string
  status?: ToolStatus
  isFavorite?: boolean
  maintainer?: string
  /** List of supported DCC hosts (e.g., ["maya", "houdini"]). Empty means all hosts. */
  hosts?: string[]
}

export interface ShelfConfig {
  id: string
  name: string
  buttons: ButtonConfig[]
}

export interface BannerConfig {
  title?: string
  subtitle?: string
  image?: string
  gradientFrom?: string
  gradientTo?: string
}

export interface ShelvesConfig {
  shelves: ShelfConfig[]
  banner?: BannerConfig
  currentHost?: string
}

export interface LaunchResult {
  success: boolean
  message: string
  buttonId: string
  /** JavaScript code to execute in WebView (for JavaScript tool type) */
  javascript?: string
}

export interface ContextMenuState {
  visible: boolean
  x: number
  y: number
  button: ButtonConfig | null
}

export interface TabItem {
  id: string
  label: string
}


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

/**
 * Tool source type - indicates where a tool comes from.
 */
export enum ToolSource {
  /** System/built-in tool from YAML config */
  SYSTEM = 'system',
  /** User-created tool stored locally */
  USER = 'user',
}

/** Special category for showing all tools */
export const ALL_TOOLS_CATEGORY = 'All Tools'

/** Category is now dynamic - it comes from shelf names */
export type ToolCategory = string

export interface ButtonConfig {
  id: string
  name: string
  /** Localized name (Chinese) */
  name_zh?: string
  toolType: ToolType
  toolPath: string
  icon: string
  args: string[]
  description: string
  /** Localized description (Chinese) */
  description_zh?: string
  /** Category from shelf name or ToolCategory enum */
  category: ToolCategory | string
  /** Localized category (Chinese) */
  category_zh?: string
  version?: string
  status?: ToolStatus
  isFavorite?: boolean
  maintainer?: string
  /** List of supported DCC hosts (e.g., ["maya", "houdini"]). Empty means all hosts. */
  hosts?: string[]
  /** Wiki URL for the tool */
  wiki?: string
  /** Documentation URL for the tool */
  docs?: string
  /** Assets URL for the tool */
  assets?: string
  /** Tool source - system (built-in) or user (custom) */
  source?: ToolSource
}

export interface ShelfConfig {
  id: string
  name: string
  /** Localized name (Chinese) */
  name_zh?: string
  buttons: ButtonConfig[]
}

export interface BannerConfig {
  title?: string
  /** Localized title (Chinese) */
  title_zh?: string
  subtitle?: string
  /** Localized subtitle (Chinese) */
  subtitle_zh?: string
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

/**
 * User tools configuration for import/export.
 */
export interface UserToolsConfig {
  /** Schema version for forward compatibility */
  version: string
  /** Export timestamp */
  exportedAt: string
  /** User-created shelves with tools */
  shelves: UserShelfConfig[]
}

/**
 * User shelf configuration (simplified for user tools).
 */
export interface UserShelfConfig {
  id: string
  name: string
  name_zh?: string
  buttons: UserButtonConfig[]
}

/**
 * User button configuration (minimal required fields).
 */
export interface UserButtonConfig {
  id: string
  name: string
  name_zh?: string
  toolType: ToolType
  toolPath: string
  icon: string
  args?: string[]
  description?: string
  description_zh?: string
  hosts?: string[]
}

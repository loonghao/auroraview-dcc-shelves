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

export enum ToolCategory {
  ALL = 'All Tools',
  MODELING = 'Modeling',
  RIGGING = 'Rigging',
  ANIMATION = 'Animation',
  UTILITIES = 'Utilities',
}

export interface ButtonConfig {
  id: string
  name: string
  toolType: ToolType
  toolPath: string
  icon: string
  args: string[]
  description: string
  category: ToolCategory
  version?: string
  status?: ToolStatus
  isFavorite?: boolean
  maintainer?: string
}

export interface ShelfConfig {
  id: string
  name: string
  buttons: ButtonConfig[]
}

export interface ShelvesConfig {
  shelves: ShelfConfig[]
}

export interface LaunchResult {
  success: boolean
  message: string
  buttonId: string
}

export interface ContextMenuState {
  visible: boolean
  x: number
  y: number
  button: ButtonConfig | null
}

export interface TabItem {
  id: ToolCategory
  label: string
}


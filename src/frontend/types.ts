/**
 * Types for DCC Shelves frontend.
 */

export enum ToolType {
  PYTHON = 'python',
  EXECUTABLE = 'executable',
}

export interface ButtonConfig {
  id: string
  name: string
  toolType: ToolType
  toolPath: string
  icon: string
  args: string[]
  description: string
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

